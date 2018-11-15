import json
import re
import time

from everyclass.auth.db.redisdb import redis_client
from everyclass.auth import logger
from everyclass.auth.utils import handle_email_register_request, handle_browser_register_request


class RedisQueue(object):
    """
    redis队列类
    """
    def __init__(self, name, namespace='queue'):
        # redis的默认参数为：host='localhost', port=6379, db=0， 其中db为定义redis database的数量
        self.__db = redis_client
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        return self.__db.llen(self.key)  # 返回队列里面list内元素的数量

    def put(self, item):
        self.__db.rpush(self.key, item)  # 添加新元素到队列最右方

    def get_wait(self, timeout=None):
        # 返回队列第一个元素，如果为空则等待至有元素被加入队列（超时时间阈值为timeout，如果为None则一直等待）
        item = self.__db.blpop(self.key, timeout=timeout)
        return item

    def get_nowait(self):
        # 直接返回队列第一个元素，如果队列为空返回的是None
        item = self.__db.lpop(self.key)
        return item


def start_register_queue():
    """
    启动用于缓存用户请求的队列
    如果为空则等待至有元素被加入队列
    并通过请求不同的验证方式调用不同的处理函数
    """
    user_queue = RedisQueue('everyclass')
    while True:
        print('p1 start')
        # 队列返回的第一个参数为频道名，第二个参数为存入的值
        result = user_queue.get_wait()[1]
        print(result)
        if not result:
            continue
        user_inf_str = bytes.decode(result)
        user_inf_str = re.sub('\'', '\"', user_inf_str)
        user_inf = json.loads(user_inf_str)

        if user_inf['method'] == 'browser':
            r = handle_browser_register_request(user_inf['request_id'], user_inf['username'], user_inf['password'])
            print(r)
        if user_inf['method'] == 'email':
            handle_email_register_request(user_inf['request_id'], user_inf['username'])

        time.sleep(2)







