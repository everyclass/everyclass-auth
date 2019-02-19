from everyclass.auth.db.mongodb import get_connection


def check_if_have_registered(username):
    """检查指定用户名是否存在"""
    db = get_connection()
    result = db.account.find_one({"username": username})
    if result:
        return True
    return False


def insert_email_account(request_id, username, method, token):
    """插入一个用户信息"""
    db = get_connection()
    db.account.insert({"request_id": request_id,
                       "username"  : username,
                       "method"    : method,
                       "token"     : token
                       })


def insert_browser_account(request_id, username, method):
    """插入一个用户信息"""
    db = get_connection()
    db.account.insert({"request_id": request_id,
                       "username"  : username,
                       "method"    : method
                       })


def check_if_request_id_exist(request_id):
    """检查指定request_id是否存在"""
    db = get_connection()
    result = db.account.find_one({"request_id": request_id})
    if result:
        return True
    return False
