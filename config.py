import os
from datetime import timedelta


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 'postgresql://postgres:mamatdiordmli@localhost:5432/brb'
    )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True

    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'sqlite:///:memory:')


class ProductionConfig(Config):
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'PROD_DATABASE_URI',
        'postgresql://brb_beta_db_user:47t1uwFZJyiNWCF6aaSXC0WEuj4eLlzc@dpg-cutdn5ggph6c73b1qnj0-a.oregon-postgres.render.com/brb_beta_db'
    )
