from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://searchparty:searchparty@localhost:5432/searchparty"
    secret_key: str = "change-me-in-production"  # noqa: S105
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = {"env_prefix": "SP_"}


settings = Settings()
