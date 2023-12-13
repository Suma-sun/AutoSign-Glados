import time
from typing import List

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_format_time() -> str:
    return time.strftime(LOG_DATE_FORMAT)


def put_and_print(log_list: List, str_list: List):
    """打印及设置日志内容"""
    log_str = get_format_time() + "\t"
    for s in str_list:
        log_str += str(s) + " "
    log_list.append(log_str)
    print(log_str)
