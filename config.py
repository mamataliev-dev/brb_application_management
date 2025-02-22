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
        'postgres://koyeb-adm:npg_rs07lpnDkXBt@ep-super-shape-a2oowjjw.eu-central-1.pg.koyeb.app/koyebdb'
    )
