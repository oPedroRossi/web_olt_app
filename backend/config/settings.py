import ipaddress
import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    flask_debug: bool
    log_level: str
    olt_username: str
    olt_password: str
    olt_port: int
    netmiko_session_log: str | None
    olt_options_raw: str

    @property
    def olt_options(self) -> list[dict[str, str]]:
        try:
            options = json.loads(self.olt_options_raw or "[]")
            if not isinstance(options, list):
                return []
        except json.JSONDecodeError:
            logging.getLogger("olt_app").warning("OLT_OPTIONS invalid JSON. Using empty list.")
            return []

        valid = []
        for item in options:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            ip = str(item.get("ip", "")).strip()
            if name and _is_valid_ip(ip):
                valid.append({"name": name, "ip": ip})
        return valid

    @property
    def allowed_olt_ips(self) -> set[str]:
        return {item["ip"] for item in self.olt_options}


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "5169")),
        flask_debug=_parse_bool(os.getenv("FLASK_DEBUG"), default=False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        olt_username=os.getenv("OLT_USERNAME", "").strip(),
        olt_password=os.getenv("OLT_PASSWORD", "").strip(),
        olt_port=int(os.getenv("OLT_PORT", "22")),
        netmiko_session_log=os.getenv("NETMIKO_SESSION_LOG") or None,
        olt_options_raw=os.getenv("OLT_OPTIONS", "[]"),
    )
    _configure_logging(settings.log_level)
    return settings
