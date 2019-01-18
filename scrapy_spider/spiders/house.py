# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request

from db.PoolDB import pool
import json

from scrapy_spider.items import RealEstateItem


class HouseSpider(scrapy.Spider):
    name = 'house'
    # allowed_domains = ["http://www.cq315house.com"]
    start_urls = [u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&"
                  u"site=%s&kfs=&projectaddr=&pagesize=10&pageindex=%s&roomtype=住宅&buildarea"]

    def make_requests_from_url(self, url):
        sql = """select region, now_page from region order by sort"""
        result_sql = pool.find_one(sql)
        url = url % (result_sql.get("region"), result_sql.get("now_page"))
        return Request(url)

    def parse(self, response):
        if not response.text:
            pass
        json_response = json.loads(response.text.replace("'", "\""))
        for json_data in json_response:
            item = RealEstateItem()
            item["address"] = json_data.get("F_ADDR")
            sql_region = """select * from region where region=%s"""
            result_sql_region = pool.find_one(sql_region, [json_data.get("F_SITE")])
            item["region"] = result_sql_region.get("id")
            item["building"] = json_data.get("PROJECTNAME")
            item["developer"] = json_data.get("ENTERPRISENAME")
            item["sale_building"] = json_data.get("F_BLOCK")
            item["source_id"] = 1
            print json_data.get("PROJECTNAME")
            yield item


























        # yield Request(u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&site=巴南&kfs=&projectaddr=&pagesize=10&pageindex=2&roomtype=住宅&buildarea")

