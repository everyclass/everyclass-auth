import gc
import json
import re
import sys
import threading

import logbook
from elasticapm.contrib.flask import ElasticAPM
from flask import Flask
from raven.contrib.flask import Sentry
from raven.handlers.logbook import SentryHandler

from everyclass.auth.db.mysql import init_pool

logger = logbook.Logger(__name__)
sentry = Sentry()
__app = None

try:
    import uwsgidecorators

    """
    below are functions that will be executed in **each** process after fork().
    these functions will be executed in the same order of definition here.
    """


    @uwsgidecorators.postfork
    def enable_gc():
        """enable garbage collection"""
        gc.set_threshold(700)


    @uwsgidecorators.postfork
    def init_db():
        """init database connection"""
        global __app
        init_pool(__app)


    @uwsgidecorators.postfork
    def init_log_handlers():
        """init log handlers"""
        from everyclass.auth.util.logbook_logstash.handler import LogstashHandler
        from elasticapm.contrib.flask import ElasticAPM

        global __app, __sentry_available

        # Sentry
        if __app.config['CONFIG_NAME'] in __app.config['SENTRY_AVAILABLE_IN']:
            sentry.init_app(app=__app)
            sentry_handler = SentryHandler(sentry.client, level='WARNING')  # Sentry 只处理 WARNING 以上的
            logger.handlers.append(sentry_handler)
            __sentry_available = True
            logger.info('You are in {} mode, so Sentry is inited.'.format(__app.config['CONFIG_NAME']))

        # Elastic APM
        if __app.config['CONFIG_NAME'] in __app.config['APM_AVAILABLE_IN']:
            ElasticAPM(__app)
            logger.info('You are in {} mode, so APM is inited.'.format(__app.config['CONFIG_NAME']))

        # Logstash centralized log
        if __app.config['CONFIG_NAME'] in __app.config['LOGSTASH_AVAILABLE_IN']:
            logstash_handler = LogstashHandler(host=__app.config['LOGSTASH']['HOST'],
                                               port=__app.config['LOGSTASH']['PORT'],
                                               release=__app.config['GIT_DESCRIBE'],
                                               bubble=True,
                                               logger=logger,
                                               filter=lambda r, h: r.level >= 11)  # do not send DEBUG
            logger.handlers.append(logstash_handler)
            logger.info('You are in {} mode, so LogstashHandler is inited.'.format(__app.config['CONFIG_NAME']))
except ModuleNotFoundError:
    pass


def create_app(offline=False):
    logger.debug('call create_app')
    from everyclass.auth.util.logbook_logstash.handler import LogstashHandler
    from everyclass.auth.util.logbook_logstash.formatter import LOG_FORMAT_STRING

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

    from everyclass.auth.views import user_blueprint
    app.register_blueprint(user_blueprint)

    # 初始化数据库
    if app.config['CONFIG_NAME'] == 'development':
        init_pool(app)

    logger.info('App created with `{0}` config'.format(app.config['CONFIG_NAME']))

    global __app
    __app = app

    # 开一个新线程来运行队列函数
    # todo: 通过配置文件定义线程数
    threading.Thread(target=queue_worker).start()

    return app


def queue_worker():
    """
    启动用于缓存用户请求的队列
    如果为空则等待至有元素被加入队列
    并通过请求不同的验证方式调用不同的处理函数
    """
    logger.debug('Queue worker started')
    global __app
    ctx = __app.app_context()
    ctx.push()

    from everyclass.auth.queue import RedisQueue
    from everyclass.auth.db.redis import redis_client

    user_queue = RedisQueue()
    while True:
        result = user_queue.get_wait()[1]  # 队列返回的第一个参数为频道名，第二个参数为存入的值
        if not result:
            continue
        request_info = bytes.decode(result)
        request_info = re.sub('\'', '\"', request_info)
        request_info = json.loads(request_info)
        if request_info['method'] == 'password':
            user_queue.handle_browser_register_request(request_info['request_id'],
                                                       request_info['username'],
                                                       request_info['password'])
        if request_info['method'] == 'email':
            user_queue.handle_email_register_request(request_info['request_id'],
                                                     request_info['username'])
