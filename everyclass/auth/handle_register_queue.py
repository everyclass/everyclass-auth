import uuid

from everyclass.auth.db.mysql import check_if_request_id_exist, check_if_have_registered, insert_browser_account
from everyclass.auth import logger
from everyclass.auth.db.redisdb import redis_client
from everyclass.auth.browse_identify import simulate_login_noidentifying
from everyclass.auth.email_identify import send_email


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

    def handle_browser_register_request(self, request_id: str, username: str, password: str):
        """
        处理redis队列中的通过浏览器验证的请求

        """
        from everyclass.auth.handle_register_queue import redis_client

        if check_if_request_id_exist(request_id):
            logger.warning("request_id as primary key reuses")
            return False, 'request_id as primary key reuses'

        if check_if_have_registered(username):
            redis_client.set("auth:request_status:%s" % request_id, 'student has registered', ex=86400)
            logger.info('student_id:%s identify fail becacuse id has registered' % username)
            return False, 'student has registered'

        # 判断该用户是否为中南大学学生
        # result数组第一个参数为bool类型判断验证是否成功，第二个参数为出错原因
        result = simulate_login_noidentifying(username, password)
        logger.debug(result)
        # 密码错误
        if not result[0]:
            redis_client.set("auth:request_status:%s" % request_id, 'password wrong', ex=86400)
            logger.info('student_id:%s identify fail because password wrong' % username)
            return False, result[1]

        # 经判断是中南大学学生，生成token，并将相应数据持久化
        redis_client.set("auth:request_status:%s" % request_id, 'identify a student in csu', ex=86400)  # 1 day
        logger.info('student_id:%s identify success' % username)
        insert_browser_account(request_id, username, 'browser')

        return True, 'identify a student in csu'

    def handle_email_register_request(self, request_id: str, username: str):
        """
        处理redis队列中的通过邮箱验证的请求

        :param request_id: str, 请求 ID
        :param username: str, 学号
        """
        from everyclass.auth.handle_register_queue import redis_client

        if check_if_request_id_exist(request_id):
            logger.warning("request_id as primary key reuses")
            return False, 'request_id as primary key reuses'

        if check_if_have_registered(username):
            redis_client.set("auth:request_status:%s" % request_id, 'student has registered', ex=86400)
            logger.info('student_id:%s identify fail becacuse id has registered' % username)
            return False, 'student has registered'

        logger.debug("use handle_email_register_request")
        email = username + "@csu.edu.cn"
        token = str(uuid.uuid1())
        send_email(email, token)
        redis_client.set("auth:request_status:%s" % request_id, 'sendEmail success', ex=86400)
        request_info = "%s:%s" % (request_id, username)
        redis_client.set("auth:email_token:%s" % token, request_info, ex=86400)
        logger.debug("auth:email_token:%s" % token)
        return True, 'sendEmail success'
