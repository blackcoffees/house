# -*- coding:utf8 -*-
import cookielib
import json
import logging
import random
import urllib2

import os

import time
from logging.handlers import TimedRotatingFileHandler

import datetime


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


def send_request(url, headers=None, data=None, cookies=None):
    index = 5
    while True:
        index = index - 1
        try:
            user_agent = list_user_agent[random.randrange(1, len(list_user_agent))]
            if headers:
                headers_key = [x.lower() for x in headers.keys()]
                if not "user-agent" in headers_key:
                    headers = {"User-Agent": user_agent}
            else:
                headers = {"User-Agent": user_agent}
            # 发送请求
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
            else:
                return False
            break
        except BaseException as e:
            print u"请求:%s error:%s" % (url, e)
        finally:
            if index == 0:
                break


def get_fields(obj):
    fileds = list()
    for field in dir(obj):
        if "__" not in field:
            fileds.append(field)
    return fileds


class WebSource(type):
    RealEstate = 1


ColorStatus = {
    "#c0c0c0": 1, # 限制销售
    "#00ff00": 2, # 可售
    "#ff00ff": 3, # 预定
    "#ffff00": 4, # 已售
    "#ff0000": 5 # 已登记
}

chinese_status = {
    u"限制销售": 1,
    u"可售": 2,
    u"预定": 3,
    u"已售": 4,
    u"已登记": 5
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
    if n == 0:
        return {0: len(array)}
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


def validate_house_door_number(door_number):
    list_nonvalidate = [u"井", u"商", u"架空", u"消", u"间", u"中心", u"站", u"室", u"房", u"超市"]
    for nonvalidate in list_nonvalidate:
        if nonvalidate in door_number:
            return False
    return True


list_user_agent = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",

    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",

    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.2)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0 Zune 3.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 4.0.20402; MS-RTC LM 8)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 1.1.4322; InfoPath.2)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Tablet PC 2.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 3.0.04506; Media Center PC 5.0; SLCC1)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Tablet PC 2.0; .NET CLR 3.0.04506; Media Center PC 5.0; SLCC1)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; FDM; Tablet PC 2.0; .NET CLR 4.0.20506; OfficeLiveConnector.1.4; OfficeLivePatch.1.3)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 3.0.04506; Media Center PC 5.0; SLCC1; Tablet PC 2.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 1.1.4322; InfoPath.2)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.3029; Media Center PC 6.0; Tablet PC 2.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.1)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; FDM; .NET CLR 1.1.4322)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; InfoPath.1; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; InfoPath.1)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.40607)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.1.4322)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.1; .NET CLR 1.0.3705; Media Center PC 3.1; Alexa Toolbar; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; el-GR)',
    'Mozilla/5.0 (MSIE 7.0; Macintosh; U; SunOS; X11; gu; SV1; InfoPath.2; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)',
    'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; c .NET CLR 3.0.04506; .NET CLR 3.5.30707; InfoPath.1; el-GR)',
    'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; c .NET CLR 3.0.04506; .NET CLR 3.5.30707; InfoPath.1; el-GR)',
    'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.0; fr-FR)',
    'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.0; en-US)',
    'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; .NET CLR 2.0.50727)',
    'Mozilla/4.79 [en] (compatible; MSIE 7.0; Windows NT 5.0; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)',
    'Mozilla/4.0 (Windows; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (Mozilla/4.0; MSIE 7.0; Windows NT 5.1; FDM; SV1; .NET CLR 3.0.04506.30)',
    'Mozilla/4.0 (Mozilla/4.0; MSIE 7.0; Windows NT 5.1; FDM; SV1)',
    'Mozilla/4.0 (compatible;MSIE 7.0;Windows NT 6.0)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0;)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; YPC 3.2.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; InfoPath.2; .NET CLR 3.5.30729; .NET CLR 3.0.30618)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; YPC 3.2.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; Media Center PC 5.0; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 3.0.04506)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; InfoPath.2; .NET CLR 3.5.30729; .NET CLR 3.0.30618; .NET CLR 1.1.4322)',
]


def delete_logs():
    base_path = os.path.realpath("image").split("main")[0] + "\\logs\\"
    files = os.listdir(base_path)
    files = sorted(files, key=lambda x: int(x.split(".log")[0]), reverse=True)
    for index, file in enumerate(files):
        if index > 6:
            os.remove(base_path + file)
            logging.error(u"删除日志成功")


def is_json(json_str):
    try:
        json_build = json.loads(json_str)
        return True
    except:
        return False


def is_number(number):
    try:
        int(number)
        return True
    except:
        return False


def is_building_name(building_name):
    list_not_name = [u"地下车库"]
    for item_not_name in list_not_name:
        if item_not_name in building_name:
            return False
    return True


HOUSE_TYPE = u"House Type"
HOUSE_STRUC = u"House Structure"

# 日志
##################################################################
# Logging settings
##################################################################
# 格式
log_formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(msg)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")
# handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
log_path = os.path.dirname(os.getcwd()) + '/logs/'
log_filename = log_path + time.strftime("%Y%m%d", time.localtime()) + ".log"
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.WARNING)

logger = logging.getLogger("house")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)