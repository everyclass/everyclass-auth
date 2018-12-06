import sys
import threading

from flask import Flask
import logbook
from elasticapm.contrib.flask import ElasticAPM
from raven.contrib.flask import Sentry
from raven.handlers.logbook import SentryHandler


# from everyclass.auth.handle_register_queue import start_register_queue



import json
import re
import time

from everyclass.auth.db.mysql import init_pool

logger = logbook.Logger(__name__)

sentry = Sentry()


def create_app(offline=False):
    print('call create_app')
    from everyclass.utils.logbook_logstash.handler import LogstashHandler
    from everyclass.utils.logbook_logstash.formatter import LOG_FORMAT_STRING

    app = Flask(__name__)

    # load app config
    from everyclass.auth.config import get_config
    _config = get_config()
    app.config.from_object(_config)

    """
    每课统一日志机制


    规则如下：
    - WARNING 以下 log 输出到 stdout
    - WARNING 以上输出到 stderr
    - DEBUG 以上日志以 json 形式通过 TCP 输出到 Logstash，然后发送到日志中心
    - WARNING 以上级别的输出到 Sentry


    日志等级：
    critical – for errors that lead to termination
    error – for errors that occur, but are handled
    warning – for exceptional circumstances that might not be errors
    notice – for non-error messages you usually want to see
    info – for messages you usually don’t want to see
    debug – for debug messages


    Sentry：
    https://docs.sentry.io/clients/python/api/#raven.Client.captureMessage
    - stack 默认是 False

    """
    stdout_handler = logbook.StreamHandler(stream=sys.stdout, bubble=True, filter=lambda r, h: r.level < 13)
    stdout_handler.format_string = LOG_FORMAT_STRING
    logger.handlers.append(stdout_handler)

    stderr_handler = logbook.StreamHandler(stream=sys.stderr, bubble=True, level='WARNING')
    stderr_handler.format_string = LOG_FORMAT_STRING
    logger.handlers.append(stderr_handler)

    if not offline and (app.config['CONFIG_NAME'] in ["production", "staging", "testing"]):
        # Sentry
        sentry.init_app(app=app)
        sentry_handler = SentryHandler(sentry.client, level='WARNING')  # Sentry 只处理 WARNING 以上的
        logger.handlers.append(sentry_handler)

        # Elastic APM
        ElasticAPM(app)
        # Log to Logstash
        logstash_handler = LogstashHandler(host=app.config['LOGSTASH']['HOST'],
                                           port=app.config['LOGSTASH']['PORT'],
                                           release=app.config['GIT_DESCRIBE'],
                                           logger=logger)
        logger.handlers.append(logstash_handler)

    from everyclass.auth.user import user_blueprint
    app.register_blueprint(user_blueprint)

    # 初始化数据库
    init_pool(app)

    logger.info('App created with `{0}` config'.format(app.config['CONFIG_NAME']))

    #开一个新线程来运行队列函数

    threading.Thread(target=start_register_queue).start()
    return app


def start_register_queue():
    """
    启动用于缓存用户请求的队列
    如果为空则等待至有元素被加入队列
    并通过请求不同的验证方式调用不同的处理函数
    """
    print('call start register queue')

    from everyclass.auth.handle_register_queue import RedisQueue
    from everyclass.auth.utils import handle_email_register_request, handle_browser_register_request
    from everyclass.auth.db.redisdb import redis_client

    user_queue = RedisQueue('everyclass')
    while True:
        logger.info('RedisQueue start')
        # 队列返回的第一个参数为频道名，第二个参数为存入的值
        result = user_queue.get_wait()[1]
        if not result:
            continue
        user_inf_str = bytes.decode(result)
        user_inf_str = re.sub('\'', '\"', user_inf_str)
        user_inf = json.loads(user_inf_str)
        if user_inf['method'] == 'password':
            handle_browser_register_request(user_inf['request_id'], user_inf['username'], user_inf['password'])
        if user_inf['method'] == 'email':
            inf = handle_email_register_request(user_inf['request_id'], user_inf['username'])
            print(inf)
        time.sleep(2)




