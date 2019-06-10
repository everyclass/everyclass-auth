import datetime
import json
import re
import sys
import threading

import gc
import logbook
from flask import Flask
from raven.contrib.flask import Sentry
from raven.handlers.logbook import SentryHandler

from everyclass.auth.db.mongodb import init_pool

logger = logbook.Logger(__name__)
sentry = Sentry()
__app = None
__load_time = datetime.datetime.now()

try:
    import uwsgidecorators

    """
    使用 `uwsgidecorators.postfork` 装饰的函数会在 fork() 后的**每一个**子进程内被执行，执行顺序与这里的定义顺序一致
    """

    @uwsgidecorators.postfork
    def enable_gc():
        """重新启用垃圾回收"""
        gc.set_threshold(700)

    @uwsgidecorators.postfork
    def init_log_handlers():
        """初始化 log handlers 并将当前配置信息打 log"""
        from everyclass.auth.util.logbook_logstash.handler import LogstashHandler
        from everyclass.auth.config import print_config
        from elasticapm.contrib.flask import ElasticAPM

        # Elastic APM
        if __app.config['CONFIG_NAME'] in __app.config['APM_AVAILABLE_IN']:
            ElasticAPM(__app)
            logger.info('APM is inited because you are in {} mode.'.format(__app.config['CONFIG_NAME']))

        # Logstash centralized log
        if __app.config['CONFIG_NAME'] in __app.config['LOGSTASH_AVAILABLE_IN']:
            logstash_handler = LogstashHandler(host=__app.config['LOGSTASH']['HOST'],
                                               port=__app.config['LOGSTASH']['PORT'],
                                               release=__app.config['GIT_DESCRIBE'],
                                               bubble=True,
                                               logger=logger,
                                               filter=lambda r, h: r.level >= 11)  # do not send DEBUG
            logger.handlers.append(logstash_handler)
            logger.info('LogstashHandler is inited because you are in {} mode.'.format(__app.config['CONFIG_NAME']))

        # Sentry
        if __app.config['CONFIG_NAME'] in __app.config['SENTRY_AVAILABLE_IN']:
            sentry.init_app(app=__app)
            sentry_handler = SentryHandler(sentry.client, level='WARNING')  # Sentry 只处理 WARNING 以上的
            logger.handlers.append(sentry_handler)
            logger.info('Sentry is inited because you are in {} mode.'.format(__app.config['CONFIG_NAME']))

        # 如果当前时间与模块加载时间相差一分钟之内，认为是第一次 spawn（进程随着时间的推移可能会被 uwsgi 回收），
        # 在 1 号 worker 里打印当前配置
        import uwsgi
        if uwsgi.worker_id() == 1 and (datetime.datetime.now() - __load_time) < datetime.timedelta(minutes=1):
            # 这里设置等级为 warning 因为我们希望在 sentry 里监控重启情况
            logger.warning('App (re)started in `{0}` environment'
                           .format(__app.config['CONFIG_NAME']), stack=False)
            print_config(__app)

    @uwsgidecorators.postfork
    def init_db():
        """init database connection"""
        global __app
        logger.info("Connecting to MongoDB...")
        init_pool(__app)

    @uwsgidecorators.postfork
    def init_queue_worker():
        """spawn queue worker thread for each queue"""
        threading.Thread(target=queue_worker).start()
except ModuleNotFoundError:
    pass


def create_app():
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
    if app.config['CONFIG_NAME'] in app.config['DEBUG_LOG_AVAILABLE_IN']:
        stdout_handler = logbook.StreamHandler(stream=sys.stdout, bubble=True, filter=lambda r, h: r.level < 13)
    else:
        # ignore debug when not in debug
        stdout_handler = logbook.StreamHandler(stream=sys.stdout, bubble=True, filter=lambda r, h: 10 < r.level < 13)
    stdout_handler.format_string = LOG_FORMAT_STRING
    logger.handlers.append(stdout_handler)

    stderr_handler = logbook.StreamHandler(stream=sys.stderr, bubble=True, level='WARNING')
    stderr_handler.format_string = LOG_FORMAT_STRING
    logger.handlers.append(stderr_handler)

    from everyclass.auth.views import user_blueprint
    app.register_blueprint(user_blueprint)

    # 初始化数据库
    if app.config['CONFIG_NAME'] == 'development':
        init_pool(app)

    global __app
    __app = app

    return app


def queue_worker():
    """
    启动用于缓存用户请求的队列
    如果为空则等待至有元素被加入队列
    并通过请求不同的验证方式调用不同的处理函数
    """
    logger.debug('Queue worker started')

    ctx = __app.app_context()
    ctx.push()

    from everyclass.auth.queue import handle_email_register_request, handle_browser_register_request
    from everyclass.auth.db.redis import redis_client

    sub = redis_client.pubsub()
    sub.subscribe('cctv')
    for item in sub.listen():
        if item['type'] == 'message':
            user_inf_str = bytes.decode(item['data'])
            user_inf_str = re.sub('\'', '\"', user_inf_str)
            user_inf = json.loads(user_inf_str)
            logger.debug(user_inf)
            if user_inf['method'] == 'password':
                handle_browser_register_request(user_inf['request_id'], user_inf['username'], user_inf['password'])
            if user_inf['method'] == 'email':
                handle_email_register_request(user_inf['request_id'], user_inf['username'])

