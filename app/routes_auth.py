from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.models import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
)
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.config import get_settings
from app.database import get_connection

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "auth_token"


def set_auth_cookie(response: Response, token: str):
    """Définit le cookie d'authentification httpOnly."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,  # True en prod (HTTPS)
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookie(response: Response):
    """Supprime le cookie d'authentification."""
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.post("/register")
async def register(request: RegisterRequest):
    """Crée un compte en attente de validation par un admin."""
    if len(request.username.strip()) < 3:
        raise HTTPException(
            status_code=400, detail="Nom d'utilisateur trop court (min 3 caractères)"
        )
    if len(request.password) < 6:
        raise HTTPException(
            status_code=400, detail="Mot de passe trop court (min 6 caractères)"
        )

    async with get_connection() as cursor:
        await cursor.execute(
            "SELECT id FROM users WHERE username = %s", (request.username.strip(),)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=409, detail="Ce nom d'utilisateur est déjà pris"
            )

        password_hash = get_password_hash(request.password)
        await cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin, is_approved) VALUES (%s, %s, 0, 0)",
            (request.username.strip(), password_hash),
        )
    return {"message": "Inscription en attente de validation par un administrateur"}


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Authentifie un utilisateur et retourne un token JWT."""
    user = await authenticate_user(form_data.username, form_data.password)
    if user == "not_approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est en attente de validation par un administrateur",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
    )
    set_auth_cookie(response, access_token)
    return TokenResponse(access_token=access_token)


@router.post("/login/json", response_model=TokenResponse)
async def login_json(response: Response, request: LoginRequest):
    """Authentifie un utilisateur via JSON et retourne un token JWT."""
    user = await authenticate_user(request.username, request.password)
    if user == "not_approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est en attente de validation par un administrateur",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
    )
    set_auth_cookie(response, access_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    """Déconnecte l'utilisateur en supprimant le cookie."""
    clear_auth_cookie(response)
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Récupère les informations de l'utilisateur connecté."""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        is_admin=bool(current_user["is_admin"]),
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Change le mot de passe de l'utilisateur connecté."""
    if not verify_password(request.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect",
        )

    new_hash = get_password_hash(request.new_password)
    async with get_connection() as cursor:
        await cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, current_user["id"]),
        )

    return {"message": "Mot de passe modifié avec succès"}


@router.delete("/me")
async def delete_account(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Supprime le compte de l'utilisateur connecté."""
    async with get_connection() as cursor:
        await cursor.execute("DELETE FROM users WHERE id = %s", (current_user["id"],))
    clear_auth_cookie(response)
    return {"message": "Compte supprimé"}
