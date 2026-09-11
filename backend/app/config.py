from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CivicResolve AI"
    environment: str = "development"
    database_url: str = "sqlite:///./civicresolve.db"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    allowed_hosts: str = "*"
    api_prefix: str = "/api/v1"
    auto_create_schema: bool = True
    jwt_secret: str = "development-only-change-me-please-replace-123456"
    jwt_exp_hours: int = 8
    auth_cookie_name: str = "civicresolve_session"
    auth_cookie_secure: bool = False
    geocoder_base_url: str = "https://nominatim.openstreetmap.org"
    geocoder_country_codes: str = "in"
    geocoder_timeout_seconds: float = 4.0
    geocoder_user_agent: str = "CivicResolveAI/0.5 civic-resolution-prototype"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @property
    def geocoder_country_code_list(self) -> list[str]:
        return [code.strip().lower() for code in self.geocoder_country_codes.split(",") if code.strip()]

    def validate_security(self) -> None:
        if self.environment.lower() == "production" and self.jwt_secret == "development-only-change-me-please-replace-123456":
            raise RuntimeError("JWT_SECRET must be changed in production.")
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters long.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
