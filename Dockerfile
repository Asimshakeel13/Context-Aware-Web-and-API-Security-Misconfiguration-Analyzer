# CAWASMA backend image.
# Includes WeasyPrint's native dependencies (cairo/pango/gdk-pixbuf) so PDF
# report generation works out of the box.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

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

# Install the lightweight core dependencies. The heavy NLP stack
# (requirements-ml.txt, CPU-only torch) is added in Phase 8:
#   RUN pip install -r requirements-ml.txt && python -m spacy download en_core_web_sm
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
