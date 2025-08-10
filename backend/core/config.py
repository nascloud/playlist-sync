import os
from typing import Optional
import secrets

from pydantic_settings import BaseSettings
from pydantic import Field

class AuthConfig(BaseSettings):
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    APP_PASSWORD: str = Field(..., env="APP_PASSWORD")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")

class PlexConfig(BaseSettings):
    URL: Optional[str] = Field(default=None, env="PLEX_URL")
    TOKEN: Optional[str] = Field(default=None, env="PLEX_TOKEN")

class DownloaderConfig(BaseSettings):
    API_KEY: Optional[str] = Field(default=None, env="DOWNLOADER_API_KEY")
    PATH: Optional[str] = Field(default=None, env="DOWNLOADER_PATH")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), '..', '.env'), extra='ignore', case_sensitive=False, env_nested_delimiter='__')

    PROJECT_NAME: str = "Plex Music Sync API"
    API_V1_STR: str = "/api"
    PORT: int = 3001
    DATABASE_URL: str = "sqlite:///./database.sqlite"
    DEBUG: bool = False

    auth: AuthConfig = AuthConfig()
    plex: PlexConfig = PlexConfig()
    downloader: DownloaderConfig = DownloaderConfig()

    

settings = Settings()