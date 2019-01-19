# -*- coding: utf-8 -*-
from urllib import unquote

import datetime
import scrapy
from scrapy import Request

from db.DBUtil import get_all_region
from db.PoolDB import pool
import json

from scrapy_spider.items import RealEstateItem
from util.ProxyIPUtil import proxy_pool


class HouseSpider(scrapy.Spider):
    name = 'house'
    # allowed_domains = ["http://www.cq315house.com"]
    # start_urls = [u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&"
    #               u"site=%s&kfs=&projectaddr=&pagesize=10&pageindex=%s&roomtype=住宅&buildarea"]
    #
    # def make_requests_from_url(self, url):
    #     sql = """select region, now_page from region order by sort"""
    #     result_sql = pool.find_one(sql)
    #     url = url % (result_sql.get("region"), result_sql.get("now_page"))
    #     return Request(url)
    proxy_ip = None
    region_index = 1
    list_region = list()

    def start_requests(self):
        self.get_proxy_ip()
        base_url = u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&" \
                   u"site=%s&kfs=&projectaddr=&pagesize=10&pageindex=%s&roomtype=住宅&buildarea"
        list_url = list()
        self.list_region = get_all_region()
        region = self.list_region[self.region_index]
        list_url.append(Request((base_url % (region.get("region"), region.get("now_page"))),
                                meta={"proxy": "http://" + self.proxy_ip}))
        return list_url

    def parse(self, response):
        try:
            page = int(response.url.split("pageindex=")[1].split("&room")[0])
            if page >= 30:
                self.region_index += 1
                region = self.list_region[self.region_index]
                page = 0
                url = response.url.split("site=")[0] + "site=" + region.get("region") + "&kfs="\
                      + response.url.split("&kfs=")[1]
                raise BaseException(u"切换区域")
            if not response.text:
                raise BaseException(u"需要切换代理")
            json_response = json.loads(response.text.replace("'", "\""))
            for json_data in json_response:
                item = RealEstateItem()
                item["address"] = json_data.get("F_ADDR")
                item["region"] = self.list_region[self.region_index].get("id")
                item["building"] = json_data.get("PROJECTNAME")
                item["developer"] = json_data.get("ENTERPRISENAME")
                item["sale_building"] = json_data.get("F_BLOCK")
                item["source_id"] = 1
                print "%s:%s" % (datetime.datetime.now(), json_data.get("F_SITE") + " " + json_data.get("PROJECTNAME"))
                yield item
        except BaseException as e:
            print e
            self.get_proxy_ip()
        finally:
            page += 1
            url = response.url.split("pageindex=")[0] + "pageindex=" + str(page) +"&room" + response.url.split("pageindex=")[1].split("&room")[1]
            yield Request(url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip})

    def get_proxy_ip(self):
        while True:
            self.proxy_ip = proxy_pool.get_proxy_ip(is_count_time=False)
            if self.proxy_ip:
                break
        print u"切换代理IP:%s" % self.proxy_ip