import os


class BaseConfig(object):
    # 启用慢查询记录功能(调试模式下自动启用), 为了在生产环境下可用，必须手动配置此项为True
    SQLALCHEMY_RECORD_QUERIES = True
    # 慢查询阈值
    FLASK_SLOW_DB_QUERY_TIME = 0.001


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_DEVELOPMENT_URI")


class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_Testing_URI")


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_PRODUCTION_URI')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    "dsn": "https://db2ab008ee2f45538ab8039698614617@o973528.ingest.sentry.io/5925003",
    "log_path": 'TU/logs',
}

PLANNING_URL = "http://10.11.80.221:4000/brain/reasoning"
INTENTION_URL = "10.11.80.108"
QUERY_URL = "http://10.5.24.30:8888/kbservice/v2/search/"

QUERY_EXHIBITION_BY_NAME = "point/by_name"

PARAMETER_DELIMITER = ";"
PARAMETER_KEY_VALUE_DELIMITER = ";"

