from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_pass: str = ""
    db_name: str = "rplacefr"

    # Twitch API
    twitch_client_id: str = ""
    twitch_client_secret: str = ""

    # JWT
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 heures

    # Cookie
    cookie_secure: bool = False  # True en production (HTTPS)

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
