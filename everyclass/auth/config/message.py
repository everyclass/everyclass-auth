class Message:
    SUCCESS = "SUCCESS"  # 表示当前步骤成功
    WRONG = "WRONG"  # 表示当前步骤用户输入错误（如密码错误）
    ERROR = "ERROR"  # 表示当前步骤出现了内部错误（如模拟登陆错误）

    IDENTIFYING_SUCCESS = "IDENTIFYING_SUCCESS"  # 验证成功
    PASSWORD_WRONG = "PASSWORD_WRONG"  # 密码错误
    IDENTIFYING_TOO_MUCH_TIMES = "IDENTIFYING_TOO_MUCH_TIMES"  # 验证循环次数过多
    ARISE_OTHER_PROMPT = "ARISE_OTHER_PROMPT"  # 出现了意料之外的其他提示语句
    PK_REUSE = "PK_REUSE"  # 主键重复
    REPEAT_REGISTRATION = "REPEAT_REGISTRATION "  # 该用户已注册
    SEND_EMAIL_SUCCESS = "SEND_EMAIL_SUCCESS"  # 发送邮件成功
    PUT_INTO_QUEUE = "PUT_INTO_QUEUE"  # 成功将请求插入处理队列
    INVALID_EMAIL_CODE = "INVALID_EMAIL_CODE"  # 用于邮箱验证的验证码无效



