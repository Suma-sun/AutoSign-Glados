import poplib
import time
from datetime import datetime
import pytz
from tzlocal import get_localzone

from email.parser import BytesParser
import email.header as eparser
import re
import exception
from log import put_and_print


class EmailConfig:
    """
    邮箱配置
    """
    __port: int
    __host: str
    __email_address: str
    __email_pass: str
    __subject: str
    __content_match_text: str
    __time_out: int
    __interval: int
    __diff_time: int
    __is_del: bool

    def __init__(self, host: str, port: int, email_address: str, email_pass: str, subject: str, content: str,
                 time_out: int, interval: int, diff_time: int, is_del: bool):
        """

        :param port: 邮箱地址端口号
        :param host: 邮箱地址
        :param email_address: 邮箱账号
        :param email_pass: 邮箱密码（授权码）
        :param subject: 标题
        :param content: 包含的内容
        :param time_out: 超时时间（s）
        :param interval: 扫描间隔时间
        :param diff_time: 邮件与脚本之间最大间隔时间（s）
        :param is_del: 是否需要删除邮件
        """
        self.__port = port
        self.__host = host
        self.__email_address = email_address
        self.__email_pass = email_pass
        self.__subject = subject
        self.__content_match_text = content
        self.__time_out = time_out
        self.__interval = interval
        self.__diff_time = diff_time
        self.__is_del = is_del

    def host(self) -> str:
        """
        邮箱地址
        :return:
        """
        return self.__host

    def port(self) -> int:
        """
        端口号
        :return:
        """
        return self.__port

    def address(self) -> str:
        """
        邮箱地址
        :return:
        """
        return self.__email_address

    def password(self) -> str:
        """
        邮箱登录密码（授权码）
        :return:
        """
        return self.__email_pass

    def subject(self) -> str:
        """
        主题匹配的文本（包含）
        :return:
        """
        return self.__subject

    def match_content(self) -> str:
        """
        内容匹配的文本（包含）
        :return:
        """
        return self.__content_match_text

    def time_out(self) -> int:
        """
        超时时间（s）
        :return:
        """
        return self.__time_out

    def interval(self) -> int:
        """
        扫描间隔时间（s）
        :return:
        """
        return self.__interval

    def diff_time(self) -> int:
        """
        邮件与脚本间隔的时间
        :return:
        """
        return self.__diff_time

    def is_del(self) -> bool:
        """是否需要删除邮件"""
        return self.__is_del


def get_code_by_config(config: EmailConfig, is_debug: bool, log_list) -> str:
    """根据配置，连接pop3邮箱服务，获取匹配的首个验证码"""
    # 连接到POP3服务器
    pop_server = poplib.POP3_SSL(config.host(), config.port())
    pop_server.user(config.address())
    pop_server.pass_(config.password())
    # start_time = time.time()
    start_time = datetime.now().timestamp()
    put_and_print(log_list, ["Get code start time", str(datetime.now().strftime("%d %b %Y %H:%M:%S %z"))])

    while datetime.now().timestamp() - start_time < config.time_out():
        # 间隔扫描，避免频繁
        time.sleep(config.interval())
        code = __get_code(pop_server, config, start_time, is_debug, log_list)
        if code is not None:
            put_and_print(log_list, ["Stop by find code %s" % code])
            # 关闭连接
            pop_server.quit()
            return code

    # 关闭连接
    pop_server.quit()
    put_and_print(log_list,
                  [str(exception.GetCodeException(exception.ERR_CODE_NOT_FIND_ACCESS_CODE_EXCEPTION,
                                                  "Not find access code by time out %ds" % config.time_out()))])
    return ""


def __get_code(pop_server: poplib, config: EmailConfig, start_time: float, is_debug: bool, log_list):
    """
    获取验证码
    :param pop_server: pop服务
    :param config: 配置信息
    :param start_time: 开始时间
    :param is_debug: 是否开启debug
    :return: code or None
    """
    # stat() 返回邮件数量和占用空间
    put_and_print(log_list, ['Mail count:%s  Temporary space:%s' % pop_server.stat()])
    # list() 返回所有邮件的编号，lines 存储了邮件的原始文本的每一行
    # resp, mails, octets = pop_server.list()
    # 获取邮箱中的邮件数量
    emails_len = len(pop_server.list()[1])
    if emails_len == 0:
        if is_debug:
            put_and_print(log_list, ["Mail is Empty"])
        return None
    last = 0
    # 反向遍历，从最新的邮件开始，步进-1
    for i in range(emails_len, last, -1):
        try:
            # 获取邮件内容
            response, lines, octets = pop_server.retr(i)
        except Exception as e:
            put_and_print(log_list, [str(e)])
            continue
        email_content = b'\r\n'.join(lines)
        # 解析邮件内容
        email_parser = BytesParser()
        email = email_parser.parsebytes(email_content)
        # 解析邮件头部信息
        email_from = email.get('From').strip()
        email_from = str(eparser.make_header(eparser.decode_header(email_from)))
        # 解析邮件主题
        subject = str(email.get('Subject').strip())

        # 只处理主题与内容匹配的文件
        if not subject.__contains__(config.subject()):
            if is_debug:
                put_and_print(log_list, ["Mail subject unmatch", subject])
            continue
        decoded_subject = str(eparser.make_header(eparser.decode_header(subject))) if subject else None
        email_body = str(get_html_payload(email))
        if not email_body.__contains__(config.match_content()):
            if is_debug:
                put_and_print(log_list, ["Mail context unmatch", email_body])
            continue
        # 邮件时间, 里面已经输出日志
        email_time = get_time(email, is_debug, log_list)
        if email_time == 0:
            continue
        diff = (start_time - email_time).__abs__()
        if is_debug:
            put_and_print(log_list, ["Diff time(s) =", diff])
        # 控制邮件时间
        if diff > config.diff_time():
            put_and_print(log_list, ["Filter by diff", diff, email_body])
            continue
        if is_debug:
            put_and_print(log_list, ["--------Mail start"])
            put_and_print(log_list, ["From:", email_from])
            put_and_print(log_list, ["Subject:", decoded_subject])
            put_and_print(log_list, ["Body:", email_body])
            put_and_print(log_list, ["--------Mail end"])

        content = email_body.split(config.match_content())[-1]
        content = content.split(config.address())[-1]
        # *182514*
        # result = re.search("\\*\\d{6}\\*", str(email_body))
        # result_code = result.group().replace("*", "")
        result = re.search("\\*\\d{5,6}\\*", content)
        if result is None:
            result = re.search("\\d{4,6}", content)
            if result is None:
                put_and_print(log_list,
                              [exception.GetCodeException(exception.ERR_CODE_NOT_FIND_ACCESS_CODE_EXCEPTION,
                             "No verification code found"), content])
                return False
        result_code = result.group()
        if result_code.__contains__("*"):
            result_code = result_code.replace("*", "")
        put_and_print(log_list, ["Match: code ", result_code])
        if is_debug:
            put_and_print(log_list, ["Is del mail", config.is_del()])
        if config.is_del():
            try:
                pop_server.dele(i)
                if is_debug:
                    put_and_print(log_list, ["Del mail"])
            except Exception as e:
                put_and_print(log_list,
                              [exception.GetCodeException(exception.ERR_CODE_REMOVE_MAIL_EXCEPTION, "Delete mail fail"),
                               e])
        return result_code
    return None


def get_html_payload(email_message):
    if email_message.is_multipart():
        return get_html_payload(email_message.get_payload(0))
    else:
        return email_message.get_payload(None, decode=True)


def get_time(email, is_debug: bool, log_list) -> float:
    """
    获取邮件时间
    :param log_list:
    :param is_debug:
    :param email:
    :return: time float or 0
    """

    # 'Tue, 16 Mar 2021 10:01:44 +0800'
    # Wed, 22 Nov 2023 08:19:38 +0000 (UTC)
    date_str = email.get('Date').strip()
    if is_debug:
        put_and_print(log_list, ["Mail time", date_str])

    email_date = str(date_str.split(",")[-1].lstrip())  # -1倒序索引
    if is_debug:
        put_and_print(log_list, ["Mail time format", email_date])
    if email_date.__contains__("("):
        email_date = email_date[0:email_date.index("(")].rstrip()
    if is_debug:
        put_and_print(log_list, ["Mail time format 2", email_date])
    # 22 Nov 2023 03:20:23 +0000

    try:
        utc_time = datetime.strptime(email_date, "%d %b %Y %H:%M:%S %z")
        if is_debug:
            put_and_print(log_list, ["Utc_time:", utc_time])

        local_tz = get_localzone()
        utc_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        if is_debug:
            put_and_print(log_list, ["Local_time:", utc_time])
        return utc_time.timestamp()

    except Exception as e:
        e2 = exception.GetCodeException(exception.ERR_CODE_DATE_TIME_CONVERT_EXCEPTION,
                                        "Format mail time err [%s]\terr[%s]" % (date_str, str(e)))
        put_and_print(log_list, [str(e2)])
        return 0
