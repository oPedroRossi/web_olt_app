from flask import Flask

from backend.config.settings import get_settings
from backend.routes.olt_routes import olt_bp


def create_app() -> Flask:
    settings = get_settings()

    app = Flask(__name__)
    app.config["APP_HOST"] = settings.app_host
    app.config["APP_PORT"] = settings.app_port
    app.config["FLASK_DEBUG"] = settings.flask_debug

    app.register_blueprint(olt_bp)
    return app
