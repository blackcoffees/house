# -*- coding: utf-8 -*-
import scrapy


class HouseSpider(scrapy.Spider):
    name = 'house'
    allowed_domains = ['www.cq315house.com/315web/HtmlPage/SpfQuery.htm']
    start_urls = ['http://www.cq315house.com/315web/HtmlPage/SpfQuery.htm/']

    def parse(self, response):
        pass
