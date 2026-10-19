# Portal home

Syntax: `fenced_include("$root/path", "format")`. The format is optional and defaults to the file extension.

## Mermaid from the current directory

{{ fenced_include("$currentDir/guide/flow.mmd", "mermaid") }}

## Highlighted code from another mount, lines 1-8

{{ fenced_include("$sharedRoot/snippets/retry.py", "python", lines="1-8") }}

## A file straight from GitHub (format guessed)

{{ fenced_include("$flaskRepo/src/flask/__init__.py", lines="1-6") }}

## Splicing another markdown doc

{{ include("$currentDir/guide/partial.md") }}

## Errors are shown inline, not fatal

{{ fenced_include("$nope/x.py") }}
{{ fenced_include("$portalRoot/../../etc/passwd") }}

Next: [the guide](guide/index.md).
