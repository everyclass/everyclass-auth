#!/usr/bin/python
# -*- coding: UTF-8 -*-
import functools
from flask import abort, request
from email.mime.text import MIMEText
from email.header import Header
import smtplib
import time
from pytesseract import pytesseract
from selenium import webdriver
from PIL import Image
from everyclass.auth.db.mysql import *
import uuid

from auth.redisdb import redis_client


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


# 给指定账号发送含有指定token的邮件
def send_email(email, token):
    # 第三方 SMTP 服务
    mail_host = "smtp.qq.com"  # 设置服务器
    mail_user = "919081500@qq.com"  # 用户名
    mail_pass = "gotceisdgsvxbcdg"  # 口令

    sender = '919081500@qq.com'
    receivers = email
    message = MIMEText(token, 'html', 'utf-8')
    message['From'] = Header("csuEveryClass", 'utf-8')
    message['To'] = Header("user", 'utf-8')
    subject = 'csu每课邮箱验证'
    message['Subject'] = Header(subject, 'utf-8')

    smtpObj = smtplib.SMTP()
    smtpObj.connect(mail_host, 587)  # SMTP 端口号,465不行

    smtpObj.ehlo()
    smtpObj.starttls()

    smtpObj.login(mail_user, mail_pass)
    smtpObj.sendmail(sender, receivers, message.as_string())
    smtpObj.quit()


# 浏览器模拟登陆
def simulate_login(username, password):
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
        driver.save_screenshot("G:/test/01.png")  # 截取屏幕内容，保存到本地
        # 打开截图，获取验证码位置，截取保存验证码
        img1 = Image.open("G:/test/01.png")
        identifying_pic = img1.crop(box)
        identifying_pic.save("G:/test/02.png")
        # 获取验证码图片，读取验证码
        identifying_code = pytesseract.image_to_string(identifying_pic)
        print(identifying_code)
        identifying_input.send_keys(identifying_code)
        login_button.click()  # 点击登录

        # 若验证码判断正确，即不出现验证码错误的提示，就会找不到提示元素，返回true
        driver.refresh()
        if driver.current_url == 'http://csujwc.its.csu.edu.cn/jsxsd/framework/xsMain.jsp':
            return True, 'identifying success'

        prompt = driver.find_element_by_css_selector("font[color='red']")
        # 出现密码错误的提示
        if '该帐号不存在或密码错误,请联系管理员!' == prompt.text:
            return False, 'password wrong'
        identifying_time = identifying_time + 1
    # 验证码识别多次后仍然失败
    return False, 'identifying too much'


# 处理redis队列中的通过浏览器验证的请求
def handle_browser_register_request(request_id, username, password):
    if check_if_have_registered(username):
        redis_client.set(request_id, 'student has registered', nx=True, ex=86400)
        return False, 'student has registered'

    # 判断该用户是否为中南大学学生
    # result数组第一个参数为bool类型判断验证是否成功，第二个参数为出错原因
    result = simulate_login(username, password)
    # 密码错误
    if not result[0]:
        redis_client.set(request_id, 'password wrong', nx=True, ex=86400)
        return False, result[1]

    # 经判断是中南大学学生，生成token，并将相应数据持久化
    redis_client.set(request_id, 'identify a student in csu', nx=True, ex=86400)  # 1 day
    insert_browser_account(request_id, username, 'browser')
    return True, 'identify a student in csu'


# 处理redis队列中的通过邮箱验证的请求
def handle_email_register_request(request_id, username):
    email = str(username) + "@csu.edu.cn"
    token = str(uuid.uuid1())
    send_email(email, token)
    redis_client.set(request_id, 'sendEmail success', nx=True, ex=86400)
    user_inf = str(request_id) + ':' + str(username)
    redis_client.set(token, user_inf, nx=True, ex=86400)
    return True, 'sendEmail success'




