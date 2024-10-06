import datetime
import time
from typing import List

from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.remote import webelement

import exception
import get_email_code as get_code
from element_utils import safe_find_elements, click_element, safe_find_element
from get_email_code import EmailConfig
from log import put_and_print

base_url = "https://glados.space"
console_url = base_url + "/console"
sign_url = console_url + "/checkin"
login_url = base_url + "/login"
module_name = "Sign in"
plan_prefix = "Current plan"
flow_balance_prefix = "Traffic comsumption"


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
    if is_debug:
        put_and_print(log_list,["Before create browser driver"])
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
        put_and_print(log_list,["Login Failed"])
        return False
    driver.get(console_url)
    if driver.current_url != console_url:
        put_and_print(log_list, [str(exception.LoginException(exception.ERR_CODE_LOGIN_FAILED_EXCEPTION,
                                                              "Unable to load %s" % console_url))])
        return False
    if is_debug:
        put_and_print(log_list,["Login success"])
    # 输出控制台首页的当前用户信息（有效期及流量）
    print_current_info(driver, email_config.address(), log_list,is_debug)

    # 登录完成，加载签到页
    driver.get(sign_url)
    # 签到
    result = check_in(driver, is_debug, log_list)
    # 打印信息
    print_user_info(driver, is_debug, log_list)
    run_time = datetime.datetime.now().timestamp() - start_time
    put_and_print(log_list, ["Auto sign in end， run time %d(s)" % int(run_time)])
    driver.quit()
    return result


def print_current_info(driver, address, log_list, is_debug):
    """输出控制台页当前的信息（套餐、流量）"""
    for i in range(10):
        div_list = safe_find_elements(driver, by.By.TAG_NAME, "div", log_list, module_name)
        if div_list is None:
            if is_debug:
                put_and_print(log_list,["Not find Plan info by not find div_list"])
            return
        for div in div_list:
            txt = str(div.text)
            if txt.__contains__(address):
                lines = txt.split("\n")
                print_count = 0
                for line in lines:
                    if line == address:
                        print_count = 2
                        put_and_print(log_list, [line])
                        continue
                    if print_count > 0:
                        put_and_print(log_list, [line])
                        print_count -= 1
                        if print_count == 0:
                            return
        time.sleep(1)
    if is_debug:
        put_and_print(log_list, ["Not find Plan info by not find target text"])



def print_user_info(driver, is_debug, log_list):
    """打印签到后的当前账户的套餐，有效期"""
    for i in range(10):
        div_list = safe_find_elements(driver, by.By.TAG_NAME, "div", log_list, module_name)
        if div_list is None:
            if is_debug:
                put_and_print(log_list,["Not find new info by not find div_list"])
            return
        for div in div_list:
            txt = str(div.text)
            if txt.__contains__(plan_prefix):
                lines = txt.split("\n")
                for line in lines:
                    if line.startswith(plan_prefix):
                        put_and_print(log_list,[line])
                        return
        time.sleep(1)
    if is_debug:
        put_and_print(log_list, ["Not find new info by not find target text"])



def check_in(driver, is_debug, log_list) -> bool:
    """执行签到，返回签到结果"""
    click_result = False
    for find_count in range(0, 5):
        # 循环尝试获取签到按钮
        buttons = safe_find_elements(driver,by.By.TAG_NAME, "button",log_list,module_name)
        if buttons is None:
            time.sleep(3)
            continue
        is_find_checkin = False
        is_collect_info = False
        for button in buttons:
            if is_collect_info:
                break
            if button.text == "Checkin" or button.text == "签到":
                is_find_checkin = True
                for i in range(0, 5):
                    if is_collect_info:
                        break
                    # 尝试点击签到
                    click_result = click_element(button, driver, is_debug, log_list, "Click checkin failed")
                    if not click_result:
                        is_find_checkin = False
                        break
                    try:
                        t_body = safe_find_element(driver, by.By.TAG_NAME, "tbody", log_list, module_name)
                        tr_list = safe_find_elements(t_body,by.By.TAG_NAME, "tr",log_list,module_name)
                        if is_debug:
                            put_and_print(log_list, ["Row count", len(tr_list)])
                        is_collect_info = True
                        if len(tr_list) > 0:
                            today = time.strftime("%Y-%m-%d")
                            for row in tr_list:
                                td_list = safe_find_elements(row,by.By.TAG_NAME, "td",log_list,module_name)
                                if td_list is not None and len(td_list) >= 4:
                                    if str(td_list[3].text).__contains__(today):
                                        put_and_print(log_list, [get_checkin_info_str(td_list)])
                                        continue
                                    break
                                else:
                                    # 表格异常
                                    put_and_print(log_list, ["Unmatched table", row])
                                    break

                    except Exception as e:
                        is_find_checkin = False
                        put_and_print(log_list, [str(e)])
                        # 元素不存在，进行上层循环
                        break

        if is_find_checkin:
            break
        time.sleep(5)
    return click_result


def get_checkin_info_str(row):
    """获取签到信息表格内容"""
    return "Info: points %s, change %s, date %s" % (
        row[0].text, row[1].text, row[3].text)


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
    if is_debug:
        put_and_print(log_list,["Web load login url"])
    driver.get(login_url)
    # 模拟输入
    input_email = safe_find_element(driver,by.By.ID, "email",log_list,module_name)
    if input_email is None:
        return False
    click_element(input_email,driver,is_debug,log_list,"Click email failed")
    input_email.send_keys(glados_account)
    if is_debug:
        put_and_print(log_list, ["Enter email address", glados_account])
    button_list = safe_find_elements(driver,by.By.TAG_NAME, "button",log_list,module_name)
    if button_list is None:
        put_and_print(log_list, [str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                                              "Not find button list"))])
        return False
    send_code_button = None
    login_button = None
    for button in button_list:
        if button.text == "send access code to email":
            send_code_button = button
        elif button.text == "Login":
            login_button = button
    if send_code_button is None:
        put_and_print(log_list, [str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                                              "Not find send access code button"))])
        return False
    if login_button is None:
        put_and_print(log_list, [str(exception.LoginException(exception.ERR_CODE_NOT_FIND_ELEMENT_EXCEPTION,
                                                              "Not find Login button"))])
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
    input_code = safe_find_element(driver,by.By.ID, "mailcode",log_list,module_name)
    if input_code is None:
        put_and_print(log_list,["find input access code element failed "])
        return False
    input_code.send_keys(code)
    if is_debug:
        put_and_print(log_list, ["Enter code", code])
    time.sleep(2)
    #找登录的按钮元素
    login_span = safe_find_element(login_button,by.By.XPATH, "./..",log_list,module_name)
    if login_span is None:
        put_and_print(log_list,["Not find login span"])
        return False

    click_result = click_element(login_span,driver,is_debug,log_list,"Click login span failed")
    if not click_result:
        return False

    for i in range(0, 10):
        if driver.current_url == console_url:
            #已经进入控制台页面，可以继续后续流程
            return True
        elif driver.current_url == login_url:
            #地址未变还在登录页的话，判断按钮还是Login就重新触发
            if login_button.text == "Login":
                if i == 5:
                    # 地址未变按钮任然是登录的话尝试再次触发，点击成功会变更文案
                    click_element(login_span,driver,is_debug,log_list,"Click again login span failed")
                    if is_debug:
                        put_and_print(log_list, ["Try again click login"])
                else:
                    if is_debug:
                        put_and_print(log_list, ["Wait login"])
                time.sleep(3)
                continue
            else:
                if is_debug:
                    put_and_print(log_list, [login_button.text])
                time.sleep(3)
                continue
        elif driver.current_url == base_url:
            put_and_print(log_list, [
                str(exception.LoginException(exception.ERR_CODE_LOGIN_FAILED_EXCEPTION, "Curr url is %s" % base_url))])
            return False
        else:
            put_and_print(log_list,["Logging in, but not match url, curr url is %s" % driver.current_url])
            return False
    return False


def send_code(driver, is_debug, send_code_button, log_list) -> bool:
    """执行发送验证码"""
    is_find_send = False
    # 点击发送验证码，获取提醒，如果未获取到提示继续等待，当等待5次后说明点击触发接口调用失败，再次尝试点击
    click_element(send_code_button,driver,is_debug,log_list,"Click send code button failed")
    if is_debug:
        put_and_print(log_list, ["Click send access code"])
    for i in range(0, 10):
        if is_debug:
            put_and_print(log_list, ["Wait access code send"])
        time.sleep(3)
        p_list = safe_find_elements(driver,by.By.TAG_NAME, "p",log_list,module_name)
        if p_list is None:
            put_and_print(log_list, ["After click send access code, not find p elements"])
            return False
        for p in p_list:
            if p.text == "access code sent. please check mailbox":
                is_find_send = True
                break
        if is_find_send:
            break
        if i == 5:
            click_element(send_code_button,driver,is_debug,log_list,"Try again click send")
            if is_debug:
                put_and_print(log_list, ["Send timeout, try again send"])
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
    driver.implicitly_wait(120)
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
