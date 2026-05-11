# Image Python officielle légère
FROM python:3.13-slim-bookworm

# Répertoire de travail dans le conteneur
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installation des dépendances Python (couche cache séparée)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY app /app/app

# Port d'écoute Flask
EXPOSE 5000

# Démarrage de l'application
CMD ["python", "-m", "flask", "run"]
