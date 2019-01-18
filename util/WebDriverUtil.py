# -*- coding:utf8 -*-
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from util.ProxyIPUtil import proxy_pool


class WebDriverManager(object):
    total_count = 0
    options = None
    type = None
    proxy_ip = None
    __list_web_driver__ = list()

    def __base_result__(self):
        return {"succ": False, "message": "系统繁忙，请稍后再试", "data": dict()}

    def __init__(self, count, type, options=None):
        self.total_count = count
        self.type = type
        self.options = options
        result = self.__base_result__()
        if count <= 0:
            result["message"] = "数量不能小于等于0"
        for index in range(count):
            self.create_web_driver()

    def get_web_driver(self, is_proxy=False):
        for web_driver in self.__list_web_driver__:
            if not web_driver.is_used():
                web_driver.use()
                return web_driver
        if len(self.__list_web_driver__) != self.total_count:
            self.create_web_driver(is_proxy)
            return self.__list_web_driver__[len(self.__list_web_driver__)-1]

    def destroy_all(self):
        for web_driver in range(len(self.__list_web_driver__)):
            web_driver.close()

    def destory_web_driver(self, web_driver_id):
        for web_driver in self.__list_web_driver__:
            if web_driver.get_id() == web_driver_id:
                web_driver.close()
                if self.proxy_ip:
                    proxy_pool.remove_proxy_ip(self.proxy_ip)
                    self.proxy_ip = None
                self.__list_web_driver__.remove(web_driver)
        # self.create_web_driver()

    def create_web_driver(self, is_proxy=False):
        if self.type == "chrome":
            temp_options = self.options
            if is_proxy:
                proxy_ip = proxy_pool.get_proxy_ip()
                if proxy_ip:
                    self.proxy_ip = proxy_ip
                    temp_options.add_argument("--proxy-server={0}".format(proxy_ip))
            temp_driver = WebChromeDriver(temp_options)
        else:
            raise BaseException("暂不支持该浏览器")
        self.__list_web_driver__.append(temp_driver)


class WebChromeDriver(webdriver.Chrome):
    id = None
    is_use = False

    def __init__(self, options=None):
        self.id = int(time.time())
        if options:
            webdriver.Chrome.__init__(self, options=options)
        else:
            webdriver.Chrome.__init__(self)

    def is_used(self):
        return self.is_use

    def use(self):
        self.is_use = True

    def send_url(self, url, tag_name="body"):
        super(webdriver.Chrome, self).get(url)
        looper = 10
        while True:
            if looper == 0:
                return False
            try:
                WebDriverWait(self, 30).until(expected_conditions.presence_of_element_located((By.TAG_NAME, tag_name)))
                return True
            except BaseException as e:
                looper -= 1
        return False

    def get_id(self):
        return self.id