# -*- coding:utf8 -*-
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class WebDriverManager(object):
    __list_web_driver__ = list()

    def __base_result__(self):
        return {"succ": False, "message": "系统繁忙，请稍后再试", "data": dict()}

    def __init__(self, count, type, options=None):
        result = self.__base_result__()
        if count <= 0:
            result["message"] = "数量不能小于等于0"
        for index in range(count):
            self.__list_web_driver__.append(WebDriver(type, options))

    def get_web_driver(self):
        for web_driver in self.__list_web_driver__:
            if not web_driver.is_used():
                web_driver.use()
                return web_driver

        return self.__list_web_driver__

    def destroy_all(self):
        for web_driver in range(len(self.__list_web_driver__)):
            web_driver.destroy()


class WebDriver(object):
    id = None
    web_driver = None
    is_use = False

    def __init__(self, type, options=None):
        self.id = int(time.time())
        if type == "chrome":
            if options:
                self.web_driver = webdriver.Chrome(chrome_options=options)
            else:
                self.web_driver = webdriver.Chrome()
            self.set_page_load_timeout(120)
            self.set_script_timeout(140)

    def destroy(self):
        self.web_driver.close()

    def set_page_load_timeout(self, time):
        self.web_driver.set_page_load_timeout(time)

    def set_script_timeout(self, time):
        self.web_driver.set_script_timeout(time)

    def is_used(self):
        return self.is_use

    def use(self):
        self.is_use = True

    def send_url(self, url):
        self.web_driver.get(url)
        looper = 10
        while True:
            if looper == 0:
                return False
            try:
                WebDriverWait(self.web_driver, 30).until(expected_conditions.presence_of_element_located((By.TAG_NAME, "body")))
                break
            except BaseException as e:
                looper -= 1
        return True

    def get_web_driver(self):
        return self.web_driver

    def find_element_by_tag_name(self, name):
        return self.web_driver.find_element_by_tag_name(name)