FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn \
 && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY app.py ./
COPY templates/ templates/

# Example config + sample trees (override both with mounts).
# The app does not assume these paths — only whatever MDPORTAL_CONFIG and
# the dir `path:` values inside that file say.
COPY roots.yaml /config/roots.yaml
COPY sample/portal /data/portal
COPY sample/shared /data/shared

RUN chown -R appuser:appuser /app /config /data

USER appuser

# Point at the example config; replace with -v …:/config/roots.yaml and/or -e.
ENV MDPORTAL_CONFIG=/config/roots.yaml

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--factory", "app:create_app"]
