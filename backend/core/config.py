import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), '..', '.env'),
        extra='ignore',
        case_sensitive=False
    )

    PROJECT_NAME: str = "Plex Music Sync API"
    API_V1_STR: str = "/api"
    PORT: int = 3001
    DATABASE_URL: str = "sqlite:///./data/database.sqlite"
    DEBUG: bool = False

    # Auth settings
    SECRET_KEY: str
    APP_PASSWORD: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # Plex settings
    PLEX_URL: Optional[str] = None
    PLEX_TOKEN: Optional[str] = None

    # Downloader settings
    DOWNLOADER_API_KEY: Optional[str] = None
    DOWNLOAD_PATH: str = "Downloads"

settings = Settings()
