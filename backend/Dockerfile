# CAWASMA backend image (api + worker).
# Build context is ./backend. Includes WeasyPrint's native dependencies
# (cairo/pango/gdk-pixbuf) so PDF report generation works out of the box.
FROM python:3.12-slim

# INSTALL_ML=false skips torch/sentence-transformers/spaCy (~1 GB, slow build);
# the endpoint classifier then runs keyword-only. INSTALL_DEV adds test/lint tools.
ARG INSTALL_ML=true
ARG INSTALL_DEV=false

# HF_HOME: model cache outside /root so the non-root runtime user can read it.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

# System libraries:
#  - build-essential/libpq-dev: psycopg2 build
#  - libcairo2, libpango*, libgdk-pixbuf*, libffi: WeasyPrint rendering
#  - fonts-dejavu-core: baseline fonts for PDF output
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies from pyproject.toml before copying the source, against a
# placeholder package, so code edits don't invalidate this layer.
COPY pyproject.toml .
RUN mkdir app && touch app/__init__.py \
    && pip install --upgrade pip \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install ".[dev]"; else pip install .; fi \
    && pip uninstall -y cawasma-backend && rm -rf app build *.egg-info

# NLP stack (CPU-only torch, sentence-transformers, spaCy). The models are
# downloaded at build time so scans never wait on (or fail at) a model download.
COPY requirements-ml.txt .
RUN if [ "$INSTALL_ML" = "true" ]; then \
        pip install -r requirements-ml.txt \
        && python -m spacy download en_core_web_sm \
        && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; \
    fi

COPY . .

RUN useradd --create-home --uid 1000 cawasma && chown -R cawasma /app
USER cawasma

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
