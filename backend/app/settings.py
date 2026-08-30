from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JARVIS Scolaire"
    database_url: str = "sqlite:///./jarvis.db"
    dev_user_email: str = "toi@example.com"
    dev_user_name: str = "Toi"
    pronote_url: str = ""
    pronote_ent_url: str = ""
    pronote_provider: str = "educonnect"
    pronote_username: str = ""
    pronote_password: str = ""
    weather_city: str = "La Loupe"
    train_departure_station: str = "La Loupe"
    train_arrival_station: str = "Nogent-le-Rotrou"
    train_usual_time: str = "07:14"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
