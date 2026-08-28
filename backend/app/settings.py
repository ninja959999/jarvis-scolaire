from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JARVIS Scolaire"
    database_url: str = "sqlite:///./jarvis.db"
    dev_user_email: str = "toi@example.com"
    dev_user_name: str = "Toi"
    pronote_url: str = ""
    pronote_username: str = ""
    pronote_password: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
