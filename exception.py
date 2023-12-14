
ERR_CODE_WEB_DRIVER_CREATE_EXCEPTION = 100001
"""错误类型：浏览器驱动生成异常"""
ERR_CODE_DATE_TIME_CONVERT_EXCEPTION = 100101
"""错误类型：邮箱邮件日期转换异常"""
ERR_CODE_NOT_FIND_ACCESS_CODE_EXCEPTION = 100102
"""错误类型：未找到邮件登录验证码"""
ERR_CODE_REMOVE_MAIL_EXCEPTION = 100103
"""错误类型：删除邮件失败"""
ERR_CODE_LOGIN_FAILED_EXCEPTION = 100201
"""错误类型：登录失败异常"""
ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION = 100301
"""错误类型：未找到指定元素异常"""
ERR_CODE_UNKNOWN_EXCEPTION = 100400
"""错误类型：未知异常"""


class LoginException(Exception):
    """登录失败异常"""

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f"[Login Failed Exception] {self.code}: {self.message}"


class GetCodeException(Exception):
    """获取登录验证码失败异常"""

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f"[Get Asses Code Failed Exception] {self.code}: {self.message}"


class SignInException(Exception):
    """签到失败异常"""

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f"[Sign in Failed Exception] {self.code}: {self.message}"
