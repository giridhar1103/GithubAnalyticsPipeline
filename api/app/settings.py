from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dashboard_db_path: str = "/data/dashboard.duckdb"
    frontend_origins: str = "https://<your_frontend_domain_here>"

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
