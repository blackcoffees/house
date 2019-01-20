# -*- coding: utf-8 -*-
from urllib import unquote

import datetime
import scrapy
from scrapy import Request

from db.DBUtil import get_all_region
from db.PoolDB import pool
import json

from scrapy_spider.items import RealEstateItem
from util.CommonUtils import WebSource
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
    proxy_ip = "183.196.168.194:9000"
    region_index = 0
    list_region = list()

    def start_requests(self):
        # self.get_proxy_ip()
        base_url = u"http://www.cq315house.com/315web/webservice/GetMyData999.ashx?projectname=&" \
                   u"site=%s&kfs=&projectaddr=&pagesize=100&pageindex=%s&roomtype=住宅&buildarea"
        list_url = list()
        self.list_region = get_all_region()
        region = self.list_region[self.region_index]
        list_url.append(Request((base_url % (region.get("region"), 1)), meta={"proxy": "http://" + self.proxy_ip}))
        return list_url

    def parse(self, response):
        now_url = response.url
        try:
            page = int(now_url.split("pageindex=")[1].split("&room")[0])
            if not response.text:
                raise BaseException(u"需要切换代理")
            json_response = json.loads(response.text.replace("'", "\""))
            if not isinstance(json_response, list):
                raise BaseException(u"返回数据错误")
            if len(json_response) == 0:
                self.region_index += 1
                region = self.list_region[self.region_index]
                page = 0
                now_url = now_url.split("site=")[0] + "site=" + region.get("region") + "&kfs=" \
                          + now_url.split("&kfs=")[1]
                print u"切换区域:%s" % region.get("region")
                if self.region_index == len(self.list_region):
                    print u"收集结束"
                    return
            for json_data in json_response:
                if not json_data.get("F_ADDR"):
                    break
                item = RealEstateItem()
                item["address"] = json_data.get("F_ADDR")
                item["region"] = self.list_region[self.region_index].get("id")
                item["building"] = json_data.get("PROJECTNAME")
                item["developer"] = json_data.get("ENTERPRISENAME")
                item["sale_building"] = json_data.get("F_BLOCK")
                item["source_id"] = WebSource.RealEstate
                item["sale_count"] = json_data.get("NUM")
                item["building_sale_buildings"] = json_data.get("F_BLOCK")
                item["building_sale_residence_counts"] = json_data.get("BUILDZZNUM")
                item["building_sale_none_residence_counts"] = json_data.get("BUILDFZZNUM")
                item["building_web_build_ids"] = json_data.get("BUILDID")
                item["building_register_times"] = json_data.get("F_REGISTER_DATE")
                print "%s:%s" % (datetime.datetime.now(), json_data.get("F_SITE") + " " + json_data.get("PROJECTNAME"))
                yield item
        except BaseException as e:
            self.get_proxy_ip()
            print e
        finally:
            page += 1
            url = now_url.split("pageindex=")[0] + "pageindex=" + str(page) +"&room" + now_url.split("pageindex=")[1].split("&room")[1]
            yield Request(url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip})

    def get_proxy_ip(self):
        while True:
            self.proxy_ip = proxy_pool.get_proxy_ip(is_count_time=False)
            if self.proxy_ip:
                break