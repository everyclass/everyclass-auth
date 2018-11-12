import pymysql

# def get_cursor():
#     """
#     配置数据库，
#     打开数据库链接，
#     并且返回数据库的操作游标
#     :return:
#     """
#     config = {
#         'host': '127.0.0.1',
#         'port': 3306,  # MySQL默认端口
#         'user': 'root',  # mysql默认用户名
#         'password': 'root',
#         'db': 'everyclass_login',  # 数据库
#         'charset': 'utf8mb4',
#         'cursorclass': pymysql.cursors.DictCursor,
#     }
#     db = pymysql.connect(**config)
#     cursor = db.cursor()
#     return cursor


def check_if_have_registered(username):
    """检查指定用户名是否存在"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "SELECT identifying FROM account WHERE username=%s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    db.close()
    if result == 1:
        return True
    else:
        return False


def insert_email_account(request_id, username, method, token):
    """插入一个用户信息"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "INSERT INTO account(request_id, username, method, token) " \
          "VALUES(%d, \'%s\', \'%s\', \'%s\')" \
          % (int(request_id), username, method, token)
    print(sql)
    cursor.execute(sql)
    db.commit()
    db.close()


def insert_browser_account(request_id, username, method):
    """插入一个用户信息"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "INSERT INTO account(request_id, username, method, identifying) VALUES(%d, \'%s\', \'%s\')" \
          % (int(request_id), username, method)
    print(sql)
    cursor.execute(sql)
    db.commit()
    db.close()


def check_if_token_exist(token):
    """检查指定token是否存在"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "SELECT token FROM account WHERE token=%s"
    result = cursor.execute(sql, (token,))
    db.close()
    if result:
        return True
    else:
        return False


def check_if_token_pick(username, print_in_token):
    """判断token与username是否匹配"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "SELECT token FROM account WHERE username = %s"
    token_in_db = cursor.execute(sql, (username,))
    db.close()
    if token_in_db == print_in_token:
        return True
    else:
        return False


def update_password(username, password):
    """修改密码"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "UPDATE account SET password = %s WHERE username = %s"
    cursor.execute(sql, (password, username,))
    db.close()


def select_username_by_token(token):
    """通过token来查找对应的username"""
    db = pymysql.connect("localhost", "root", "root", "everyclass_login")
    cursor = db.cursor()
    sql = "SELECT username FROM account WHERE token = %s"
    cursor.execute(sql, (token,))
    db.close()







