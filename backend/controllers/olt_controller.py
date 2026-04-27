import logging

from flask import jsonify, render_template, request

from backend.services.olt_service import (
    fetch_ont_status,
    load_olt_options,
    reboot_onu,
    unlock_onu,
)
from backend.utils.validators import parse_onu_payload, validate_cliente, validate_olt_ip

logger = logging.getLogger("olt_app")


def index():
    return render_template("index.html", olt_options=load_olt_options())


def health():
    return {"status": "ok"}, 200


def status_olt():
    payload = request.get_json(silent=True) or {}
    olt_ip = str(payload.get("olt", "")).strip()
    cliente = str(payload.get("cliente", "")).strip().lower()

    is_valid, message = validate_olt_ip(olt_ip)
    if not is_valid:
        return jsonify({"erro": message}), 400

    if not validate_cliente(cliente):
        return jsonify({"erro": "Cliente invalido. Use 2-64 chars alfanumericos."}), 400

    try:
        dados = fetch_ont_status(olt_ip, cliente)
        return jsonify(dados), 200
    except Exception:
        logger.exception("OLT query failed. olt_ip=%s cliente=%s", olt_ip, cliente)
        return jsonify({"erro": "Erro interno ao consultar OLT."}), 500


def unlocked_btn():
    payload = request.get_json(silent=True) or {}
    is_valid, olt_ip, fsp = parse_onu_payload(payload.get("onu", ""))
    if not is_valid:
        return jsonify({"status": "erro", "mensagem": "ONU payload invalido."}), 400

    ip_ok, _ = validate_olt_ip(olt_ip)
    if not ip_ok:
        return jsonify({"status": "erro", "mensagem": "OLT nao permitida."}), 400

    return jsonify(unlock_onu(olt_ip, fsp))


def reboot_onu_handler():
    payload = request.get_json(silent=True) or {}
    is_valid, olt_ip, fsp = parse_onu_payload(payload.get("onu", ""))
    if not is_valid:
        return jsonify({"status": "erro", "mensagem": "ONU payload invalido."}), 400

    ip_ok, _ = validate_olt_ip(olt_ip)
    if not ip_ok:
        return jsonify({"status": "erro", "mensagem": "OLT nao permitida."}), 400

    result = reboot_onu(olt_ip, fsp)
    status_code = 200 if result.get("status") == "ok" else 500
    return jsonify(result), status_code
