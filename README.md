# r/placeFR Backend

![GitHub Release](https://img.shields.io/github/v/release/laxe4k/rplacefr-backend)
![GitHub License](https://img.shields.io/github/license/laxe4k/rplacefr-backend)

Backend API pour le site r/placeFR, construit avec FastAPI + Python.

## Installation

```bash
# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=user
DB_PASS=password
DB_NAME=rplacefr

TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

COOKIE_SECURE=false  # true en production (HTTPS)
```

## Lancement

```bash
# Mode développement avec hot-reload
uvicorn app.main:app --reload

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Structure du projet

- `app/main.py` - Point d'entrée de l'application FastAPI
- `app/routes_*.py` - Routes API (auth, config, streamers, links)
- `app/database.py` - Configuration de la connexion MySQL
- `app/auth.py` - Authentification JWT avec cookies httpOnly
- `app/twitch.py` - Intégration API Twitch

## Docker

```bash
# Avec docker-compose
docker compose up -d

# Ou manuellement
docker build -t rplacefr-backend .
docker run -p 8000:8000 --env-file .env rplacefr-backend
```

## Endpoints API

- `GET /api/config` - Récupère la configuration (event actif, liens)
- `GET /api/streamers` - Récupère la liste des streamers avec leur statut live
- `GET /api/health` - Health check
- `POST /api/login` - Connexion admin
- `POST /api/logout` - Déconnexion
