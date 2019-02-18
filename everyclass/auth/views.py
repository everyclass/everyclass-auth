from flask import Blueprint, jsonify, request

from everyclass.auth import logger
from everyclass.auth.db.mysql import check_if_request_id_exist, insert_email_account
from everyclass.auth.handle_register_queue import RedisQueue, redis_client
from everyclass.auth.messages import Message
from everyclass.auth.utils import json_payload

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


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
                    "username"  : username,
                    "password"  : password,
                    "method"    : "password"})

    logger.info('New request: %s wants to verify by password' % username)

    return jsonify({"acknowledged": True,
                    "message"     : Message.SUCCESS
                    })


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

    user_queue = RedisQueue('everyclass')
    user_queue.put({"request_id": request_id,
                    "username"  : username,
                    "method"    : "email"})

    logger.info('New request: %s wants to verify by email' % username)

    return jsonify({"acknowledged": True,
                    "message"     : Message.SUCCESS
                    })


@user_blueprint.route('/verify_email_token', methods=['GET'])
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
            'success': False,
            'message': Message.INVALID_EMAIL_TOKEN
        })

    # 通过user_inf_by_token取到的数据格式为request_id:username
    user_info = bytes.decode(user_info).split(':')
    request_id, username = user_info
    logger.info('Account:%s identifying success' % username)

    if not check_if_request_id_exist(request_id):
        insert_email_account(request_id, username, 'email', email_token)

    redis_client.set("auth:request_status:%s" % request_id, Message.IDENTIFYING_SUCCESS, ex=86400)  # valid for 1 day
    return jsonify({
        'success': True,
        'message': Message.SUCCESS
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
    # 通过redis取出的信息格式为 auth:request_status:message
    message = (redis_client.get("auth:request_status:" + request_id))
    logger.debug(message)

    if not message:
        logger.info('There is no message for %s' % request_id)
        return jsonify({
            'success': False,
            'message': Message.INVALID_REQUEST_ID
        })

    return jsonify({
        "success": True,  # todo 根据 message判断成功失败
        "message": message.decode()
    })
