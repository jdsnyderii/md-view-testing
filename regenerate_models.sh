#!/bin/sh
# Regenerate Pydantic models from LinkML and attach type discriminator.
set -e
cd "$(dirname "$0")"
export PATH="/usr/local/bin:$PATH"

if command -v gen-pydantic >/dev/null 2>&1; then
  gen-pydantic roots.linkml.yaml --extra-fields forbid > roots_models.py
else
  python3 -c "
from linkml.generators.pydanticgen import PydanticGenerator
print(PydanticGenerator('roots.linkml.yaml', extra_fields='forbid').serialize())
" > roots_models.py
fi

python3 << 'PY'
from pathlib import Path
import re
path = Path("roots_models.py")
text = path.read_text()
if "Annotated" not in text:
    text = text.replace(
        "from typing import (\n    Any,\n    ClassVar,\n    Literal,\n    Optional,\n    Union\n)",
        "from typing import (\n    Annotated,\n    Any,\n    ClassVar,\n    Literal,\n    Optional,\n    Union\n)",
    )
text2, n = re.subn(
    r"roots: dict\[str, Union\[Dir,\s*Github,\s*Http,\s*S3\]\] = Field\(",
    'roots: dict[str, Annotated[Union[Dir, Github, Http, S3], Field(discriminator="type")]] = Field(',
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"discriminator patch failed (n={n})")
path.write_text(text2)
print("wrote roots_models.py with discriminator")
PY
