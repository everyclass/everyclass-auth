import pymysql
from DBUtils.PooledDB import PooledDB
from flask import current_app as app


def init_pool(current_app):
    """创建连接池，保存在 app 的 mysql_pool 对象中"""

    # current_app.mysql_pool = PooledDB.ConnectionPool(**current_app.config.MYSQL_CONFIG)
    current_app.mysql_pool = PooledDB(creator=pymysql,
                                      mincached=1,
                                      maxcached=5,
                                      maxconnections=100,
                                      host=current_app.config['MYSQL_CONFIG']['host'],
                                      user=current_app.config['MYSQL_CONFIG']['user'],
                                      passwd=current_app.config['MYSQL_CONFIG']['password'],
                                      db=current_app.config['MYSQL_CONFIG']['db'],
                                      port=current_app.config['MYSQL_CONFIG']['port'],
                                      charset=current_app.config['MYSQL_CONFIG']['charset'])
    print(current_app)
    print(current_app.mysql_pool)


def get_connection():
    """在连接池中获得连接"""
    return app.mysql_pool.connection()

    # return pymysql.Connection(**config.MYSQL_CONFIG)


def check_if_have_registered(username):
    """检查指定用户名是否存在"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT username FROM account WHERE username=%s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    if result == 1:
        return True
    else:
        return False


def insert_email_account(request_id, username, method, token):
    """插入一个用户信息"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO account(request_id, username, method, token) " \
          "VALUES( \'%s\', \'%s\', \'%s\', \'%s\')" \
          % (int(request_id), username, method, token)
    cursor.execute(sql)
    if cursor:
        cursor.close()
    if connection:
        connection.close()


def insert_browser_account(request_id, username, method):
    """插入一个用户信息"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO account(request_id, username, method) VALUES( \'%s\', \'%s\', \'%s\')" \
          % (request_id, username, method)
    cursor.execute(sql)
    connection.commit()
    count = cursor.rowcount
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    return count


def check_if_token_exist(token):
    """检查指定token是否存在"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT token FROM account WHERE token=%s"
    result = cursor.execute(sql, (token,))
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    if result:
        return True
    else:
        return False


def check_if_token_pick(username, print_in_token):
    """判断token与username是否匹配"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT token FROM account WHERE username = %s"
    token_in_db = cursor.execute(sql, (username,))
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    if token_in_db == print_in_token:
        return True
    else:
        return False


def update_password(username, password):
    """修改密码"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "UPDATE account SET password = %s WHERE username = %s"
    cursor.execute(sql, (password, username,))
    if cursor:
        cursor.close()
    if connection:
        connection.close()


def select_username_by_token(token):
    """通过token来查找对应的username"""
    connection = get_connection()
    cursor = connection.cursor()
    sql = "SELECT username FROM account WHERE token = %s"
    cursor.execute(sql, (token,))
    result = cursor.fetchone()
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    return result


if __name__ == '__main__':
    print(select_username_by_token('123'))



