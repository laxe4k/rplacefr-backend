# r/placeFR Backend

Backend API pour le site r/placeFR, construit avec FastAPI.

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
```

## Lancement

```bash
# Mode développement
uvicorn app.main:app --reload

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoints API

- `GET /api/config` - Récupère la configuration (event actif, liens)
- `GET /api/streamers` - Récupère la liste des streamers avec leur statut live
- `GET /api/health` - Health check
