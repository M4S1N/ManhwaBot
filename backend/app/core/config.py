from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "backend"
    version: str = '0.1.0'
    debug: bool = True

    class Config:
        extra = "allow"
        CORS_CONFIG = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

settings = Settings()
