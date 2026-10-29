# Image Python officielle légère
FROM python:3.15-slim-trixie

# Répertoire de travail dans le conteneur
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances Python (couche cache séparée)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Utilisateur non privilégié
RUN useradd --create-home --uid 10001 appuser

# Copie du code de l'application
COPY --chown=appuser:appuser app /app/app

USER appuser

# Port d'écoute
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/status', timeout=4)"]

# Serveur de production. Un seul worker : l'état de l'application est en
# mémoire et ne doit pas être réparti entre plusieurs processus.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--access-logfile", "-", "app.app:app"]
