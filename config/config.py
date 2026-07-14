"""Application configuration loaded and validated from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pyrogram.enums import ParseMode

load_dotenv()


class ConfigError(Exception):
    """Raised when the application configuration is invalid or incomplete."""


def _get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise ConfigError(f"Missing required environment variable: '{name}'")
    return value


def _get_int_env(name: str, required: bool = True, default: int | None = None) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        if required and default is None:
            raise ConfigError(f"Missing required environment variable: '{name}'")
        return default if default is not None else 0

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable '{name}' must be an integer") from exc


def _get_list_env(name: str, default: str = "") -> List[int]:
    raw_value = os.getenv(name, default)

    if not raw_value.strip():
        return []

    result: List[int] = []

    for chunk in raw_value.split(","):
        chunk = chunk.strip()

        if not chunk:
            continue

        try:
            result.append(int(chunk))
        except ValueError as exc:
            raise ConfigError(f"Environment variable '{name}' must contain integers") from exc

    return result


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    bot_token: str

    mongo_uri: str
    mongo_db_name: str

    owner_id: int
    sudo_users: List[int] = field(default_factory=list)

    log_channel_id: int | None = None

    environment: str = "production"
    log_level: str = "INFO"

    session_name: str = "hori_bot"
    workers: int = 8

    parse_mode: ParseMode = ParseMode.HTML

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def privileged_users(self) -> List[int]:
        return [self.owner_id, *self.sudo_users]


def _load_config() -> Config:
    log_channel_raw = os.getenv("LOG_CHANNEL_ID")
    log_channel_id = (
        int(log_channel_raw)
        if log_channel_raw and log_channel_raw.strip()
        else None
    )

    return Config(
        api_id=_get_int_env("API_ID"),
        api_hash=_get_env("API_HASH"),
        bot_token=_get_env("BOT_TOKEN"),
        mongo_uri=_get_env("MONGO_URI"),
        mongo_db_name=_get_env(
            "MONGO_DB_NAME",
            required=False,
            default="hori_bot",
        ),
        owner_id=_get_int_env("OWNER_ID"),
        sudo_users=_get_list_env("SUDO_USERS"),
        log_channel_id=log_channel_id,
        environment=_get_env(
            "ENVIRONMENT",
            required=False,
            default="production",
        ),
        log_level=_get_env(
            "LOG_LEVEL",
            required=False,
            default="INFO",
        ),
        session_name=_get_env(
            "SESSION_NAME",
            required=False,
            default="hori_bot",
        ),
        workers=_get_int_env(
            "WORKERS",
            required=False,
            default=8,
        ),
        parse_mode=ParseMode.HTML,
    )


@lru_cache(maxsize=1)
def get_config() -> Config:
    return _load_config()
