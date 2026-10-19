"""mdportal: markdown viewer whose Jinja2 `fenced_include` reads from named "mount" roots.

    {{ fenced_include("$portalRoot/guide/flow.mmd", "mermaid") }}   -> mermaid diagram
    {{ fenced_include("$currentDir/snippet.py", "python", lines="3-9") }} -> highlighted code
    {{ fenced_include("$bucket/conf/app.yaml") }}                   -> format guessed from extension
    {{ include("$sharedRoot/legal/footer.md") }}                    -> splice another markdown doc

A root is a provider object (local dir, GitHub repo, ...). The path after the root is
interpreted by that provider, so adding S3/HTTP/etc. means adding one small class.
"""
from __future__ import annotations

import os
import posixpath
import re
import shlex
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import mistune
import yaml
from flask import Flask, abort, redirect, render_template, url_for
from jinja2 import StrictUndefined, TemplateError
from jinja2.sandbox import SandboxedEnvironment
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound


# --------------------------------------------------------------------------- roots
class RootError(Exception):
    """Anything that goes wrong resolving or reading an include."""


def clean(path: str) -> str:
    """Normalise a root-relative path. '..' may never climb above the root."""
    parts: list[str] = []
    for seg in path.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise RootError(f"path {path!r} escapes its root")
            parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)


class LocalDir:
    """A directory on disk (in Docker: wherever you bind-mounted it)."""

    def __init__(self, name: str, path: str):
        self.name, self.base = name, Path(path).resolve()

    def read(self, rel: str) -> str:
        target = (self.base / rel).resolve()
        if not target.is_relative_to(self.base):  # blocks symlink escapes too
            raise RootError(f"${self.name}/{rel} resolves outside the mount")
        if not target.is_file():
            raise RootError(f"not found: ${self.name}/{rel}")
        return target.read_text(encoding="utf-8")


MAX_BYTES = 2_000_000  # refuse to pull anything bigger into a doc


class TTLCache:
    def __init__(self, ttl: int = 60):
        self.ttl, self._d = ttl, {}

    def get(self, key):
        hit = self._d.get(key)
        return hit[1] if hit and time.time() - hit[0] < self.ttl else None

    def put(self, key, value):
        self._d[key] = (time.time(), value)


def _decode(data: bytes, where: str) -> str:
    if len(data) > MAX_BYTES:
        raise RootError(f"{where} is larger than {MAX_BYTES // 1000} kB")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise RootError(f"{where} is not UTF-8 text") from None


class HTTP:
    """Any http(s) base URL. The doc only ever supplies the path *under* that base."""

    def __init__(self, name, base_url, headers=None, timeout=10, ttl=60):
        if not base_url.startswith(("http://", "https://")):
            raise ValueError(f"root {name!r}: url must be http(s), got {base_url!r}")
        self.name, self.base, self.timeout = name, base_url.rstrip("/"), timeout
        self.headers = {"User-Agent": "mdportal", **(headers or {})}
        self.cache = TTLCache(ttl)

    def read(self, rel: str) -> str:
        url = f"{self.base}/{quote(rel)}"  # quote() also neutralises %2e%2e tricks
        if (hit := self.cache.get(url)) is not None:
            return hit
        where = f"${self.name}/{rel}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=self.headers),
                                        timeout=self.timeout) as r:
                data = r.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as e:
            raise RootError(f"HTTP {e.code} for {where}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise RootError(f"cannot reach {where}: {getattr(e, 'reason', e)}") from e
        text = _decode(data, where)
        self.cache.put(url, text)
        return text


class GitHub(HTTP):
    """A repo at a ref, via raw.githubusercontent.com (just an HTTP root with auth)."""

    def __init__(self, name, repo, ref="main", subdir="", token=None, ttl=60):
        base = f"https://raw.githubusercontent.com/{repo}/{ref}"
        if subdir.strip("/"):
            base += "/" + subdir.strip("/")
        super().__init__(name, base, {"Authorization": f"token {token}"} if token else None, ttl=ttl)


class S3:
    """An S3 (or S3-compatible: MinIO, R2...) bucket + optional key prefix.

    Credentials come from boto3's normal chain (env vars, ~/.aws, IAM role), never from docs.
    """

    def __init__(self, name, bucket, prefix="", region=None, endpoint_url=None, profile=None, ttl=60):
        self.name, self.bucket, self.prefix = name, bucket, prefix.strip("/")
        self.region, self.endpoint_url, self.profile = region, endpoint_url, profile
        self.cache, self._client = TTLCache(ttl), None

    def _s3(self):
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise RootError("S3 roots need boto3 (pip install boto3)") from None
            session = boto3.Session(profile_name=self.profile, region_name=self.region)
            self._client = session.client("s3", endpoint_url=self.endpoint_url)
        return self._client

    def read(self, rel: str) -> str:
        where = f"${self.name}/{rel}"
        if not self.bucket:
            raise RootError(f"${self.name}: no bucket configured")
        key = "/".join(p for p in (self.prefix, rel) if p)
        if (hit := self.cache.get(key)) is not None:
            return hit
        client = self._s3()
        from botocore.exceptions import BotoCoreError, ClientError
        try:
            obj = client.get_object(Bucket=self.bucket, Key=key)
            if obj.get("ContentLength", 0) > MAX_BYTES:
                raise RootError(f"{where} is larger than {MAX_BYTES // 1000} kB")
            data = obj["Body"].read(MAX_BYTES + 1)
        except ClientError as e:
            raise RootError(f"S3 {e.response.get('Error', {}).get('Code', 'error')} for {where}") from e
        except BotoCoreError as e:
            raise RootError(f"S3 error for {where}: {e}") from e
        text = _decode(data, where)
        self.cache.put(key, text)
        return text


def _expand_env(value):
    """Expand ${VAR} / ${VAR:-default} in strings, recursively. Empty results are dropped
    from mappings, so an unset ${TOKEN} just means 'no token' / 'no header'."""
    if isinstance(value, dict):
        out = {k: _expand_env(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v != ""}
    if not isinstance(value, str):
        return value
    pattern = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")
    return pattern.sub(lambda m: os.environ.get(m[1]) or m[2] or "", value)


def load_roots(specs: dict, config_dir: Path) -> dict:
    roots = {}
    for name, spec in specs.items():
        spec = _expand_env(spec)
        kind, ttl = spec.get("type"), int(spec.get("ttl", 60))
        if kind == "dir":
            p = Path(spec["path"])
            roots[name] = LocalDir(name, str(p if p.is_absolute() else config_dir / p))
        elif kind == "github":
            roots[name] = GitHub(name, spec["repo"], spec.get("ref", "main"),
                                 spec.get("subdir", ""), spec.get("token"), ttl)
        elif kind == "http":
            roots[name] = HTTP(name, spec["url"], spec.get("headers"), spec.get("timeout", 10), ttl)
        elif kind == "s3":
            roots[name] = S3(name, spec.get("bucket", ""), spec.get("prefix", ""), spec.get("region"),
                             spec.get("endpoint_url"), spec.get("profile"), ttl)
        else:
            raise ValueError(f"root {name!r}: unknown type {kind!r}")
    return roots


# ----------------------------------------------------------------------- helpers
@dataclass(frozen=True)
class Loc:
    """Where the document currently being rendered lives. Backs $currentDir."""
    root: str
    dir: str


def fence(body: str, info: str) -> str:
    """Wrap body in a code fence longer than any backtick run inside it."""
    longest = max((len(m) for m in re.findall(r"`+", body)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"\n\n{ticks}{info}\n{body.rstrip(chr(10))}\n{ticks}\n\n"


def guess_lang(path: str) -> str:
    if path.endswith((".mmd", ".mermaid")):
        return "mermaid"
    try:
        return get_lexer_for_filename(path).aliases[0]
    except (ClassNotFound, IndexError):
        return "text"


def slice_lines(text: str, spec: str) -> str:
    """'5' -> line 5, '3-10' -> lines 3..10, '3-' -> line 3 to the end (1-based)."""
    lines = text.splitlines()
    try:
        if "-" in spec:
            a, b = spec.split("-", 1)
            start, end = int(a or 1), int(b) if b else len(lines)
        else:
            start = end = int(spec)
    except ValueError:
        raise RootError(f"bad lines spec {spec!r}") from None
    return "\n".join(lines[start - 1:end])


def parse_info(info: str | None) -> tuple[str, dict]:
    try:
        parts = shlex.split(info or "")
    except ValueError:
        parts = (info or "").split()
    lang = parts[0] if parts and "=" not in parts[0] else ""
    return lang, dict(p.split("=", 1) for p in parts if "=" in p)


# ---------------------------------------------------------------------- markdown
class CodeRenderer(mistune.HTMLRenderer):
    """Every fenced block (included or hand-written) goes through here."""

    def block_code(self, code, info=None):
        lang, attrs = parse_info(info)
        if lang == "include-error":
            return f'<div class="include-error" role="alert">{mistune.escape(code)}</div>\n'
        if lang == "mermaid":
            body = f'<pre class="mermaid">{mistune.escape(code)}</pre>'
        else:
            try:
                lexer = get_lexer_by_name(lang or "text")
            except ClassNotFound:
                lexer = TextLexer()
            body = highlight(code, lexer, HtmlFormatter(cssclass="highlight"))
        cap = f"<figcaption>{mistune.escape(attrs['title'])}</figcaption>" if "title" in attrs else ""
        return f'<figure class="include {"diagram" if lang == "mermaid" else "code"}">{cap}{body}</figure>\n'


class Portal:
    MAX_DEPTH = 8

    def __init__(self, config_path: str):
        path = Path(config_path).resolve()
        cfg = yaml.safe_load(path.read_text())
        self.home = cfg.get("home", "portalRoot/index.md")
        self.roots = load_roots(cfg["roots"], path.parent)
        # Sandboxed: docs (esp. ones pulled from GitHub) can't reach Python internals.
        self.env = SandboxedEnvironment(undefined=StrictUndefined, keep_trailing_newline=True)
        self.md = mistune.create_markdown(
            renderer=CodeRenderer(escape=True),
            plugins=["table", "strikethrough", "task_lists", "url", "footnotes"],
        )

    def resolve(self, ref: str, cur: Loc | None) -> tuple[str, str]:
        """'$root/some/path' -> (root name, cleaned path under that root)."""
        if not ref.startswith("$"):
            raise RootError(f"{ref!r} must look like '$<root>/<path>' (known: {self._known()})")
        token, _, path = ref.partition("/")
        name = token[1:]
        if name == "currentDir":
            if cur is None:
                raise RootError("$currentDir used outside a document")
            return cur.root, clean(posixpath.join(cur.dir, path))
        if name not in self.roots:
            raise RootError(f"unknown root ${name} (known: {self._known()})")
        return name, clean(path)

    def _known(self) -> str:
        return ", ".join(["$currentDir", *(f"${n}" for n in self.roots)])

    def _context(self, cur: Loc, depth: int) -> dict:
        def fenced_include(ref, format=None, lines=None, title=True):
            try:
                r, p = self.resolve(ref, cur)
                text = self.roots[r].read(p)
                if lines:
                    text = slice_lines(text, str(lines))
                fmt = (format or "auto").strip().lower()
                if fmt == "auto":
                    fmt = guess_lang(p)
                label = title if isinstance(title, str) else (f"${r}/{p}" if title else None)
                info = fmt + (" " + shlex.quote(f"title={label}") if label else "")
                return fence(text, info)
            except RootError as e:
                return fence(f"fenced_include({ref!r}): {e}", "include-error")

        def include(ref):
            try:
                r, p = self.resolve(ref, cur)
                inner = self._expand(self.roots[r].read(p), Loc(r, posixpath.dirname(p)), depth + 1)
                return f"\n\n{inner}\n\n"
            except (RootError, TemplateError) as e:
                return fence(f"include({ref!r}): {e}", "include-error")

        return {"fenced_include": fenced_include, "include": include}

    def _expand(self, text: str, cur: Loc, depth: int = 0) -> str:
        if depth > self.MAX_DEPTH:
            raise RootError("include depth exceeded (circular include?)")
        return self.env.from_string(text).render(**self._context(cur, depth))

    def render_doc(self, root: str, path: str) -> str:
        if root not in self.roots:
            raise RootError(f"unknown root ${root}")
        text = self.roots[root].read(path)
        try:
            text = self._expand(text, Loc(root, posixpath.dirname(path)))
        except TemplateError as e:  # broken template: show the error, then the raw text
            text = fence(f"Template error: {e}", "include-error") + text
        return self.md(text)


# --------------------------------------------------------------------------- web
_light = HtmlFormatter(style="friendly").get_style_defs(".highlight")
_dark = HtmlFormatter(style="native").get_style_defs(".highlight")
PYGMENTS_CSS = f"{_light}\n@media (prefers-color-scheme: dark) {{\n{_dark}\n}}"


def create_app(config: str | None = None):
    if config is None:
        config = os.environ.get(
            "MDPORTAL_CONFIG",
            str(Path(__file__).with_name("roots.yaml")),
        )
    portal = Portal(config)
    app = Flask(__name__)

    @app.get("/")
    def home():
        root, _, doc = portal.home.partition("/")
        return redirect(url_for("view", root=root, doc=doc))

    @app.get("/view/<root>/<path:doc>")
    def view(root, doc):
        try:
            html = portal.render_doc(root, clean(doc))
        except RootError as e:
            abort(404, str(e))
        return render_template("page.html", html=html, root=root, doc=doc, css=PYGMENTS_CSS)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
