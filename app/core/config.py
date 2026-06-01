# Single source of truth for all app configuration
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required — app won't start if these are missing
    DATABASE_URL: str
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    APP_NAME: str = "You Know It"
    DEBUG: bool = False  # Always False in production

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global instance — imported everywhere in the app
settings = Settings()
