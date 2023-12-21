import configparser
import datetime
import os
import random
import sys
import time
from typing import List

import exception
import glados_auto_sign_in
from get_email_code import EmailConfig
from log import put_and_print

# 日志文件名称格式化规则
FILE_TIME_FORMAT = "%Y-%m-%d_%H_%M_%S"


def out_log_file(logs: List):
    """输出日志文件"""
    file_name = "%s.log" % time.strftime(FILE_TIME_FORMAT)
    file_name = os.path.join(log_path, file_name)
    log_file = open(file_name, mode="wb")
    for log in logs:
        line = str(log + "\n").encode("utf-8")
        log_file.write(line)
    log_file.close()


def get_log_path(path: str):
    """获取log日志输出目录"""
    if len(path) != 0:
        _log_path = os.path.dirname(r"%s" % path)
        try:
            os.makedirs(_log_path)
        except Exception as e:
            put_and_print(log_list, ["Make log dir failed path[%s]" % path, e])
            _log_path = get_def_path()
    else:
        _log_path = get_def_path()
    if os.path.exists(_log_path) and os.path.isdir(_log_path):
        return _log_path
    else:
        os.makedirs(_log_path)
    return _log_path


def get_def_path():
    # 未配置使用当前目录
    curr_file = os.path.abspath(sys.argv[0])
    curr_dir = os.path.dirname(curr_file)
    return os.path.join(curr_dir, "Log")


def auto_remove_log(cache_day: int, logs: List):
    """自动移除过期日志文件"""

    now_time = datetime.datetime.now().timestamp()
    # 最大保存时间偏差
    diff = cache_day * 24 * 60 * 60
    files = []
    count = 0
    put_and_print(logs, ["diff:", diff, "now:", now_time])
    for log_file in os.listdir(log_path):
        if log_file.endswith(".log"):
            files.append(log_file)
            log_time_str = log_file.split(".log")[0]
            try:
                log_time = datetime.datetime.strptime(log_time_str, FILE_TIME_FORMAT).timestamp()
            except Exception as e:
                put_and_print(logs, ["Auto remove log failed", str(log_file), str(e)])
                continue
            if (now_time - log_time) >= diff:
                del_file = os.path.join(log_path, log_file)
                try:
                    os.remove(del_file)
                except Exception as e:
                    put_and_print(logs, ["Remove log failed", str(del_file), str(e)])
                    continue
                put_and_print(logs, [str(del_file), "diff:", (now_time - log_time)])
                count += 1
    put_and_print(logs, ["Auto remove log file:", count])


def delay_start(max_delay):
    if max_delay >= 1:
        delay = random.randrange(1, max_delay)
        if is_debug:
            put_and_print(log_list, ["Delay start:", delay])
        time.sleep(delay)
        if is_debug:
            put_and_print(log_list, ["Delay restart"])


def work():
    """执行自动登录及签到"""
    try:
        glados_auto_sign_in.auto_sign_int(setting["browser"], glados_account=glados["user"], email_config=email_config,
                                          log_list=log_list, is_debug=is_debug)
    except Exception as e:
        put_and_print(log_list, [exception.SignInException(exception.ERR_CODE_UNKNOWN_EXCEPTION, "Other exception"), e])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 日志信息，用于输出日志文件
    log_list = []
    put_and_print(log_list, ['Start auto sign in'])
    curr = os.path.abspath(sys.argv[0])
    curr = os.path.dirname(curr)
    file = os.path.join(curr, "config.ini")
    config = configparser.ConfigParser()
    config.read(file, "utf-8")

    email = dict(config.items("email"))
    mail = dict(config.items("mail"))
    glados = dict(config.items("glados"))
    setting = dict(config.items("setting"))
    is_debug = setting["is_debug"] == "1"
    is_del = mail["is_del_mail"] == "1"
    max_delay = int(setting["max_delay_start"])
    try:
        log_path = get_log_path(setting["log_path"])
    except Exception as e:
        print(e)

    if setting["is_test"] == "1":
        email_config = EmailConfig(host=email["host"], port=int(email["port"]), email_address=email["user"],
                                   email_pass=email["password"], subject=mail["subject"], content=mail["content"],
                                   time_out=int(setting["timeout"]), interval=int(setting["interval"]),
                                   diff_time=int(setting["diff_time"]), is_del=is_del)
    else:
        email_config = EmailConfig(host=email["host"], port=int(email["port"]), email_address=email["user"],
                                   email_pass=email["password"], subject=mail["subject"], content=mail["content"],
                                   time_out=int(mail["timeout"]), interval=int(mail["interval"]),
                                   diff_time=int(mail["diff_time"]), is_del=is_del)
    delay_start(max_delay)
    work()
    auto_remove_log(int(setting["log_validity_date"]), log_list)
    out_log_file(log_list)
