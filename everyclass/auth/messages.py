class Message:
    # 以下字段为返回请求时会使用的字段
    ERROR = "ERROR"  # 表示当前步骤出现了内部错误（如模拟登陆错误）
    PASSWORD_WRONG = "PASSWORD_WRONG"  # 密码错误
    REPEAT_REGISTRATION = "REPEAT_REGISTRATION "  # 该用户已注册
    INVALID_EMAIL_TOKEN = "INVALID_EMAIL_CODE"  # 用于邮箱验证的验证码无效
    INVALID_REQUEST_ID = "INVALID_REQUESTID"  # 请求中提供的requestID不存在或已过期
    SEND_EMAIL_SUCCESS = "SEND_EMAIL_SUCCESS"  # 发送邮件成功
    IDENTIFYING_SUCCESS = "IDENTIFYING_SUCCESS"  # 验证成功

    SUCCESS = "SUCCESS"  # 表示当前步骤成功
