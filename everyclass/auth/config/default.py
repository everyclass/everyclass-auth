import git


class Config(object):
    """
    Basic Configurations
    """
    DEBUG = False
    SECRET_KEY = 'development_key'

    REDIS_CONFIG = {
        'host': '127.0.0.1',
        'port': 6379,
        'db'  : 1
    }

    POSTGRES_SCHEMA = "everyclass_auth"
    POSTGRES_CONNECTION = {
        'dbname': 'everyclass',
        'user': 'everyclass_auth',
        'password': 'everyclass_auth',
        'host': 'localhost',
        'port': 5432
    }

    """
    Git Hash
    """
    _git_repo = git.Repo(search_parent_directories=True)
    GIT_HASH = _git_repo.head.object.hexsha
    try:
        GIT_BRANCH_NAME = _git_repo.active_branch.name
    except TypeError:
        GIT_BRANCH_NAME = 'detached'
    _describe_raw = _git_repo.git.describe(tags=True).split("-")  # like `v0.8.0-1-g000000`
    GIT_DESCRIBE = _describe_raw[0]  # actual tag name like `v0.8.0`
    if len(_describe_raw) > 1:
        GIT_DESCRIBE += "." + _describe_raw[1]  # tag 之后的 commit 计数，代表小版本
        # 最终结果类似于：v0.8.0.1

    """
    APM and error tracking platforms
    """
    SENTRY_CONFIG = {
        'DSN'     : '',
        'RELEASE': '',
        'TAGS'    : {'environment': 'default'}
    }

    """
    邮件SMTP服务相关设置
    """
    EMAIL = {
        'HOST'    : 'smtp',
        'USERNAME': 'mail_user',
        'PASSWORD': '12234',
        'SENDER'  : 'mail_sender',
        'PORT'    : 2525
    }

    SERVER_BASE_URL = "https://everyclass.xyz"

    # define available environments for logs, APM and error tracking
    SENTRY_AVAILABLE_IN = ('production', 'staging', 'testing')

    # fields that should be overwritten in production environment
    PRODUCTION_OVERWRITE_FIELDS = ()

    # fields that should not be in log
    PRODUCTION_SECURE_FIELDS = ("SENTRY_CONFIG.dsn",
                                "REDIS_CONFIG.password",
                                "MONGO.password",
                                "SECRET_KEY",
                                "EMAIL.PASSWORD"
                                )
