import smtplib
import uuid
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

from everyclass.auth.config import get_config
from everyclass.auth.consts import Message
from everyclass.auth.db.dao import check_if_have_registered, check_if_request_id_exist
from everyclass.auth.db.redis import redis_client

config = get_config()


def send_email(email, token):
    """
    给指定账号发送含有指定token的邮件
    :param email: str,需要发送的邮箱账号
    :param token: str，需要给该邮箱账号发送的token
    """
    from everyclass.auth import logger
    logger.info("Sending email to {}".format(email))

    sender = config.EMAIL['SENDER']
    receivers = email
    # message = MIMEText(token, 'html', 'utf-8')
    message = MIMEMultipart('related')
    message['From'] = _format_address("每课 <verification@mail.everyclass.xyz>")
    message['To'] = _format_address("每课用户 <%s>" % email)
    message['Subject'] = Header('每课@CSU 学生身份验证', charset='utf-8').encode()

    message_alternative = MIMEMultipart('alternative')
    message.attach(message_alternative)

    with open('everyclass/auth/static/everyclass_email.html', 'r', encoding='utf-8') as email_html, open(
            'everyclass/auth/static/everyclass_icon.png', 'rb') as logo_file:
        original_text = email_html.read()
        text = original_text.format(config.SERVER_BASE_URL, token)
        email_html.close()

        message_alternative.attach(MIMEText(text, 'html', 'utf-8'))

        # 指定图片为当前目录
        message_image = MIMEImage(logo_file.read())

        # 定义图片 ID，在 HTML 文本中引用
        message_image.add_header('Content-ID', '<image1>')
        message.attach(message_image)

        smtp_obj = smtplib.SMTP(host=config.EMAIL['HOST'], port=config.EMAIL['PORT'])
        smtp_obj.connect(host=config.EMAIL['HOST'], port=config.EMAIL['PORT'])  # SMTP 端口号

        smtp_obj.ehlo()
        smtp_obj.starttls()

        smtp_obj.login(config.EMAIL['USERNAME'], config.EMAIL['PASSWORD'])
        smtp_obj.sendmail(sender, receivers, message.as_string())
        smtp_obj.quit()

        logger.info("Email sent to {} with token {}".format(email, token))


def _format_address(email):
    """邮件地址的格式化"""
    name, address = parseaddr(email)
    return formataddr((Header(name, 'utf-8').encode(), address))


def handle_email_register_request(request_id: str, username: str):
    """
    处理redis队列中的通过邮箱验证的请求

    :param request_id: str, 请求 ID
    :param username: str, 学号
    """
    from everyclass.auth import logger
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
