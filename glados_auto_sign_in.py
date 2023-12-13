import datetime
import time
from typing import List

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common import by

import exception
import get_email_code as get_code
from get_email_code import EmailConfig
from log import put_and_print

base_url = "https://glados.space"
sign_url = base_url + "/console/checkin"
login_url = base_url + "/login"


def auto_sign_int(browser: str, glados_account: str, email_config: EmailConfig, log_list: List[str],
                  is_debug: bool) -> bool:
    """
    自动签到
    :param log_list: 日志列表
    :param browser 浏览器类型
    :param glados_account glados登录的账号
    :param email_config 获取邮箱验证码所需的配置信息
    :param is_debug 是否输出非必要日志
    :return: 成功与否
    """
    start_time = datetime.datetime.now().timestamp()
    # 浏览器驱动生成
    try:
        driver = create_browser_driver(browser, is_debug, log_list)
    except Exception as e:
        put_and_print(log_list,
                      [str(exception.SignInException(exception.ERR_CODE_WEB_DRIVER_CREATE_EXCEPTION, str(e)))])
        return False
    # 登录账号
    login_result = login_glados(driver, email_config, glados_account, log_list, is_debug)
    if login_result is False:
        driver.quit()
        return False
    # 登录完成，加载签到页
    driver.get(sign_url)
    # 签到
    check_in(driver, is_debug, log_list)
    # 打印信息
    print_user_info(driver, is_debug, log_list)
    run_time = datetime.datetime.now().timestamp() - start_time
    put_and_print(log_list, ["Auto sign in end， run time %d(s)" % int(run_time)])
    driver.quit()


def print_user_info(driver, is_debug, log_list):
    """打印当前账户信息，流量、有效期"""
    p_list = driver.find_elements(by.By.TAG_NAME, "p")
    is_find_p = False
    for p in p_list:
        if p.text.__contains__("Current plan is"):
            b = p.find_element(by.By.TAG_NAME, "b")
            if b is not None:
                put_and_print(log_list, [b.text])
            put_and_print(log_list, [p.text.split(",")[-1].lstrip()])
            is_find_p = True
            break
    if not is_find_p and is_debug:
        put_and_print(log_list, ["Not find new info"])


def check_in(driver, is_debug, log_list):
    for find_count in range(0, 5):
        # 循环尝试获取签到按钮
        try:
            buttons = driver.find_elements(by.By.TAG_NAME, "button")
        except Exception as e:
            time.sleep(5)
            if is_debug:
                put_and_print(log_list, ["Not find button by", driver.current_url, e])
            continue
        is_find_checkin = False
        for button in buttons:
            if button.text == "Checkin":
                is_find_checkin = True
                for i in range(0, 5):
                    # 尝试点击签到
                    click_result = click_element(button, driver, is_debug, log_list, "Click checkin failed")
                    if not click_result:
                        is_find_checkin = False
                        break
                    try:
                        tbody = driver.find_element(by.By.TAG_NAME, "tbody")
                        tr_list = tbody.find_elements(by.By.TAG_NAME, "tr")
                        if is_debug:
                            put_and_print(log_list, ["Row count", len(tr_list)])
                        if len(tr_list) > 0:
                            row = tr_list[0]
                            td_list = row.find_elements(by.By.TAG_NAME, "td")
                            if len(td_list) >= 4:
                                put_and_print(log_list, ["Info: points %s, change %s, date %s" % (
                                    td_list[0].text, td_list[1].text, td_list[3].text)])
                                break
                    except Exception as e:
                        is_find_checkin = False
                        put_and_print(log_list, [str(e)])
                        # 元素不存在，进行上层循环
                        break

        if is_find_checkin:
            break
        time.sleep(5)


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


def login_glados(driver, email_config, glados_account, log_list, is_debug) -> bool:
    """
    登录账号
    :param log_list: 日志列表
    :param driver: 浏览器
    :param email_config: 验证码邮箱配置
    :param glados_account: 网站账号
    :param is_debug: 是否输出非必要日志
    :return: 登录与否
    """
    driver.get(login_url)
    # 模拟输入
    input_email = driver.find_element(by.By.ID, "email")
    ActionChains(driver).move_to_element(input_email).pause(0.5).click(input_email).perform()
    input_email.send_keys(glados_account)
    if is_debug:
        put_and_print(log_list, ["Enter email address", glados_account])
    button_list = driver.find_elements(by.By.TAG_NAME, "button")
    send_code_button = None
    login_button = None
    for button in button_list:
        if button.text == "send access code to email":
            send_code_button = button
        else:
            login_button = button
    if send_code_button is None:
        put_and_print(log_list, [str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                                              "Not find send access code button"))])
        return False
    if login_button is None:
        put_and_print(log_list, [
            str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION, "Not find login button"))])
        return False
    if send_code_button is not None:
        # 该方法已压入失败exception
        send_result = send_code(driver, is_debug, send_code_button, log_list)
        if send_result is False:
            return False
    # 该方法已压入失败exception
    code = get_code.get_code_by_config(email_config, is_debug, log_list)
    if code == "":
        return False
    input_code = driver.find_element(by.By.ID, "mailcode")
    input_code.send_keys(code)
    if is_debug:
        put_and_print(log_list, ["Enter code", code])
    # 实例化,悬浮、点击，可以连续调用多个方法，是因为返回的都是self对象
    ActionChains(driver).move_to_element(login_button).pause(0.5).click(login_button).perform()

    for i in range(0, 10):
        if driver.current_url == login_url:
            # 地址未变按钮任然是登录的话尝试再次触发，点击成功会变更文案
            if login_button.text == "Login":
                if is_debug:
                    put_and_print(log_list, ["Wait login"])
                time.sleep(5)
                continue
            else:
                if is_debug:
                    put_and_print(log_list, [login_button.text])
                time.sleep(5)
                continue
        if driver.current_url == base_url:
            put_and_print(log_list, [
                str(exception.LoginException(exception.ERR_CODE_LOGIN_FAILED_EXCEPTION, "Curr url is %s" % base_url))])
            return False
        break
    if driver.current_url == base_url:
        put_and_print(log_list, [
            str(exception.LoginException(exception.ERR_CODE_LOGIN_FAILED_EXCEPTION, "Curr url is %s" % base_url))])
        return False
    else:
        return True


def send_code(driver, is_debug, send_code_button, log_list) -> bool:
    """执行发送验证码"""
    is_find_send = False
    # 点击发送验证码，获取提醒，如果未获取到提示，说明点击触发失败，再次尝试，总共尝试5次
    for i in range(0, 10):
        ActionChains(driver).move_to_element(send_code_button).pause(0.5).click(send_code_button).perform()
        if is_debug:
            put_and_print(log_list, ["Try find sent mess"])
        time.sleep(5)
        p_list = driver.find_elements(by.By.TAG_NAME, "p")
        for p in p_list:
            if p.text == "access code sent. please check mailbox":
                is_find_send = True
                break
        if is_find_send:
            break
    if is_find_send:
        if is_debug:
            put_and_print(log_list, ["Access code sent"])
        return True
    else:
        put_and_print(log_list, [
            str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION, "Not find access code sent"))])
        return False


def create_browser_driver(browser, is_debug, log_list):
    """
    创建浏览器驱动对象
    :param log_list: 日志列表
    :param browser: 浏览器类型
    :param is_debug: 是否调试模式
    :return:
    """
    if browser == "0":
        service = webdriver.SafariService()
        options = webdriver.SafariOptions()
        init_options(options)
        driver = webdriver.Safari(options=options, service=service)
        if is_debug:
            put_and_print(log_list, ["Create SafariService"])
    elif browser == "1":
        service = webdriver.ChromeService()
        options = webdriver.ChromeOptions()
        init_options(options)
        driver = webdriver.Chrome(options=options, service=service)
        if is_debug:
            put_and_print(log_list, ["Create ChromeService"])
    elif browser == "2":
        service = webdriver.FirefoxService()
        options = webdriver.FirefoxOptions()
        init_options(options)
        driver = webdriver.Firefox(options=options, service=service)
        if is_debug:
            put_and_print(log_list, ["Create FirefoxService"])
    elif browser == "3":
        service = webdriver.EdgeService()
        options = webdriver.EdgeOptions()
        init_options(options)
        driver = webdriver.Edge(options=options, service=service)
        if is_debug:
            put_and_print(log_list, ["Create EdgeService"])
    else:
        service = webdriver.IeService()
        options = webdriver.IeOptions()
        init_options(options)
        driver = webdriver.Ie(options=options, service=service)
        if is_debug:
            put_and_print(log_list, ["Create Ie"])
    # 隐式等待，查找元素直到找到或者浏览器超时才返回
    driver.implicitly_wait(60)
    return driver


def init_options(options):
    """
    初始化浏览器设置
    :param options:
    :return:
    """
    # 保持浏览器打开
    # options.add_experimental_option("detach", True)
    # 等待所有资源加载完毕才算加载完成
    options.page_load_strategy = "normal"
    # 把Chrome浏览器设置为静默模式
    options.add_argument('--headless')


def test_get_code(email_config: EmailConfig):
    """
    测试获取验证码
    :return:
    """
    logs = []
    get_code.get_code_by_config(email_config, True, logs)
