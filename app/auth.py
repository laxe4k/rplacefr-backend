from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.config import get_settings
from app.database import get_connection

settings = get_settings()

# Password hashing avec Argon2id
ph = PasswordHasher()

# OAuth2 scheme (optionnel pour supporter aussi Bearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

COOKIE_NAME = "auth_token"


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extrait le token du cookie httpOnly."""
    return request.cookies.get(COOKIE_NAME)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Hash un mot de passe avec Argon2id."""
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crée un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_user_by_username(username: str) -> dict | None:
    """Récupère un utilisateur par son nom d'utilisateur."""
    async with get_connection() as cursor:
        await cursor.execute(
            "SELECT id, username, password_hash, is_admin, is_approved FROM users WHERE username = %s",
            (username,),
        )
        return await cursor.fetchone()


async def authenticate_user(username: str, password: str) -> Union[dict, str, None]:
    """Authentifie un utilisateur."""
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_approved"):
        return "not_approved"
    return user


async def get_current_user(
    request: Request,
    bearer_token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
) -> dict:
    """Récupère l'utilisateur courant à partir du cookie ou du header Bearer."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Priorité au cookie httpOnly, sinon Bearer token
    token = get_token_from_cookie(request) or bearer_token

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Vérifie que l'utilisateur courant est admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user


async def create_default_admin():
    """Crée un compte admin par défaut s'il n'existe pas."""
    async with get_connection() as cursor:
        await cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = 1")
        result = await cursor.fetchone()
        if result["count"] == 0:
            # Créer un admin par défaut (username: admin, password: admin)
            password_hash = get_password_hash("admin")
            await cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin, is_approved) VALUES (%s, %s, %s, %s)",
                ("admin", password_hash, True, True),
            )
            print("Compte admin par défaut créé (username: admin, password: admin)")
        else:
            # S'assurer que tous les admins existants sont approuvés
            await cursor.execute("UPDATE users SET is_approved = 1 WHERE is_admin = 1")
