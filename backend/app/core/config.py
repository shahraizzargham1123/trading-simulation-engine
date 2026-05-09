from typing import Annotated, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg2://trader:trader@localhost:5432/trading_sim"
    )

    demo_user_username: str = Field(default="demo")
    demo_user_starting_cash: float = Field(default=10000.0)

    price_source: str = Field(default="simulated")
    price_tick_seconds: float = Field(default=3.0)
    # NoDecode prevents pydantic-settings from JSON-parsing the env value
    # before our validator runs, so a comma-separated TRACKED_SYMBOLS works.
    tracked_symbols: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["AAPL", "TSLA", "GOOG", "MSFT", "AMZN"]
    )

    alpha_vantage_api_key: str = Field(default="")
    alpha_vantage_base_url: str = Field(default="https://www.alphavantage.co/query")

    frontend_origin: str = Field(default="http://localhost:5173")

    @field_validator("tracked_symbols", mode="before")
    @classmethod
    def split_symbols(cls, v):
        if isinstance(v, str):
            return [s.strip().upper() for s in v.split(",") if s.strip()]
        return v

    @field_validator("price_source")
    @classmethod
    def normalize_source(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in {"simulated", "alphavantage"}:
            raise ValueError("PRICE_SOURCE must be 'simulated' or 'alphavantage'")
        return v


settings = Settings()
