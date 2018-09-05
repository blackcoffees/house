# -*- coding:utf8 -*-
from spider.RealEstate import RealEstateSpider

if __name__ == "__main__":
    try:
        a = RealEstateSpider()
        a.work()
    except BaseException as e:
        print e
