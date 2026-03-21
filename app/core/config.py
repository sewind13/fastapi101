from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class Settings(BaseSettings):
    APP_NAME: str = "Default APP Name"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

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