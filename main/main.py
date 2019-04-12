# -*- coding:utf8 -*-
import os
import pytesseract
from scrapy import cmdline

from scrapy_spider.spiders.house import BuildingSpider, RealEstateSpider, HouseSpider

# if __name__ == "__main__":
#     try:
#         a = RealEstateSpider()
#         a.work()
#         b = BuildingSpider()
#         b.work()
#         c = HouseSpider()
#         c.work()
#     except BaseException as e:
#         print e

# # cmdline.execute("scrapy crawl real_estate".split())
# cmdline.execute("scrapy crawl building".split())
# # cmdline.execute("scrapy crawl house".split())

os.system("scrapy crawl real_estate")
os.system("scrapy crawl building")
os.system("scrapy crawl house")