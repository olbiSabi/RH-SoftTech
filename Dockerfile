# ============================================
# HR_ONIAN - Dockerfile Multi-Stage
# ============================================
# Build : docker build -t hr_onian .
# Run   : docker compose up -d

# ------------------------------------------
# Stage 1 : Builder (compilation des deps)
# ------------------------------------------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ------------------------------------------
# Stage 2 : Runtime (image finale legere)
# ------------------------------------------
FROM python:3.12-slim

# Dependances runtime uniquement (pas de compilateur)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root pour la securite
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Installer les dependances Python depuis les wheels
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copier le code source
COPY . .

# Creer les repertoires necessaires
RUN mkdir -p media logs staticfiles backups \
    && chown -R appuser:appgroup /app

# Collecter les fichiers statiques pendant le build
# (necessite une SECRET_KEY temporaire car settings.py l'exige)
RUN SECRET_KEY="build-only-key" \
    DEBUG="False" \
    ALLOWED_HOSTS="*" \
    DB_NAME="dummy" \
    DB_USER="dummy" \
    DB_PASSWORD="dummy" \
    DB_HOST="localhost" \
    python manage.py collectstatic --noinput 2>/dev/null || true

# Rendre le script d'entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Permissions finales
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "HR_ONIAN.wsgi:application", "-c", "gunicorn.conf.py"]
