from flask import Blueprint, jsonify, request

from auth.handle_register_queue import RedisQueue, redis_client
from everyclass.auth import logger
from everyclass.auth.db.mysql import check_if_request_id_exist, insert_email_account
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
    user_information = {"request_id": request_id, "username": username, "password": password, "method": "password"}
    user_queue.put(user_information)

    logger.info('New request: %s wants to verify by password' % username)

    return jsonify({"acknowledged": True,
                    "message"     : 'Success putting request to handle queue'
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
    user_information = {"request_id": request_id, "username": username, "method": "email"}
    user_queue.put(user_information)

    logger.info('New request: %s wants to verify by email' % username)

    return jsonify({"acknowledged": True,
                    "message"     : 'Success putting request to handle queue'
                    })


@user_blueprint.route('/identifying_email_code', methods=['POST'])
@json_payload('email_code', supposed_type=str)
def identifying_email_code():
    """
        从用户输入的code判断，该用户是否有注册资格
        期望格式：
        {
            "email_code": "asdda451"
        }
    """
    email_code = request.json.get('email_code')

    if not email_code:
        return jsonify({
            'success': False,
            'message': 'no email_code in request'
        })
    user_inf_by_token = redis_client.get("auth:email_token:%s" % email_code)
    if not user_inf_by_token:
        logger.warning('no user for email_code %s' % email_code)
        return jsonify({
            'success': False,
            'message': 'no user for email_code'
        })
    # 通过的user_inf_by_token取到的数据格式为request_id:username
    logger.debug(user_inf_by_token)
    user_inf = bytes.decode(user_inf_by_token).split(':')
    request_id = user_inf[0]
    username = user_inf[1]
    logger.info('student_id:%s identifying success' % username)
    if not check_if_request_id_exist(request_id):
        insert_email_account(request_id, username, 'email', email_code)
    return jsonify({
        'success': True
    })


@user_blueprint.route('/get_identifying_result')
@json_payload('request_id', supposed_type=str)
def get_identifying_result():
    """
    根据requestid获取服务器验证的判断结果
    期望格式：
    {
        "request_id":"123"
    }
    """
    request_id = str(request.json.get('request_id'))
    if not request_id:
        return jsonify({
            'acknowledged': False,
            'message'     : "field `request_id` is empty"
        })
    # 通过redis取出的信息格式为auth:request_status:message
    message = (redis_client.get("auth:request_status:" + request_id))
    logger.debug(message)

    if not message:
        logger.info('There is no message for %s' % request_id)
        return jsonify({
            'acknowledged': True,
            "verified"    : False,
            'message'     : "request_id does not exist or expired"
        })

    return jsonify({
        "acknowledged": True,
        "verified"    : True,  # todo 根据 message判断成功失败
        "message"     : message.decode()
    })
