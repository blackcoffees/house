# -*- coding:utf8 -*-
import random

from bs4 import BeautifulSoup


list_proxy_ip = list()

switch_proxy = True


def get_proxy_ip():
    if not switch_proxy:
        return None
    __get_proxy_ip_kuaidaili()
    if (len(list_proxy_ip)) > 0:
        return list_proxy_ip[0]
    else:
        return None


def get_switch_proxy():
    return switch_proxy


def set_switch_proxy(value):
    switch_proxy = value


def __get_proxy_ip_kuaidaili():
    """
    获取快代理的免费代理ip
    :return:
    """
    from util.CommonUtils import send_request, test_proxy_ip_send_request
    if len(list_proxy_ip) > 0:
        return True
    base_url = "https://www.kuaidaili.com/free/intr/%s/" % (random.randrange(1, 1000))
    response = send_request(base_url, get_proxy=True)
    soup = BeautifulSoup(response, "html.parser")
    table = soup.find("table", attrs={"class": "table"})
    trs = table.find("tbody").find_all("tr")
    for tr in trs:
        ip = tr.find("td").text
        port = tr.find_all("td")[1].text
        proxy_ip = "%s:%s" % (ip, port)
        if test_proxy_ip_send_request(proxy_ip):
            list_proxy_ip.append(proxy_ip)


def remove_unvalidate_proxy_ip(proxy_ip):
    if proxy_ip:
        list_proxy_ip.remove(proxy_ip)