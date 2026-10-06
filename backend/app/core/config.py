from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TrackBus API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    firebase_database_url: str = ""
    firebase_credentials_path: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()