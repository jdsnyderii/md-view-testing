# Material print test

This standalone site is a small comparison target for **Material for MkDocs' built-in print styles**. Open the browser's native print preview with <kbd>Cmd</kbd>+<kbd>P</kbd> (or <kbd>Ctrl</kbd>+<kbd>P</kbd> on Windows/Linux). No custom print stylesheet or PDF plugin is enabled here.

The preview should paginate this page as printable sheets. The browser, rather than MkDocs, supplies the print-preview window and PDF controls.

!!! tip "What to look for"

    Check whether the navigation disappears, the content uses the printable width, and headings and colored elements remain readable. Compare the screen page with the native print preview.

## Color and text

Material's default teal and amber palette is configured in `mkdocs.yml`. This sentence has **bold text**, *emphasis*, and a [link to the Material documentation](https://squidfunk.github.io/mkdocs-material/).

> A block quote provides another contrasting element to inspect in the print preview.

### A table

| Element | Screen purpose | Print check |
| --- | --- | --- |
| Navigation | Move around the site | Is it hidden on paper? |
| Admonition | Emphasize a note | Does the color remain legible? |
| Code | Show source examples | Does it fit within the page? |
| Table | Compare values | Are columns kept together? |

### A code sample

```python
from pathlib import Path


def markdown_files(documentation_root: Path) -> list[Path]:
    """Return Markdown files in stable order for a tiny documentation site."""
    return sorted(documentation_root.rglob("*.md"))


for path in markdown_files(Path("docs")):
    print(f"Printing: {path}")
```

## Page layout

The following sections make the sample long enough to inspect page breaks, repeated spacing, and continuation across printed pages.

### Headings and pagination

The heading hierarchy is intentionally varied. Look for headings stranded at the bottom of a page and whether the following paragraph stays with its heading.

#### Smaller heading

Print styles need to preserve a clear hierarchy while adapting the site layout to paper. This paragraph is long enough to demonstrate ordinary wrapping at the page's printable width, without relying on fixed screen dimensions or custom CSS.

### Details block

??? note "Expandable content"

    This detail block is included to see how expandable content is represented when printing. It contains enough text to check the relationship between its summary and body.

### Another color block

!!! warning "Print settings matter"

    Browser print settings can affect backgrounds and color adjustment. This is part of the test: inspect the preview options as well as the page itself.

## Final section

Material's print rules are part of the theme's CSS; this sample deliberately does not override them. The goal is to compare the native Cmd-P result here with the result from the Flask Markdown viewer.

The output depends on the browser and its print settings, so note the browser, page count, and whether the preview shows color when comparing results.