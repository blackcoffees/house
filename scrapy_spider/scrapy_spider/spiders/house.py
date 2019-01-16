# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request

from db.PoolDB import pool
import json

class HouseSpider(scrapy.Spider):
    name = 'house'
    # allowed_domains = ["http://www.cq315house.com"]
    start_urls = [u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&site=%s&kfs=&projectaddr=&pagesize=10&pageindex=%s&roomtype=住宅&buildarea"]

    def make_requests_from_url(self, url):
        sql = """select region, now_page from region order by sort"""
        result_sql = pool.find_one(sql)
        url = url % (result_sql.get("region"), result_sql.get("now_page"))
        return Request(url)

    def parse(self, response):
        json_response = json.loads(response.text)

        # yield Request(u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&site=巴南&kfs=&projectaddr=&pagesize=10&pageindex=2&roomtype=住宅&buildarea")

