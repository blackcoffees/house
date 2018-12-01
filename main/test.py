import logging
import urllib

from PIL import Image
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from selenium import webdriver

from db import DBUtil
from spider.RealEstate import RealEstateSpider
from util.CommonUtils import chinese_correct, send_request
from util.ImageUtil import alpha_composite_simple, blend, composite, test_eval, merge, cute, compare_image, \
    image_corde_correct, getbands, getbbox, getcolors
from util.ProxyIPUtil import get_proxy_ip

if __name__ == "__main__":
    try:
        get_proxy_ip()
    except BaseException as e:
        print e
