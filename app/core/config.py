from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class Settings(BaseSettings):
    APP_NAME: str = "Default APP Name"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # -- For JWT login
    SECRET_KEY: str = "your-super-secret-key-don-t-tell-anyone" # ใน Prod จริงให้ใช้ openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # อายุ Token 30 นาที

    # -- Postguest (Neon) database
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # Use double underscore to denote nested settings (e.g., db__URL for DatabaseSettings.URL)
        env_file_encoding="utf-8",
        case_sensitive=False,        # Environment variables are case-sensitive
        extra="ignore",             # Ignore extra fields in the .env file that are not defined in the settings classes
        validate_default=True
    )

settings = Settings()

if __name__ ==  "__main__":
    print(settings.APP_NAME)
    print(type(settings.DEBUG))
    print(settings.API_V1_STR)