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


# Linux、Mac定时任务
# vi定时任务用的编辑器 https://www.runoob.com/linux/linux-vim.html
# 定时任务协议 https://www.runoob.com/linux/linux-comm-crontab.html
# Windows 定时任务
# https://blog.csdn.net/u012849872/article/details/82719372


def out_log_file(logs: List):
    """输出日志文件"""
    file_name = "%s.log" % time.strftime(FILE_TIME_FORMAT)
    log_file = open("%s" % file_name, mode="wb")
    for log in logs:
        line = str(log + "\n").encode("utf-8")
        log_file.write(line)
    log_file.close()


def auto_remove_log(cache_day: int, logs: List):
    """自动移除过期日志文件"""
    curr_file = os.path.abspath(sys.argv[0])
    curr_dir = os.path.dirname(curr_file)
    now_time = datetime.datetime.now().timestamp()
    # 最大保存时间偏差
    diff = cache_day * 24 * 60 * 60
    files = []
    count = 0
    put_and_print(logs, ["diff:", diff, "now:", now_time])
    for file in os.listdir(curr_dir):
        if file.endswith(".log"):
            files.append(file)
            log_time_str = file.split(".log")[0]
            try:
                log_time = datetime.datetime.strptime(log_time_str, FILE_TIME_FORMAT).timestamp()
            except Exception as e:
                put_and_print(logs, ["Auto remove log failed", str(file), str(e)])
                continue
            put_and_print(logs, [str(file), "diff:", (now_time - log_time)])
            if (now_time - log_time) >= diff:
                os.remove(file)
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

    if setting["is_test"] == "1":
        email_config = EmailConfig(host=email["host"], port=int(email["port"]), email_address=email["user"],
                                   email_pass=email["password"], subject=mail["subject"], content=mail["content"],
                                   time_out=int(setting["timeout"]), interval=int(setting["interval"]),
                                   diff_time=int(setting["diff_time"]), is_del=is_del)
    else:
        delay_start(max_delay)
        email_config = EmailConfig(host=email["host"], port=int(email["port"]), email_address=email["user"],
                                   email_pass=email["password"], subject=mail["subject"], content=mail["content"],
                                   time_out=int(mail["timeout"]), interval=int(mail["interval"]),
                                   diff_time=int(mail["diff_time"]), is_del=is_del)
    try:
        glados_auto_sign_in.auto_sign_int(setting["browser"], glados_account=glados["user"], email_config=email_config,
                                          log_list=log_list, is_debug=is_debug)
    except Exception as e:
        put_and_print(log_list, [exception.SignInException(exception.ERR_CODE_UNKNOWN_EXCEPTION, "Other exception"), e])
    auto_remove_log(int(setting["log_validity_date"]), log_list)
    out_log_file(log_list)
