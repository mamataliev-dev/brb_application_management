import os
import redis


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 'postgresql://url'
    )

    SECRET_KEY = "secret"
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis.StrictRedis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=False
    )
    ADMIN_SESSION_KEY_PREFIX = "admin_session:"
    MANAGER_SESSION_KEY_PREFIX = "manager_session:"
    # Directory to save flask sessions
    # app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'

    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True

    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'sqlite:///:memory:')


class ProductionConfig(Config):
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'PROD_DATABASE_URI',
        'postgresql://url'
    )
