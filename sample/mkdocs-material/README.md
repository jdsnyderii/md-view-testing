# Material print test

This is an isolated MkDocs site using the official Material for MkDocs Docker image. It has no custom CSS, so the browser print preview exercises the theme's built-in print styles.

From this directory, pull and start the site:

```bash
docker pull squidfunk/mkdocs-material:9
docker run --rm -it -p 8001:8000 -v "$PWD":/docs squidfunk/mkdocs-material:9
```

Open <http://localhost:8001>, then use <kbd>Cmd</kbd>+<kbd>P</kbd> to inspect the browser's native print preview and choose Save as PDF if desired. On Windows/Linux use <kbd>Ctrl</kbd>+<kbd>P</kbd>.

The separate port avoids colliding with mdportal's usual port 8000. This container is for local previewing, not production deployment.