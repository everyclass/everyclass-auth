import datetime
import json
import re
import logging
import threading
import gc

from flask import Flask
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler

from everyclass.auth.db.mongodb import init_pool

logger = logging.getLogger(__name__)
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
    def init_plugins():
        """初始化 log handlers 并将当前配置信息打 log"""
        from everyclass.auth.config import print_config

        # Sentry
        if __app.config['CONFIG_NAME'] in __app.config['SENTRY_AVAILABLE_IN']:
            sentry.init_app(app=__app)
            sentry_handler = SentryHandler(sentry.client)
            sentry_handler.setLevel(logging.WARNING)
            logging.getLogger().addHandler(sentry_handler)

        # 如果当前时间与模块加载时间相差一分钟之内，认为是第一次 spawn（进程随着时间的推移可能会被 uwsgi 回收），
        # 在 1 号 worker 里打印当前配置
        import uwsgi
        if uwsgi.worker_id() == 1 and (datetime.datetime.now() - __load_time) < datetime.timedelta(minutes=1):
            # 这里设置等级为 warning 因为我们希望在 sentry 里监控重启情况
            logger.warning('App (re)started in `{0}` environment'.format(__app.config['CONFIG_NAME']))
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
    app = Flask(__name__)

    # load app config
    from everyclass.auth.config import get_config
    _config = get_config()
    app.config.from_object(_config)

    # 日志
    if app.config['DEBUG']:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

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
    from everyclass.auth.handle_request import handle_email_register_request, handle_browser_register_request
    logger.debug('Queue worker started')

    ctx = __app.app_context()
    ctx.push()

    from everyclass.auth.handle_register_queue import RedisQueue
    from everyclass.auth.db.redis import redis_client

    user_queue = RedisQueue("everyclass")
    while True:
        result = user_queue.get_wait()[1]  # 队列返回的第一个参数为频道名，第二个参数为存入的值
        if not result:
            continue
        request_info = bytes.decode(result)
        request_info = re.sub('\'', '\"', request_info)
        request_info = json.loads(request_info)
        if request_info['method'] == 'password':
            handle_browser_register_request(request_info['request_id'],
                                            request_info['username'],
                                            request_info['password'])
        if request_info['method'] == 'email':
            handle_email_register_request(request_info['request_id'],
                                          request_info['username'])
