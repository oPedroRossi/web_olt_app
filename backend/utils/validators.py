import ipaddress
import re
from typing import Tuple

from backend.config.settings import get_settings

FSP_ONT_PATTERN = re.compile(r"^\d+/\d+/\d+\s+\d+$")
CLIENT_PATTERN = re.compile(r"^[A-Za-z0-9_.\-\s]{2,64}$")


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def validate_olt_ip(olt_ip: str) -> Tuple[bool, str]:
    if not is_valid_ip(olt_ip):
        return False, "OLT IP invalid."

    allowed_ips = get_settings().allowed_olt_ips
    if allowed_ips and olt_ip not in allowed_ips:
        return False, "OLT not allowed."
    return True, ""


def validate_cliente(cliente: str) -> bool:
    return bool(CLIENT_PATTERN.fullmatch(cliente))


def parse_onu_payload(onu_value: str) -> Tuple[bool, str, str]:
    if not isinstance(onu_value, str) or "," not in onu_value:
        return False, "", ""

    olt_ip, fsp = [value.strip() for value in onu_value.split(",", 1)]
    if not is_valid_ip(olt_ip):
        return False, "", ""
    if not FSP_ONT_PATTERN.fullmatch(fsp):
        return False, "", ""
    return True, olt_ip, fsp
