import httpx
import time
from app.config import get_settings
from app.database import get_connection

settings = get_settings()

# Cache pour le token OAuth
_oauth_token: str | None = None
_token_expires_at: int = 0


async def get_oauth_token() -> str | None:
    """Récupère ou rafraîchit le token OAuth Twitch."""
    global _oauth_token, _token_expires_at

    # Vérifier si le token est encore valide (marge de 60 secondes)
    if _oauth_token and _token_expires_at > (time.time() + 60):
        return _oauth_token

    # Demander un nouveau token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": settings.twitch_client_id,
                "client_secret": settings.twitch_client_secret,
                "grant_type": "client_credentials",
            },
        )

        if response.status_code == 200:
            data = response.json()
            _oauth_token = data.get("access_token")
            expires_in = data.get("expires_in", 0)
            _token_expires_at = int(time.time()) + expires_in

            # Sauvegarder dans la DB (optionnel)
            try:
                async with get_connection() as cursor:
                    await cursor.execute(
                        "UPDATE options SET oauth_token = %s, token_expires_at = %s WHERE id = 1",
                        (_oauth_token, _token_expires_at),
                    )
            except Exception:
                pass  # Ignorer les erreurs de sauvegarde

            return _oauth_token

    return None


async def get_streamer_names() -> list[str]:
    """Récupère la liste des noms de streamers depuis la DB."""
    async with get_connection() as cursor:
        await cursor.execute("SELECT name FROM streamers ORDER BY name")
        rows = await cursor.fetchall()
        return [row["name"] for row in rows]


async def get_streamer_data(streamer_names: list[str]) -> list[dict]:
    """Récupère les données des streamers depuis l'API Twitch."""
    token = await get_oauth_token()
    if not token:
        return []

    live_streamers: dict[str, dict] = {}
    offline_streamers: dict[str, dict] = {}

    headers = {
        "Client-ID": settings.twitch_client_id,
        "Authorization": f"Bearer {token}",
    }

    async with httpx.AsyncClient() as client:
        # Traiter par lots de 100 (limite Twitch)
        for i in range(0, len(streamer_names), 100):
            chunk = streamer_names[i : i + 100]

            # Récupérer les infos utilisateurs
            users_params = {"login": chunk}
            users_response = await client.get(
                "https://api.twitch.tv/helix/users",
                headers=headers,
                params=users_params,
            )
            users_data = users_response.json().get("data", [])

            # Récupérer les streams en cours
            streams_params = {"user_login": chunk}
            streams_response = await client.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params=streams_params,
            )
            streams_data = streams_response.json().get("data", [])
            live_logins = {stream["user_login"].lower() for stream in streams_data}

            # Organiser les données
            for user in users_data:
                streamer_data = {
                    "name": user["login"],
                    "profileImage": user["profile_image_url"],
                    "isLive": user["login"].lower() in live_logins,
                }

                if streamer_data["isLive"]:
                    live_streamers[user["login"]] = streamer_data
                else:
                    offline_streamers[user["login"]] = streamer_data

    # Trier et fusionner (live en premier)
    sorted_live = sorted(live_streamers.values(), key=lambda x: x["name"].lower())
    sorted_offline = sorted(offline_streamers.values(), key=lambda x: x["name"].lower())

    return sorted_live + sorted_offline
