import logging
import sys

from flask import Flask
from logging.handlers import RotatingFileHandler
from flask_cors import CORS

from app.extensions import db, migrate
from app.api import api_blueprint


def setup_logging():
    """Configures application-wide logging."""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    file_handler = RotatingFileHandler("app.log", maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


def create_app(config_class='config.ProductionConfig'):
    app = Flask(__name__)
    CORS(app, resources={r"/.*": {"origins": "*"}})
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api_blueprint)

    return app
