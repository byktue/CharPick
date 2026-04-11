from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]


DEFAULT_DATABASE_URL = os.getenv(
    "DEFAULT_DATABASE_URL",
    "postgresql+psycopg2://charpick:charpick@localhost:5432/charpick",
)


@dataclass(frozen=True)
class DatabaseSettings:
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    echo: bool = os.getenv("DATABASE_ECHO", "false").strip().lower() in {"1", "true", "yes", "on"}

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = DatabaseSettings()