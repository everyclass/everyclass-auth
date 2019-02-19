import uuid

from everyclass.auth import logger
from everyclass.auth.db.dao import check_if_have_registered, check_if_request_id_exist, insert_browser_account
from everyclass.auth.db.redis import redis_client
from everyclass.auth.email_identify import send_email
from everyclass.auth.messages import Message
from everyclass.auth.password_identify import simulate_login_noidentifying


class RedisQueue(object):
    """
    redis队列类
    """

    def __init__(self, name='task', namespace='auth'):
        # redis的默认参数为：host='localhost', port=6379, db=0， 其中db为定义redis database的数量
        self._db = redis_client
        self.key = "{namespace}:{key_name}".format(namespace=namespace, key_name=name)

    def qsize(self):
        return self._db.llen(self.key)  # 返回队列里面list内元素的数量

    def put(self, item):
        self._db.rpush(self.key, item)  # 添加新元素到队列最右方

    def get_wait(self, timeout=None):
        # 返回队列第一个元素，如果为空则等待至有元素被加入队列（超时时间阈值为timeout，如果为None则一直等待）
        item = self._db.blpop(self.key, timeout=timeout)
        return item

    def get_nowait(self):
        # 直接返回队列第一个元素，如果队列为空返回的是None
        item = self._db.lpop(self.key)
        return item

    @staticmethod
    def handle_browser_register_request(request_id: str, username: str, password: str):
        """
        处理redis队列中的通过浏览器验证的请求

        """
        if check_if_request_id_exist(request_id):
            logger.warning("request_id reuses as primary key. Rejected.")
            return False, Message.INTERNAL_ERROR

        if check_if_have_registered(username):
            redis_client.set("auth:request_status:%s" % request_id, Message.INTERNAL_ERROR, ex=86400)
            logger.warn("User try to register for a second time. Rejected." % username)
            return False, Message.INTERNAL_ERROR

        # 判断该用户是否为中南大学学生
        # result数组第一个参数为bool类型判断验证是否成功，第二个参数为出错原因
        success, cause = simulate_login_noidentifying(username, password)

        # 验证失败
        if not success:
            redis_client.set("auth:request_status:%s" % request_id, cause, ex=86400)
            logger.info("User {} password verification failed({}).".format(username, cause))
            return False, cause

        # 经判断是中南大学学生，生成token，并将相应数据持久化
        redis_client.set("auth:request_status:%s" % request_id, Message.IDENTIFYING_SUCCESS, ex=86400)  # 1 day
        logger.info('User %s password verification success.' % username)
        insert_browser_account(request_id, username, 'browser')

        return True, Message.SUCCESS

    @staticmethod
    def handle_email_register_request(request_id: str, username: str):
        """
        处理redis队列中的通过邮箱验证的请求

        :param request_id: str, 请求 ID
        :param username: str, 学号
        """

        if check_if_request_id_exist(request_id):
            logger.warning("request_id reuses as primary key. Rejected.")
            return False, Message.INTERNAL_ERROR

        if check_if_have_registered(username):
            redis_client.set("auth:request_status:%s" % request_id, Message.INTERNAL_ERROR, ex=86400)
            logger.warn("User try to register for a second time. Rejected." % username)
            return False, Message.INTERNAL_ERROR

        email = username + "@csu.edu.cn"
        token = str(uuid.uuid1())
        send_email(email, token)

        redis_client.set("auth:request_status:%s" % request_id, Message.SEND_EMAIL_SUCCESS, ex=86400)
        request_info = "%s:%s" % (request_id, username)
        redis_client.set("auth:email_token:%s" % token, request_info, ex=86400)
        return True, Message.SUCCESS
