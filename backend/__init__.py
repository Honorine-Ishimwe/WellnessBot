"""
WellnessBot — Flask application factory.
Creates and configures the Flask app with all extensions and blueprints.
"""

import os

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # ── CORS ──────────────────────────────────────────────
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
    if allowed_origins != "*":
        allowed_origins = [o.strip() for o in allowed_origins.split(",")]
    CORS(app, origins=allowed_origins)

    # ── Rate Limiter ──────────────────────────────────────
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per hour"],
        storage_uri="memory://",
    )
    # Store limiter on app so blueprints can access it
    app.limiter = limiter

    # ── Logging middleware ────────────────────────────────
    from backend.middleware.logging import request_logging_middleware
    request_logging_middleware(app)

    # ── Register blueprints ──────────────────────────────
    from backend.routes.health import health_bp
    from backend.routes.auth import auth_bp
    from backend.routes.chat import chat_bp
    from backend.routes.conversations import conversations_bp
    from backend.routes.goals import goals_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(goals_bp)

    # ── Initialize DB ────────────────────────────────────
    from backend.db import init_db
    from backend.middleware.logging import logger

    with app.app_context():
        try:
            init_db()
        except Exception as e:
            logger.warning(f"DB init skipped (will retry on first request): {e}")

    return app
