from fastapi import APIRouter, HTTPException
from app.models import (
    ConfigResponse,
    StreamersResponse,
    HealthResponse,
    Links,
    Streamer,
)
from app.database import get_connection
from app.twitch import get_streamer_names, get_streamer_data

router = APIRouter(prefix="/api")


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Récupère la configuration du site (event actif, liens)."""
    try:
        async with get_connection() as cursor:
            # Récupérer le statut de l'événement
            await cursor.execute("SELECT event FROM options WHERE id = 1")
            option = await cursor.fetchone()
            # Convertir explicitement: 1 ou "1" = True, sinon False
            event_value = option["event"] if option else 0
            event = event_value == 1 or event_value == "1"

            # Récupérer les liens
            await cursor.execute("SELECT * FROM links WHERE id = 1")
            link = await cursor.fetchone()

            links = Links(
                discord=link.get("discord", "") if link else "",
                reddit=link.get("reddit", "") if link else "",
                tuto=link.get("tuto", "") if link else "",
                atlas=link.get("atlas", "") if link else "",
                relations=link.get("relations", "") if link else "",
            )

            return ConfigResponse(event=event, links=links)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streamers", response_model=StreamersResponse)
async def get_streamers():
    """Récupère la liste des streamers avec leur statut live."""
    try:
        streamer_names = await get_streamer_names()
        streamer_data = await get_streamer_data(streamer_names)

        streamers = [
            Streamer(
                name=s["name"],
                profileImage=s["profileImage"],
                isLive=s["isLive"],
            )
            for s in streamer_data
        ]

        return StreamersResponse(streamers=streamers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        async with get_connection() as cursor:
            await cursor.execute("SELECT 1")
            return HealthResponse(status="ok", database="connected")
    except Exception as e:
        return HealthResponse(status="ok", database=f"error: {str(e)}")
