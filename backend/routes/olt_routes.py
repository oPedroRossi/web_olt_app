from flask import Blueprint

from backend.controllers.olt_controller import (
    health,
    index,
    reboot_onu_handler,
    status_olt,
    unlocked_btn,
)

olt_bp = Blueprint("olt", __name__)

olt_bp.add_url_rule("/", view_func=index)
olt_bp.add_url_rule("/health", view_func=health)
olt_bp.add_url_rule("/olt/", view_func=status_olt, methods=["POST"])
olt_bp.add_url_rule("/olt/unlocked/", view_func=unlocked_btn, methods=["POST"])
olt_bp.add_url_rule("/olt/reboot/", view_func=reboot_onu_handler, methods=["POST"])
