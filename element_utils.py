from typing import List

from selenium.webdriver import ActionChains

import exception
from log import put_and_print


def safe_find_elements(driver, type, content: str, log_list: List[str], module_name: str):
    """安全的获取界面中的元素，可能返回None"""
    try:
        target = driver.find_elements(type, content)
        return target
    except Exception as e:
        put_and_print(log_list, [
            exception.FindElementException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                           "%s ,Not find target elements %s" % (module_name, content)), e])
        return None


def safe_find_element(driver, type, content: str, log_list: List[str], module_name: str):
    """安全的获取界面中的元素，可能返回None"""
    try:
        target = driver.find_element(type, content)
        return target
    except Exception as e:
        put_and_print(log_list, [exception.FindElementException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                                                "%s ,Not find target element %s" % (
                                                                module_name, content)), e])


def click_element(button, driver, is_debug, log_list, err_msg) -> bool:
    """
    点击指定元素
    @:return 点击是否成功
    """
    try:
        ActionChains(driver).move_to_element(button).pause(0.5).click(button).perform()
        if is_debug:
            put_and_print(log_list, ["Click", button.text])
        return True
    except Exception as e:
        put_and_print(log_list, [err_msg, str(e)])
        return False