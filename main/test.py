import logging
import urllib

from PIL import Image
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from selenium import webdriver

from spider.RealEstate import RealEstateSpider
from util.CommonUtils import chinese_correct, send_request
from util.ImageUtil import alpha_composite_simple, blend, composite, test_eval, merge, cute, compare_image, \
    image_corde_correct, getbands, getbbox, getcolors

if __name__ == "__main__":
    try:
        pass
    except BaseException as e:
        print e
