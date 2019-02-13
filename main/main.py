# -*- coding:utf8 -*-
import pytesseract

from spider.House import HouseSpider
from spider.RealEstate import RealEstateSpider

if __name__ == "__main__":
    try:
        # a = RealEstateSpider()
        # a.work()
        b = HouseSpider()
        b.work()
    except BaseException as e:
        print e
