# -*- coding:utf8 -*-
import json
import logging
import random

import datetime
import urllib2

import os
from bs4 import BeautifulSoup

from util.CommonUtils import logger

switch_proxy = False


def get_switch_proxy(self):
    return switch_proxy


def set_switch_proxy(value):
    switch_proxy = value


class ProxyPool(object):
    list_proxy_ip = list()
    switch_proxy = False
    test_url = None
    __proxy_ip_conf_file_path__ = os.path.abspath(__file__).split(os.path.basename(__file__))[0]+"\\proxy_ip_conf.text"

    def __init__(self, test_url):
        self.switch_proxy = True
        if not test_url:
            raise BaseException(u"请输入代理ip测试地址")
        self.test_url = test_url
        if not os.path.exists(self.__proxy_ip_conf_file_path__):
            proxy_ip_file = open(self.__proxy_ip_conf_file_path__, "w")
            temp_dict = {"list_online_proxy_ip": list(), "list_static_proxy_ip": list()}
            proxy_ip_file.write(json.dumps(temp_dict))
            proxy_ip_file.close()

    def __get_proxy_ip_kuaidaili__(self):
        """
        获取快代理的免费代理ip
        :return:
        """
        from util.CommonUtils import send_request
        base_url = "https://www.kuaidaili.com/free/intr/%s/" % (random.randrange(1, 1000))
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", attrs={"class": "table"})
        trs = table.find("tbody").find_all("tr")
        print u"获得快代理ip:%s" % len(trs)
        for tr in trs:
            ip = tr.find("td").text
            port = tr.find_all("td")[1].text
            proxy_ip = "%s:%s" % (ip, port)
            self.list_proxy_ip.append(proxy_ip)

    def __get_proxy_ip_xici__(self):
        """
        获得xici的免费代理ip
        :return:
        """
        from util.CommonUtils import send_request
        list_trs = list()
        # 透明
        base_url = "https://www.xicidaili.com/nt/%s" % random.randrange(1, 723)
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", attrs={"id": "ip_list"})
        list_trs.extend(table.find_all("tr")[1:])
        # 代理
        base_url = "https://www.xicidaili.com/wt/%s" % random.randrange(1, 1900)
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", attrs={"id": "ip_list"})
        list_trs.extend(table.find_all("tr")[1:])
        # 高匿
        base_url = "https://www.xicidaili.com/nn/%s" % random.randrange(1, 3000)
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", attrs={"id": "ip_list"})
        list_trs.extend(table.find_all("tr")[1:])
        print u"获得xici ip:%s" % len(list_trs)
        for tr in list_trs:
            ip = tr.find_all("td")[1].text
            port = tr.find_all("td")[2].text
            proxy_ip = "%s:%s" % (ip, port)
            self.list_proxy_ip.append(proxy_ip)

    def __get_proxy_ip_conf__(self):
        if not os.path.exists(self.__proxy_ip_conf_file_path__):
            return
        file_str = ""
        with open(self.__proxy_ip_conf_file_path__) as proxy_file:
           file_str = proxy_file.readlines()
        if not file_str:
            print u"代理IP文件解析错误"
        is_exception = False
        for str in file_str:
            try:
                json_str = json.loads(str)
                if json_str.get("list_online_proxy_ip"):
                    self.list_proxy_ip.extend(json_str.get("list_online_proxy_ip"))
                if json_str.get("list_static_proxy_ip"):
                    self.list_proxy_ip.extend(json_str.get("list_static_proxy_ip"))
                random.shuffle(self.list_proxy_ip)
                print u"获得文件代理ip:%s" % (len(json_str.get("list_online_proxy_ip")) + len(json_str.get("list_static_proxy_ip")))
            except:
                is_exception = True
                continue
        if is_exception:
            print u"代理IP文件解析错误"

    def get_proxy_ip(self, is_count_time=True):
        if self.switch_proxy and len(self.list_proxy_ip) == 0:
            self.__get_proxy_ip_conf__()
            self.__get_proxy_ip_kuaidaili__()
            # self.__get_proxy_ip_feiyi()
            self.__get_proxy_ip_xici__()
        if not self.switch_proxy:
            self.switch_proxy = True
        if (len(self.list_proxy_ip)) > 0:
            start_time = datetime.datetime.now()
            for proxy_ip in self.list_proxy_ip:
                if self.__test_proxy_ip_send_request__(proxy_ip):
                    return proxy_ip
                else:
                    self.list_proxy_ip.remove(proxy_ip)
                end_time = datetime.datetime.now()
                if is_count_time and (end_time - start_time).seconds > 300:
                    return None
        else:
            return None

    def remove_proxy_ip(self, ip):
        if ip in self.list_proxy_ip:
            self.list_proxy_ip.remove(ip)

    def __test_proxy_ip_send_request__(self, proxy_ip):
        """
        测试代理Ip的请求
        :param url:
        :param proxy_ip:
        :return:
        """
        url = self.test_url
        try:
            temp_proxy_dict = {"http": "http://%s" % proxy_ip, "https:": "https://%s" % proxy_ip}
            proxy_support = urllib2.ProxyHandler(temp_proxy_dict)
            opener = urllib2.build_opener(proxy_support)
            urllib2.install_opener(opener)
            request = urllib2.Request(url, data=json.dumps({"areaType": "", "entName": "", "location": "", "maxrow": 11, "minrow": 1,
                                                 "projectname": "", "siteid": 34, "useType": "1"}),
                                      headers={"Content-Type": "application/json"})
            response = urllib2.urlopen(request, timeout=30)
            if response.code == 200:
                if response.read():
                    logger.info(u"测试代理IP,切换代理IP:%s" % proxy_ip)
                    file_str = ""
                    with open(self.__proxy_ip_conf_file_path__) as file:
                        file_str = file.readlines()
                    if not file_str:
                        print u"代理IP文件解析错误"
                    for str in file_str:
                        try:
                            json_str = json.loads(str)
                            list_online_proxy_ip = json_str.get("list_online_proxy_ip")
                            if not proxy_ip in list_online_proxy_ip:
                                list_online_proxy_ip.append(proxy_ip)
                                dict_temp = {"list_online_proxy_ip": list_online_proxy_ip, "list_static_proxy_ip": json_str.get("list_static_proxy_ip")}
                                with open(self.__proxy_ip_conf_file_path__, "w") as file:
                                    file.write(json.dumps(dict_temp))
                        except:
                            continue
                    return True
            return False
        except BaseException as e:
            print u"%s，代理ip测试请求:%s error:%s" % (datetime.datetime.now(), proxy_ip, e)
            return False


# proxy_pool = ProxyPool("http://www.cq315house.com/315web/HtmlPage/SpfQuery.htm")
proxy_pool = ProxyPool("http://www.cq315house.com/WebService/Service.asmx/getParamDatas2")