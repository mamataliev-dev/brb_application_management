import os
import redis


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 'postgresql://postgres:mamatdiordmli@localhost:5432/brb'
    )

    SECRET_KEY = "e31692cd6a66dca5d56d0a5ccc48d528cfbf2cd1331865aa68a55398f6827d1a"
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
        'postgresql://brb_db_3uzl_user:WZ8AXXVGcMS29oqBnHj2SuNUfZ6Pw025@dpg-cutdri2j1k6c738bk63g-a.oregon-postgres.render.com/brb_db_3uzl'
    )
