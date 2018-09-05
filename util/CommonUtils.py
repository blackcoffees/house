# -*- coding:utf8 -*-
import urllib2


class Region(type):
    BaNan = "巴南"

    all_region = [BaNan]


def send_request(url, headers=None, data=None):
    if headers and data:
        request = urllib2.Request(url, headers=headers, data=data)
    elif headers:
        request = urllib2.Request(url, headers=headers)
    elif data:
        request = urllib2.Request(url, data=data)
    else:
        request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    if response.code == 200:
        return response.read()
    else:
        return False


def get_fields(obj):
    fileds = list()
    for field in dir(obj):
        if "__" not in field:
            fileds.append(field)
    return fileds


class WebSource(type):
    RealEstate = 1
