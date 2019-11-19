import uuid

from everyclass.auth.db.postgres import conn_context


def check_if_have_registered(username: str) -> bool:
    """检查指定用户名是否存在"""
    with conn_context() as conn, conn.cursor() as cursor:
        select_query = "SELECT username FROM account WHERE username=%s"
        cursor.execute(select_query, (username,))
        result = cursor.fetchone()
    if result:
        return True
    return False


def insert_email_account(request_id: str, username: str, token: str) -> None:
    """插入一个用户信息"""
    with conn_context() as conn, conn.cursor() as cursor:
        insert_query = """
        INSERT INTO account (request_id, username, method, token) VALUES (%s,%s,%s,%s)
        """
        cursor.execute(insert_query, (uuid.UUID(request_id), username, "email", uuid.UUID(token)))
        conn.commit()


def insert_browser_account(request_id, username):
    """插入一个用户信息"""
    with conn_context() as conn, conn.cursor() as cursor:
        insert_query = """
        INSERT INTO account (request_id, username, method) VALUES (%s,%s,%s)
        """
        cursor.execute(insert_query, (uuid.UUID(request_id), username, "browser"))
        conn.commit()


def check_if_request_id_exist(request_id):
    """检查指定request_id是否存在"""
    with conn_context() as conn, conn.cursor() as cursor:
        select_query = "SELECT request_id FROM account WHERE request_id=%s"
        cursor.execute(select_query, (uuid.UUID(request_id),))
        result = cursor.fetchone()
    if result:
        return True
    return False
