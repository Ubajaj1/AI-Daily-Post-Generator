"""Simple settings loader using python-dotenv and environment variables.

We avoid pydantic/BaseSettings here to keep the runtime lightweight and
compatible with environments that don't have `pydantic-settings` installed.
If you prefer typed validation, we can switch back to pydantic once the
`pydantic-settings` package is added to the environment.
"""

from dotenv import load_dotenv
import os


# Load .env file if present
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    SENDGRID_API_KEY: str | None = os.getenv("SENDGRID_API_KEY")
    SENDER_EMAIL: str | None = os.getenv("SENDER_EMAIL")
    RECIPIENT_EMAIL: str | None = os.getenv("RECIPIENT_EMAIL")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")


settings = Settings()
