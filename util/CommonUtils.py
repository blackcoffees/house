# -*- coding:utf8 -*-
import cookielib
import logging
import random
import urllib2

import os

import time
from logging.handlers import TimedRotatingFileHandler
from urllib import unquote

import datetime
import pytesseract
import requests
from PIL import Image, ImageEnhance
from io import BytesIO

from bs4 import BeautifulSoup
from selenium import webdriver
from urllib3 import response


class Region(type):
    BaNan = "巴南"
    BeiBei = "北碚"
    DaDuKou = "大渡口"
    JiangBei = "江北"
    JiuLongPo = "九龙坡"
    NanAn = "南岸"
    ShaPingBa = "沙坪坝"
    YuBei = "渝北"
    YuZhong = "渝中"
    LiangJiang = "两江新"

    all_region = [BaNan, BeiBei, DaDuKou, JiangBei, JiuLongPo, NanAn, ShaPingBa, YuBei, LiangJiang]


formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(msg)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_path = os.path.dirname(os.getcwd()) + '/logs/'
log_filename = log_path + time.strftime("%Y%m%d", time.localtime()) + ".log"
fh = TimedRotatingFileHandler(log_filename, when="d", encoding='utf-8', backupCount=7)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(console_handler)


def send_request(url, headers=None, data=None, cookies=None, proxy=False):
    index = 10
    proxy_ip = None
    while True:
        index = index - 1
        try:
            if proxy:
                proxy_ip = "v.as2333.win:11688"
                logging.info("切换代理ip:%s" % proxy_ip)
                temp_proxy_dict = {"http": "http://%s" % proxy_ip, "https:": "https://%s" % proxy_ip}
                proxy_support = urllib2.ProxyHandler(temp_proxy_dict)
                opener = urllib2.build_opener(proxy_support)
                urllib2.install_opener(opener)
                pass
            if headers and data and cookies:
                request = urllib2.Request(url, headers=headers, data=data, cookies=cookies)
            elif headers and cookies:
                request = urllib2.Request(url, headers=headers, cookies=cookies)
            elif data and cookies:
                request = urllib2.Request(url, data=data, cookies=cookies)
            elif data and headers:
                request = urllib2.Request(url, data=data, headers=headers)
            elif headers:
                request = urllib2.Request(url, headers=headers)
            elif data:
                request = urllib2.Request(url, data=data)
            elif cookies:
                request = urllib2.Request(url, cookies=cookies)
            else:
                request = urllib2.Request(url)
            response = urllib2.urlopen(request, timeout=120)
            if response.code == 200:
                return response.read()
                response_text = response.read()
                if not response_text:
                    if proxy:
                        if proxy_ip:
                            proxy = False
                        else:
                            proxy = True
                        continue
                    else:
                        if proxy_ip:
                            proxy = False
                        else:
                            proxy = True
                        continue
                else:
                    return response_text
            else:
                return False
            break
        except BaseException as e:
            if index == 0:
                return False
                break
            print e


def get_fields(obj):
    fileds = list()
    for field in dir(obj):
        if "__" not in field:
            fileds.append(field)
    return fileds


class WebSource(type):
    RealEstate = 1

# 二值化
threshold = 140
table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

# 由于都是数字
# 对于识别成字母的 采用该表进行修正
rep = {"O": "0", "I": "1", "L": "1", "Z": "2", "S": "8"}

chinese_correct = {
    u"夕刀": u"加", u"夕奴": u"加", u"潺": u"减", u"汐奴": u"加", u"遂夕": u"加", u"儡": u"1", u"喊": u"减", u"遂奴": u"加"
}


ColorStatus = {
    "#c0c0c0": 1, # 限制销售
    "#00ff00": 2, # 可售
    "#ff00ff": 3, # 预定
    "#ffff00": 4, # 已售
    "#ff0000": 5 # 已登记
}


def get_status(color):
    color = color.replace(" ", "")
    if "#" in color:
        return ColorStatus.get(color)
    elif color == "rgb(192,192,192)":
        return 1
    elif color == "rgb(0,255,0)":
        return 2
    elif color == "rgb(255,0,255)":
        return 3
    elif color == "rgb(255,255,0)":
        return 4
    elif color == "rgb(255,0,0)":
        return 5
    else:
        return 0


def div_list_return_dict(array, n):
    """
    等分数组
    :param list:
    :param n:
    :return:
    """
    n = len(array) / n
    if not isinstance(array, list) or not isinstance(n, int):
        return {0: array}
    if n > len(array):
        return {0: array}
    if n <= 1:
        return {0: array}
    temp_index = 0
    dict_index = 0
    return_dict = dict()
    temp_list = list()
    for index, value in enumerate(array):
        if temp_index <= n-1:
            temp_list.append(value)
            temp_index += 1
        else:
            return_dict[dict_index] = temp_list
            temp_index = 0
            temp_list = [index]
            dict_index += 1
    if temp_list:
        return_dict[dict_index] = temp_list
    return return_dict


def get_unit(house_count_dict, unit_list, house_index):
    for unit_index, house_list in house_count_dict.items():
        if house_index in house_list:
            return unit_list[unit_index]


proxy_list = list()


# def get_proxy_ips():
#     url = "https://www.kuaidaili.com/free/inha/%s/" % random.randint(1, 100)
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     trs = soup.find_all('tr')
#     for tr in trs:
#         tds = tr.find_all('td')
#         if not tds:
#             continue
#         proxy_list.append("%s:%s" % (tds[0].text, tds[1].text))
#
#
# def delete_proxy(ip_info):
#     proxy_list.remove(ip_info)
#
#
# def get_first_proxy_ip():
#     if proxy_list:
#         return proxy_list[0]
#     else:
#         return False
