import git


class Config(object):
    """
    Basic Configurations
    """
    DEBUG = False
    SECRET_KEY = 'development_key'

    MONGO = {
        'host'              : 'mongodb',
        'port'              : 12306,
        'uuidRepresentation': 'standard'
    }
    MONGO_DB = 'everyclass_auth'
    REDIS_CONFIG = {
        'host': '127.0.0.1',
        'port': 6379,
        'db'  : 1
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
        'RELSEASE': '',
        'TAGS'    : {'environment': 'default'}
    }
    ELASTIC_APM = {
        'SERVICE_NAME'   : 'everyclass-auth_server',
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

    # define available environments for logs, APM and error tracking
    SENTRY_AVAILABLE_IN = ['production', 'staging', 'testing']
    APM_AVAILABLE_IN = ['production', 'staging', 'testing']
    LOGSTASH_AVAILABLE_IN = ['production', 'staging', 'testing']

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
