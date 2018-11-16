from .default import Config


class DevelopmentConfig(Config):
    DEBUG = False
    SECRET_KEY = 'development key'

    # Sentry
    SENTRY_CONFIG = {
       # 'dsn'    : 'https://299b791f00a6435a80d3acd39b7ca9cb@sentry.admirable.pro//2',
       # 'release': Config.GIT_DESCRIBE,
       # 'tags'   : {'environment': 'development'}
    }

    # HTML minify
    HTML_MINIFY = True

    # Static file settings
    # STATIC_VERSIONED = False
    STATIC_VERSIONED = True

    # Database config
    MYSQL_CONFIG = {
        # 'user'       : 'root',
        # 'password': ',G(mvC4ocooZt)KjGt',
        'user'       : 'root',
        'password'   : 'root',
        'host'       : 'localhost',
        'port'       : 3306,
        'db'   : 'everyclass_login',
        'use_unicode': True,
        'charset'    : 'utf8mb4'
    }

    ELASTIC_APM = {
        'SERVICE_NAME': 'everyclass-api_server',
        'SECRET_TOKEN': 'token',
        'SERVER_URL'  : 'http://10.140.0.2:8200',
    }

    REDIS_CONFIG = {
        'host': '127.0.0.1',
        'port': 6379
    }

