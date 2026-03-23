from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    UpdateEventRequest,
    UpdateLinksRequest,
    AddStreamerRequest,
    StreamerListItem,
    StreamerListResponse,
    Links,
)
from app.auth import get_current_admin_user
from app.database import get_connection

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ==================== OPTIONS ====================


@router.get("/event")
async def get_event_status(_: Annotated[dict, Depends(get_current_admin_user)]):
    """Récupère le statut de l'événement."""
    async with get_connection() as cursor:
        await cursor.execute("SELECT event FROM options WHERE id = 1")
        result = await cursor.fetchone()
        event_value = result["event"] if result else 0
        return {"event": event_value == 1 or event_value == "1"}


@router.put("/event")
async def update_event_status(
    request: UpdateEventRequest,
    _: Annotated[dict, Depends(get_current_admin_user)],
):
    """Met à jour le statut de l'événement."""
    async with get_connection() as cursor:
        await cursor.execute(
            "UPDATE options SET event = %s WHERE id = 1",
            (1 if request.event else 0,),
        )
    return {"message": "Statut de l'événement mis à jour", "event": request.event}


# ==================== LINKS ====================


@router.get("/links", response_model=Links)
async def get_links(_: Annotated[dict, Depends(get_current_admin_user)]):
    """Récupère tous les liens."""
    async with get_connection() as cursor:
        await cursor.execute("SELECT * FROM links WHERE id = 1")
        link = await cursor.fetchone()
        if not link:
            return Links()
        return Links(
            discord=link.get("discord", ""),
            reddit=link.get("reddit", ""),
            tuto=link.get("tuto", ""),
            atlas=link.get("atlas", ""),
            relations=link.get("relations", ""),
        )


@router.put("/links")
async def update_links(
    request: UpdateLinksRequest,
    _: Annotated[dict, Depends(get_current_admin_user)],
):
    """Met à jour les liens."""
    async with get_connection() as cursor:
        await cursor.execute(
            """UPDATE links SET 
                discord = %s, 
                reddit = %s, 
                tuto = %s, 
                atlas = %s, 
                relations = %s 
            WHERE id = 1""",
            (
                request.discord,
                request.reddit,
                request.tuto,
                request.atlas,
                request.relations,
            ),
        )
    return {"message": "Liens mis à jour"}


# ==================== STREAMERS ====================


@router.get("/streamers", response_model=StreamerListResponse)
async def get_all_streamers(_: Annotated[dict, Depends(get_current_admin_user)]):
    """Récupère la liste de tous les streamers (sans données Twitch)."""
    async with get_connection() as cursor:
        await cursor.execute("SELECT name FROM streamers ORDER BY name")
        rows = await cursor.fetchall()
        streamers = [StreamerListItem(name=row["name"]) for row in rows]
        return StreamerListResponse(streamers=streamers)


@router.post("/streamers")
async def add_streamer(
    request: AddStreamerRequest,
    _: Annotated[dict, Depends(get_current_admin_user)],
):
    """Ajoute un nouveau streamer."""
    async with get_connection() as cursor:
        # Vérifier si le streamer existe déjà
        await cursor.execute(
            "SELECT name FROM streamers WHERE name = %s", (request.name.lower(),)
        )
        existing = await cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Ce streamer existe déjà")

        await cursor.execute(
            "INSERT INTO streamers (name) VALUES (%s)",
            (request.name.lower(),),
        )
    return {"message": f"Streamer {request.name} ajouté"}


@router.delete("/streamers/{name}")
async def delete_streamer(
    name: str,
    _: Annotated[dict, Depends(get_current_admin_user)],
):
    """Supprime un streamer."""
    async with get_connection() as cursor:
        await cursor.execute("DELETE FROM streamers WHERE name = %s", (name.lower(),))
    return {"message": f"Streamer {name} supprimé"}
