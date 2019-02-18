class Message:
    # 以下字段为返回请求时会使用的字段
    SUCCESS = "SUCCESS"  # 表示当前步骤成功
    ERROR = "ERROR"  # 表示当前步骤出现了内部错误（如模拟登陆错误）
    PASSWORD_WRONG = "PASSWORD_WRONG"  # 密码错误
    REPEAT_REGISTRATION = "REPEAT_REGISTRATION "  # 该用户已注册
    INVALID_EMAIL_TOKEN = "INVALID_EMAIL_CODE"  # 用于邮箱验证的验证码无效
    INVALID_REQUEST_ID = "INVALID_REQUESTID"  # 请求中提供的requestID不存在或已过期

    # 以下字段用于描述各个账户的不同状态
    IDENTIFYING_SUCCESS = "IDENTIFYING_SUCCESS"  # 验证成功
    IDENTIFYING_TOO_MUCH_TIMES = "IDENTIFYING_TOO_MUCH_TIMES"  # 验证循环次数过多
    ARISE_OTHER_PROMPT = "ARISE_OTHER_PROMPT"  # 出现了意料之外的其他提示语句
    PK_REUSE = "PK_REUSE"  # 主键重复
    SEND_EMAIL_SUCCESS = "SEND_EMAIL_SUCCESS"  # 发送邮件成功
    PUT_INTO_QUEUE = "PUT_INTO_QUEUE"  # 成功将请求插入处理队列
