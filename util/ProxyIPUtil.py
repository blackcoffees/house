# -*- coding:utf8 -*-
import random

import datetime
from bs4 import BeautifulSoup
switch_proxy = False


def get_switch_proxy(self):
    return switch_proxy


def set_switch_proxy(value):
    switch_proxy = value


class ProxyPool(object):
    list_proxy_ip = list()
    switch_proxy = False

    def __init__(self):
        self.switch_proxy = True

    def __get_proxy_ip_kuaidaili(self):
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

    def __get_proxy_ip_feiyi(self):
        """
        获得飞蚁的免费代理ip
        :return:
        """
        from util.CommonUtils import send_request
        base_url = "http://www.feiyiproxy.com/?page_id=1457"
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("div", attrs={"class": "et_pb_code et_pb_module et_pb_code_1"}).find("table")
        list_trs = table.find_all("tr")[1:]
        print u"获得飞蚁ip:%s" % len(list_trs)
        for tr in list_trs:
            ip = tr.find("td").text
            port = tr.find_all("td")[1].text
            proxy_ip = "%s:%s" % (ip, port)
            self.list_proxy_ip.append(proxy_ip)

    def get_proxy_ip_xici(self):
        """
        获得xici的免费代理ip
        :return:
        """
        from util.CommonUtils import send_request
        random_number = random.randrange(1, 3000)
        base_url = "https://www.xicidaili.com/nn/%s" % random_number
        response = send_request(base_url)
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", attrs={"id": "ip_list"})
        list_trs = table.find_all("tr")[1:]
        base_url = "https://www.xicidaili.com/nt/%s" % random_number
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

    def get_proxy_ip(self):
        from util.CommonUtils import test_proxy_ip_send_request
        if self.switch_proxy and len(self.list_proxy_ip) == 0:
            self.__get_proxy_ip_kuaidaili()
            # self.__get_proxy_ip_feiyi()
            self.get_proxy_ip_xici()
        if not self.switch_proxy:
            self.switch_proxy = True
        if (len(self.list_proxy_ip)) > 0:
            start_time = datetime.datetime.now()
            for proxy_ip in self.list_proxy_ip:
                if test_proxy_ip_send_request(proxy_ip):
                    return proxy_ip
                else:
                    self.list_proxy_ip.remove(proxy_ip)
                end_time = datetime.datetime.now()
                if (end_time - start_time).seconds > 300:
                    return None
        else:
            return None


proxy_pool = ProxyPool()