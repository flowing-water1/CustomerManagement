from dataclasses import dataclass
import os


@dataclass
class Settings:
    database_url: str
    app_secret_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            app_secret_key=os.environ["APP_SECRET_KEY"],
        )
