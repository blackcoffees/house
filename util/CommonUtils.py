# -*- coding:utf8 -*-
import cookielib
import urllib2

import os

import time

import pytesseract
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
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


def send_request(url, headers=None, data=None, cookies=None):
    index = 10
    while True:
        try:
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
            index = index - 1
            if index == 0:
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


def get_internet_validate_code(img):
    try:
        location_img_url = "e:/spider_img/temp.png"
        # 保存验证码图片
        # response = requests.get(img_url, cookies=cookies)
        # response = urllib2.urlopen(img_url)
        # opener = urllib2.build_opener()
        # opener.addheaders.append(("Cookie", cookies))
        # response = opener.open(img_url)
        left = img.location.get("x")
        top = img.location.get("y")
        width = left + img.size.get("width")
        height = top + img.size.get("height")
        # image = Image.open(BytesIO(response.read()))
        image = Image.open(location_img_url).crop((left, top, width, height))
        if not os.path.exists("e:/spider_img"):
            os.mkdir("e:/spider_img")
        image.save(location_img_url)
        # 解析验证码
        time.sleep(3)
        location_img = Image.open(location_img_url)
        # 转到灰度
        imgry = location_img.convert("L")
        imgry.save(location_img_url)
        # 对比度增强
        sharpness = ImageEnhance.Contrast(imgry)
        sharp_img = sharpness.enhance(2.0)
        sharp_img.save(location_img_url)
        # 二值化，采用阈值分割法，threshold为分割点
        out = sharp_img.point(table, '1')
        out.save(location_img_url)
        code_str = pytesseract.image_to_string(out, lang="chi_sim")
        code_str = code_str.strip()
        code_str = code_str.upper()
        for r in rep:
            code_str = code_str.replace(r, rep[r])
        if code_str[0].isdigit():
            number1 = int(code_str[0])
        else:
            raise BaseException
        if code_str[2].isdigit():
            number2 = int(code_str[2])
        else:
            raise BaseException
        if code_str[1] == u"\u52a0":
            return number1 + number2
        elif code_str[1] == u"\u51cf":
            return number1 - number2
        elif code_str[1] == u"\u4e58":
            return number1 * number2
        elif code_str[1] == u"\u9664":
            return number1 / number2
        return -1
    except BaseException as e:
        return -1



# 二值化
threshold = 140
table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

#由于都是数字
#对于识别成字母的 采用该表进行修正
rep={'O':'0',
    'I':'1','L':'1',
    'Z':'2',
    'S':'8'
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
        if temp_index <= n:
            temp_list.append(value)
            temp_index += 1
            if temp_index > n:
                return_dict[dict_index] = temp_list
                temp_index = 0
    return return_dict


def get_unit(house_count_dict, unit_list, house_index):
    for unit_index, house_list in house_count_dict.items():
        if house_index in house_list:
            return unit_list[unit_index]

