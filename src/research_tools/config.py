"""Configuration loading for research-tools."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env_config() -> dict[str, str | None]:
    """Load environment config from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "devto_api_key": os.getenv("DEVTO_API_KEY"),
        "serper_api_key": os.getenv("SERPER_API_KEY"),
    }
