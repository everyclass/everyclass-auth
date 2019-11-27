from flask import Blueprint, jsonify, request

from everyclass.auth import logger
from everyclass.auth.consts import Message
from everyclass.auth.db.dao import check_if_request_id_exist, insert_email_account
from everyclass.auth.db.redis import redis_client
from everyclass.auth.message_queue import RedisQueue
from everyclass.auth.utils import json_payload

user_blueprint = Blueprint('user', __name__, url_prefix='/')


@user_blueprint.route('/register_by_password', methods=['POST'])
@json_payload('request_id', 'student_id', 'password', supposed_type=str)
def register_by_password():
    """
    通过教务系统的账户密码验证进行用户注册

    期望格式：
    {
        "request_id":"1",
        "student_id": "3901160413",
        "password": "",
    }
    """
    request_id = request.json.get('request_id')
    username = request.json.get('student_id')
    password = request.json.get('password')

    user_queue = RedisQueue('everyclass')
    user_queue.put({"request_id": request_id,
                    "username": username,
                    "password": password,
                    "method": "password"})
    redis_client.set("auth:request_status:" + request_id, Message.WAITING)
    logger.info('New request: %s wants to verify by password' % username)

    return jsonify({"acknowledged": True})


@user_blueprint.route('/register_by_email', methods=['POST'])
@json_payload('request_id', 'student_id', supposed_type=str)
def register_by_email():
    """
    通过学校邮箱验证的方式进行用户注册

    期望格式：
    {
        "request_id": "123"
        "student_id": "3901160413"
    }
    """

    request_id = request.json.get("request_id")
    student_id = request.json.get("student_id")
    username = student_id

    user_queue = RedisQueue("everyclass")
    user_queue.put({"request_id": request_id,
                    "username": username,
                    "method": "email"})

    redis_client.set("auth:request_status:" + request_id, Message.WAITING)

    logger.info('New request: %s wants to verify by email' % username)

    return jsonify({"acknowledged": True})


@user_blueprint.route('/verify_email_token', methods=['POST'])
@json_payload('email_token', supposed_type=str)
def verify_email_token():
    """
    从用户输入的code判断，该用户是否有注册资格
    期望格式：
    {
        "email_token": "123456"
    }
    """
    email_token = request.json.get('email_token')
    user_info = redis_client.get("auth:email_token:%s" % email_token)
    if not user_info:
        logger.info('No user information for email token %s' % email_token)
        return jsonify({
            'success': False
        })

    # 通过user_inf_by_token取到的数据格式为request_id:username
    user_info = bytes.decode(user_info).split(':')
    request_id, username = user_info
    logger.info('User %s email verification success' % username)

    if not check_if_request_id_exist(request_id):
        insert_email_account(request_id, username, email_token)

    redis_client.set("auth:request_status:%s" % request_id, Message.IDENTIFYING_SUCCESS, ex=86400)  # valid for 1 day
    return jsonify({
        'success'   : True,
        'request_id': request_id
    })


@user_blueprint.route('/get_result')
@json_payload('request_id', supposed_type=str)
def get_result():
    """
    根据 request_id 获取服务器验证结果
    期望格式：
    {
        "request_id":"123"
    }
    """
    request_id = str(request.json.get('request_id'))

    message = redis_client.get("auth:request_status:" + request_id)

    if not message:
        logger.info('Try to query status for a non-exist request_id: {}'.format(request_id))
        return jsonify({
            'success': False,
            'message': Message.INVALID_REQUEST_ID
        })

    message = message.decode()
    return jsonify({
        "success": True if message == Message.IDENTIFYING_SUCCESS else False,
        "message": message
    })
