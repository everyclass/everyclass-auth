class Message:
    # 以下字段为返回请求时会使用的字段
    IDENTIFYING_SUCCESS = "IDENTIFYING_SUCCESS"  # 验证成功
    SEND_EMAIL_SUCCESS = "SEND_EMAIL_SUCCESS"  # 发送邮件成功
    INVALID_REQUEST_ID = "INVALID_REQUEST_ID"  # 请求中提供的requestID不存在或已过期
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 表示当前步骤出现了内部错误（如模拟登陆错误）
    PASSWORD_WRONG = "PASSWORD_WRONG"  # 密码错误

    SUCCESS = "SUCCESS"  # 表示当前步骤成功
