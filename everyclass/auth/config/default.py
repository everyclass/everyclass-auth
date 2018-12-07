import git
import os


class Config(object):
    """
    Basic Configurations
    """
    DEBUG = False
    SECRET_KEY = 'development_key'

    MYSQL_CONFIG = {
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'port': 3306,
        'db': 'everyclass_login',
        'use_unicode': True,
        'charset': 'utf8mb4'
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
        'dsn'    : '',
        'release': '',
        'tags'   : {'environment': 'default'}
    }
    ELASTIC_APM = {
        'SERVICE_NAME'   : 'everyclass-api_server',
        'SECRET_TOKEN'   : 'token',
        'SERVER_URL'     : 'http://127.0.0.1:8200',
        # https://www.elastic.co/guide/en/apm/agent/python/2.x/configuration.html#config-auto-log-stacks
        'AUTO_LOG_STACKS': False,
        'SERVICE_VERSION': GIT_DESCRIBE
    }
    LOGSTASH = {
        'HOST': '127.0.0.1',
        'PORT': 8888
    }

    """
    邮件SMTP服务相关设置
    """
    EMAIL = {
        'mail_host': 'smtp.mailgun.org',
        'mail_user': 'verification@mail.everyclass.xyz',
        'mail_pass': '12234',
        'sender':    'verification@mail.everyclass.xyz',
        'SMTP_port': 2525

    }

    """
    维护模式
    """
    MAINTENANCE_FILE = os.path.join(os.getcwd(), 'maintenance')
    if os.path.exists(MAINTENANCE_FILE):
        MAINTENANCE = True
    else:
        MAINTENANCE = False
