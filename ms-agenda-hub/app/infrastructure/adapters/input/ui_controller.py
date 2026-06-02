from flask import Blueprint, send_from_directory
import os

# Determinar la ruta absoluta al directorio 'static' relativo a este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

ui_bp = Blueprint("ui", __name__)


def create_ui_routes():

    @ui_bp.route("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @ui_bp.route("/static/<path:path>")
    def serve_static(path):
        return send_from_directory(STATIC_DIR, path)

    return ui_bp
