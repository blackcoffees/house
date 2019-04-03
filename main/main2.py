# -*- coding:utf8 -*-
from scrapy import cmdline

# cmdline.execute("scrapy crawl real_estate".split())
# cmdline.execute("scrapy crawl building".split())
# from scrapy.crawler import CrawlerProcess
# from scrapy_spider.spiders.house import RealEstateSpider, BuildingSpider
#
# process = CrawlerProcess()
# process.crawl(RealEstateSpider)
# process.crawl(BuildingSpider)
# process.start()

cmdline.execute("scrapy crawl real_estate".split())