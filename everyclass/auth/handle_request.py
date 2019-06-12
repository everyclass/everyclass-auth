import uuid

from everyclass.auth.db.dao import check_if_have_registered, check_if_request_id_exist, insert_browser_account
from everyclass.auth.db.redis import redis_client
from everyclass.auth.email_identify import send_email
from everyclass.auth.messages import Message
from everyclass.auth.password_identify import simulate_login_without_captcha


def handle_browser_register_request(request_id: str, username: str, password: str):
    """
    处理redis队列中的通过浏览器验证的请求

    """
    from everyclass.auth import logger
    if check_if_request_id_exist(request_id):
        logger.warning("request_id reuses as primary key. Rejected.")
        return False, Message.INTERNAL_ERROR

    if check_if_have_registered(username):
        logger.warn("User %s try to register for a second time." % username)

    # 判断该用户是否为中南大学学生
    # result数组第一个参数为bool类型判断验证是否成功，第二个参数为出错原因
    success, cause = simulate_login_without_captcha(username, password)

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
        logger.warn("User %s try to register for a second time. " % username)

    email = username + "@csu.edu.cn"
    token = str(uuid.uuid1())
    send_email(email, token)

    redis_client.set("auth:request_status:%s" % request_id, Message.SEND_EMAIL_SUCCESS, ex=86400)
    request_info = "%s:%s" % (request_id, username)
    redis_client.set("auth:email_token:%s" % token, request_info, ex=86400)
    return True, Message.SUCCESS
