#!/usr/bin/python
# -*- coding: UTF-8 -*-
import functools
import uuid
import time
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

from flask import abort, request
import smtplib
from pytesseract import pytesseract
from selenium import webdriver
from PIL import Image

from everyclass.auth.db.mysql import *
from everyclass.auth.handle_register_queue import redis_client
from everyclass.auth import logger
from everyclass.auth.config import get_config

config = get_config()


def json_payload(*fields, supposed_type=None, supposed_in=None):
    """
    装饰器，检查 MIME-type 是否为 json，并检查各个字段是否存在

    :param supposed_in: 如果指定了 `supposed_in`，检查字段是否在 `supposed_in` 内
    :param supposed_type: 如果指定了 `supposed_type`，检查各个字段的类型是否为 `supposed_type`
    """

    def decorator(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            if not request.json:
                return abort(400)
            for each_field in fields:
                if request.json.get(each_field) is None:
                    return abort(400)
                # 类型检查
                if supposed_type is not None and not isinstance(request.json.get(each_field), supposed_type):
                    return abort(400)
                # 区间检查
                if supposed_in is not None and request.json.get(each_field) not in supposed_in:
                    return abort(400)
            return func(*args, **kwargs)

        return _wrapped

    return decorator


def send_email(email, token):
    """
    给指定账号发送含有指定token的邮件
    :param email: str,需要发送的邮箱账号
    :param token: str，需要给该邮箱账号发送的token
    """
    # 第三方 SMTP 服务
    # mail_host = app.config['EMAIL_HOST']
    mail_host = config.EMAIL['mail_host']  # 设置服务器
    mail_user = config.EMAIL['mail_user']  # 用户名
    mail_pass = config.EMAIL['mail_pass']  # 口令

    sender = config.EMAIL['sender']
    receivers = email
    message = MIMEText(token, 'html', 'utf-8')
    # message['From'] = Header("每课 <verification@mail.everyclass.xyz>", charset='utf-8').encode()
    message['From'] = _format_address("每课 <verification@mail.everyclass.xyz>")
    # message['To'] = Header("user", charset='utf-8')
    message['To'] = _format_address("每课用户 <%s>" % email)
    message['Subject'] = Header('每课@CSU 学生身份验证', charset='utf-8').encode()

    smtpObj = smtplib.SMTP()
    smtpObj.connect(mail_host, config.EMAIL['SMTP_port'])  # SMTP 端口号

    smtpObj.ehlo()
    smtpObj.starttls()

    smtpObj.login(mail_user, mail_pass)
    smtpObj.sendmail(sender, receivers, message.as_string())
    smtpObj.quit()


def simulate_login(username: str, password: str):
    """
    浏览器模拟登陆
    :param username: str
    :param password: str
    :return:
    """
    # 创建chrome参数对象
    options = webdriver.ChromeOptions()
    # 把chrome设置成无界面模式
    options.add_argument('headless')
    # 创建chrome无界面对象
    driver = webdriver.Chrome(chrome_options=options)
    url = "http://csujwc.its.csu.edu.cn/"
    driver.get(url)

    name_input = driver.find_element_by_id("userAccount")  # 找到用户名的框框
    pass_input = driver.find_element_by_id('userPassword')  # 找到输入密码的框框
    name_input.clear()
    name_input.send_keys(username)  # 填写用户名
    time.sleep(0.2)
    pass_input.clear()
    pass_input.send_keys(password)  # 填写密码
    time.sleep(0.3)

    identifying_time = 0
    while identifying_time < 100:
        identifying_input = driver.find_element_by_id('RANDOMCODE')  # 找到验证码输入框
        login_button = driver.find_element_by_id('btnSubmit')  # 找到登录按钮
        identifying_pic = driver.find_element_by_id('SafeCodeImg')  # 找到验证码图片
        # 获取验证码位置
        box = (identifying_pic.rect['x'],
               identifying_pic.rect['y'],
               identifying_pic.rect['x'] + identifying_pic.rect['width'] - 100,
               identifying_pic.rect['y'] + identifying_pic.rect['height'])
        driver.save_screenshot("everyclass/auth/pic/system_screenshot.png")  # 截取屏幕内容，保存到本地
        # 打开截图，获取验证码位置，截取保存验证码
        img1 = Image.open("everyclass/auth/pic/system_screenshot.png")
        identifying_pic = img1.crop(box)
        identifying_pic.save("everyclass/auth/pic/code_screenshot.png")
        # 获取验证码图片，读取验证码
        identifying_code = pytesseract.image_to_string(identifying_pic)
        print(identifying_code)
        identifying_input.send_keys(identifying_code)
        login_button.click()  # 点击登录

        # 若验证码判断正确，即不出现验证码错误的提示，就会找不到提示元素，返回true
        driver.refresh()
        if driver.current_url == 'http://csujwc.its.csu.edu.cn/jsxsd/framework/xsMain.jsp':
            return True, 'identifying success'

        # 出现红色提示窗口
        prompt = driver.find_elements_by_css_selector("font[color='red']")
        if len(prompt) > 0:
            # 出现密码错误的提示
            if prompt[0].text == '该帐号不存在或密码错误,请联系管理员!':
                return False, 'password wrong'

            # 离奇抽风时会刷新网页，需要重新输入用户名和密码
            if prompt[0] == '用户名或密码为空!':
                name_input = driver.find_element_by_id("userAccount")  # 找到用户名的框框
                pass_input = driver.find_element_by_id('userPassword')  # 找到输入密码的框框
                name_input.clear()
                name_input.send_keys(username)  # 填写用户名
                time.sleep(0.2)
                pass_input.clear()
                pass_input.send_keys(password)  # 填写密码

            # 还有可能弹出验证码无效等等错误提示
            logger.warning('arise other prompt,prompt is : ' + str(prompt[0].text))

        # 出现alert text弹窗
        try:
            alert = driver.switch_to.alert
            alert.accept()
            logger.warning('arise alert,alert text is' + alert.text)
        except:
            pass

        identifying_time = identifying_time + 1

    # 验证码识别多次后仍然失败
    logger.warning('identifying code mistakes too much times')
    return False, 'identifying code mistakes too much times'


def handle_browser_register_request(request_id: str, username: str, password: str):
    """
    处理redis队列中的通过浏览器验证的请求

    """
    print('调用handlerbrowse')
    if check_if_have_registered(username):
        redis_client.set("auth:request_status:%s" % request_id, 'student has registered', nx=True, ex=86400)
        logger.info('student_id:%s identify fail becacuse id has registered' % username)
        return False, 'student has registered'

    # 判断该用户是否为中南大学学生
    # result数组第一个参数为bool类型判断验证是否成功，第二个参数为出错原因
    result = simulate_login(username, password)
    # 密码错误
    if not result[0]:
        redis_client.set("auth:request_status:%s" % request_id, 'password wrong', nx=True, ex=86400)
        logger.info('student_id:%s identify fail because password wrong' % username)
        return False, result[1]

    # 经判断是中南大学学生，生成token，并将相应数据持久化
    redis_client.set("auth:request_status:%s" % request_id, 'identify a student in csu', nx=True, ex=86400)  # 1 day
    logger.info('student_id:%s identify success' % username)
    insert_browser_account(request_id, username, 'browser')

    return True, 'identify a student in csu'


def handle_email_register_request(request_id: str, username: str):
    """
    处理redis队列中的通过邮箱验证的请求

    :param request_id: str, 请求 ID
    :param username: str, 学号
    """
    email = username + "@csu.edu.cn"
    token = str(uuid.uuid1())
    send_email(email, token)
    redis_client.set("auth:request_status" + request_id, 'sendEmail success', nx=True, ex=86400)
    request_info = "%s:%s" % (request_id, username)
    redis_client.set("auth:email_token:%s" % token, request_info, ex=86400)
    return True, 'sendEmail success'


def _format_address(email):
    """邮件地址的格式化"""
    name, address = parseaddr(email)
    return formataddr((Header(name, 'utf-8').encode(), address))


if __name__ == '__main__':
    send_email('919081500@qq.com', "123")
    send_email("3901160413@csu.edu.cn", '123')

