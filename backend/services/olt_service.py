import logging
import re
from collections import defaultdict
from typing import Dict, List

from netmiko import ConnectHandler

from backend.config.settings import get_settings

logger = logging.getLogger("olt_app")

SN_PATTERN = re.compile(
    r"^\s*(?P<fsp>\d+/\s*\d+/\d+)\s+"
    r"(?P<ont_id>\d+)\s+"
    r"(?P<sn>[0-9A-Fa-f]{8,})\s+"
    r"\S+\s+"
    r"(?P<run_state>\w+)",
    re.MULTILINE,
)
DESC_PATTERN = re.compile(
    r"^\s*(?P<fsp>\d+/\s*\d+/\d+)\s+"
    r"(?P<ont_id>\d+)\s+"
    r"(?P<description>.+\S)\s*$",
    re.MULTILINE,
)


def _device_config(olt_ip: str) -> Dict[str, str | int | None]:
    settings = get_settings()
    if not settings.olt_username or not settings.olt_password:
        raise RuntimeError("OLT credentials not configured.")

    return {
        "device_type": "huawei_smartax",
        "ip": olt_ip,
        "username": settings.olt_username,
        "password": settings.olt_password,
        "port": settings.olt_port,
        "session_log": settings.netmiko_session_log,
    }


def load_olt_options() -> list[dict[str, str]]:
    return get_settings().olt_options


def process_ont_output(output: str, olt_ip: str) -> List[dict]:
    entries = {}

    for match in SN_PATTERN.finditer(output):
        fsp = match.group("fsp").replace(" ", "")
        ont_id = match.group("ont_id")
        entries[(fsp, ont_id)] = {
            "fsp": fsp,
            "ont_id": ont_id,
            "sn": match.group("sn"),
            "run_state": match.group("run_state"),
            "description": "",
            "olt_ip": olt_ip,
        }

    for match in DESC_PATTERN.finditer(output):
        fsp = match.group("fsp").replace(" ", "")
        ont_id = match.group("ont_id")
        description = match.group("description").strip()

        first_token = description.split()[0] if description else ""
        if re.fullmatch(r"[0-9A-Fa-f]{8,}", first_token):
            continue

        key = (fsp, ont_id)
        if key in entries:
            entries[key]["description"] = description
        else:
            entries[key] = {
                "fsp": fsp,
                "ont_id": ont_id,
                "sn": None,
                "run_state": None,
                "description": description,
                "olt_ip": olt_ip,
            }

    return list(entries.values())


def enrich_onts_with_signal(olt_ip: str, onts: List[dict]) -> List[dict]:
    if not onts:
        return onts

    ssh = ConnectHandler(**_device_config(olt_ip))
    try:
        ssh.send_command("enable", expect_string=r"#", read_timeout=10)
        ssh.send_command("config", expect_string=r"\(config\)#", read_timeout=10)

        slot_groups = defaultdict(list)
        for ont in onts:
            try:
                frame, slot, _ = map(int, ont["fsp"].split("/"))
                slot_groups[(frame, slot)].append(ont)
            except Exception:
                logger.warning("Invalid FSP in ONT payload: %s", ont)

        for (frame, slot), ont_group in slot_groups.items():
            ssh.send_command(
                f"interface gpon {frame}/{slot}",
                expect_string=r"\(config-if-gpon",
                read_timeout=10,
            )

            online = [ont for ont in ont_group if ont.get("run_state") == "online"]
            offline = [ont for ont in ont_group if ont.get("run_state") != "online"]

            for ont in online:
                pon = int(ont["fsp"].split("/")[2])
                ont_id = int(ont["ont_id"])
                output = ssh.send_command(f"display ont optical-info {pon} {ont_id}", read_timeout=15)
                match = re.search(r"Rx optical power\(dBm\)\s*:\s*([-\d.]+)", output)
                ont["rx_power"] = float(match.group(1)) if match else None

            for ont in offline:
                pon = int(ont["fsp"].split("/")[2])
                ont_id = int(ont["ont_id"])
                output = ssh.send_command(f"display ont alarm-state {pon} {ont_id}", read_timeout=10)
                match = re.search(
                    r"Active Alarm List\s*:\s*\n\s*\((?:\d+)\)(.+)",
                    output,
                    re.IGNORECASE,
                )
                ont["alarm"] = match.group(1).strip() if match else None

        return onts
    finally:
        try:
            ssh.disconnect()
        except Exception:
            logger.warning("Failed to close SSH session for olt_ip=%s", olt_ip)


def fetch_ont_status(olt_ip: str, cliente: str) -> List[dict]:
    ssh = ConnectHandler(**_device_config(olt_ip))
    try:
        ssh.send_command("enable", expect_string=r"#", read_timeout=10)
        output = ssh.send_command(f"display ont info by-desc {cliente}", read_timeout=25)
    finally:
        try:
            ssh.disconnect()
        except Exception:
            logger.warning("Failed to close query SSH session for olt_ip=%s", olt_ip)

    parsed = process_ont_output(output, olt_ip)
    return enrich_onts_with_signal(olt_ip, parsed)


def unlock_onu(olt_ip: str, fsp: str) -> dict:
    ssh = None
    try:
        ssh = ConnectHandler(**_device_config(olt_ip))
        ssh.send_command("enable", expect_string=r"#", read_timeout=10)
        ssh.send_command("diagnose", expect_string=r"\(diagnose\)%%", read_timeout=10)
        output = ssh.send_command(f"ont wan-access http {fsp} enable", read_timeout=12)
        return {"status": "ok", "mensagem": output}
    except Exception:
        logger.exception("Failed to unlock ONU. olt_ip=%s fsp=%s", olt_ip, fsp)
        return {"status": "erro", "mensagem": "Falha ao liberar ONU."}
    finally:
        if ssh is not None:
            try:
                ssh.disconnect()
            except Exception:
                logger.warning("Failed to close unlock SSH session. olt_ip=%s", olt_ip)


def reboot_onu(olt_ip: str, fsp: str) -> dict:
    ssh = None
    try:
        ssh = ConnectHandler(**_device_config(olt_ip))
        ssh.send_command("enable", expect_string=r"#", read_timeout=10)
        ssh.send_command("diagnose", expect_string=r"\(diagnose\)%%", read_timeout=10)
        output = ssh.send_command_timing(f"ont force-reset {fsp}")
        if "Are you sure to reset" in output:
            output += ssh.send_command_timing("y")
        return {"status": "ok", "mensagem": output}
    except Exception:
        logger.exception("Failed to reboot ONU. olt_ip=%s fsp=%s", olt_ip, fsp)
        return {"status": "erro", "mensagem": "Falha ao reiniciar ONU."}
    finally:
        if ssh is not None:
            try:
                ssh.disconnect()
            except Exception:
                logger.warning("Failed to close reboot SSH session. olt_ip=%s", olt_ip)
