import logging
import sys

from flask import Flask
from logging.handlers import RotatingFileHandler
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_session import Session

from app.api.graphql import schema
from app.extensions import db, migrate, redis_client


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


def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    CORS(app, resources={r"/.*": {"origins": "*"}})
    app.config.from_object(config_class)

    Session(app)

    redis_client.connection_pool.connection_kwargs.update(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB']
    )

    db.init_app(app)
    migrate.init_app(app, db)

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql",
            schema=schema,
            graphiql=True
        )
    )

    @app.after_request
    def apply_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        return response

    return app
