from flask import Blueprint, jsonify, request
from everyclass.auth.db.mysql import *
from everyclass.auth.utils import json_payload
from auth.handle_register_queue import redis_client, RedisQueue

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
    user_information = {"request_id": request_id, "username": username, "method": "email"}
    user_queue.put(user_information)

    return jsonify({
        "success": True,
        "message": 'request in handle queue success'
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

    # if user_sum < 50:
    #
    # else:
    #     return jsonify({
    #         'success': False,
    #         'message': 'request too much'
    #     })

    return jsonify({
        "success": True,
        "message": 'request in handle queue success'
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
            'message': 'no token in request'
        })
    token = email_code
    print(redis_client.get(token))
    # 取到的token格式为auth:email_token:request_id:username
    user_inf = bytes.decode(redis_client.get(token)).split(':')
    request_id = user_inf[2]
    username = user_inf[3]
    if not request_id:
        return jsonify({
            'success': False,
            'message': 'no token in db'
        })
    else:
        insert_email_account(request_id, username, 'email', token)
        return jsonify({
            'success': True
        })


@user_blueprint.route('/login', methods=['POST'])
@json_payload('username', 'password', supposed_type=str)
def login():
    """
        登陆

        期望格式：
        {
            "username":"username",
            "password":"password"
        }
    """
    username = request.json.get('username')
    password = request.json.get('password')

    return jsonify({'success': True})


@user_blueprint.route('/get_identifying_result', methods=['POST'])
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
    print(request_id)
    print(type(request_id))
    # 通过redis取出的信息格式为auth:request_state:message
    print(redis_client.get(request_id))
    message = (redis_client.get(request_id)).split(':')[2]
    return message





