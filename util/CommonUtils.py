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

    all_region = [BaNan]


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
        out = imgry.point(table, '1')
        out.save(location_img_url)
        code_str = pytesseract.image_to_string(sharp_img, lang="chi_sim")
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
        return 0
    except BaseException as e:
        return 0



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
    };