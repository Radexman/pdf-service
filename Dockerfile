# syntax=docker/dockerfile:1

# 1) BASE IMAGE
# A tiny Debian Linux that already has Python 3.13 installed.
# "slim" = stripped down, smaller download.
FROM python:3.13-slim

# 2) SYSTEM LIBRARIES FOR WEASYPRINT
# These are operating-system libraries, NOT Python packages.
# WeasyPrint uses Pango to lay out and render text into the PDF.
# On your Windows PC these came bundled with the GTK runtime, so it "just worked".
# A fresh Linux container has none of them, so we install them explicitly.
#   - libpango / libpangoft2 / libharfbuzz-subset : text layout & shaping (required)
#   - fonts-dejavu : actual font files, incl. the ✓ glyph used in the template
# (rm -rf .../lists keeps the image small by deleting the package index afterwards.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# 3) PYTHON RUNTIME SETTINGS
# PYTHONUNBUFFERED   : logs appear immediately (not held in a buffer)
# PYTHONDONTWRITEBYTECODE : don't litter the image with .pyc cache files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 4) WORKING DIRECTORY
# Everything below happens inside /app in the container's filesystem.
WORKDIR /app

# 5) INSTALL PYTHON DEPS (copied first, on purpose)
# Docker caches each step as a layer. By copying ONLY requirements.txt before
# the rest of the code, this slow "pip install" step is re-run only when the
# dependencies change — not every time you edit a .py file.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6) COPY THE APPLICATION CODE
COPY . .

# 7) RUN AS A NON-ROOT USER (good security hygiene)
RUN useradd --create-home appuser
USER appuser

# 8) DOCUMENT THE PORT the app listens on (informational).
EXPOSE 8000

# 9) START COMMAND
# uvicorn serves the FastAPI "app" object from main.py.
# --host 0.0.0.0 is REQUIRED in a container: it means "accept connections from
# outside the container". (127.0.0.1 would only be reachable from inside it.)
#
# We use the shell form with ${PORT:-8000} so the port is DYNAMIC:
#   - Hosts like Render/Railway inject a PORT env var and require the app to
#     listen on it. ${PORT} picks that up automatically.
#   - Locally PORT is unset, so it falls back to :-8000 (your usual port).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
