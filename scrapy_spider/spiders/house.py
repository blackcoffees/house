# -*- coding: utf-8 -*-
from urllib import unquote

import datetime

import os
import scrapy
import sys

from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.exceptions import CloseSpider

from db.DBUtil import get_all_region, get_building_statictics_data, update_building_count
from db.PoolDB import pool
import json

from scrapy_spider.items import RealEstateItem, HouseItem
from util.CommonUtils import WebSource, validate_house_door_number, logger, is_json
from util.ProxyIPUtil import proxy_pool

reload(sys)
sys.setdefaultencoding( "utf-8" )


class RealEstateSpider(scrapy.Spider):
    name = 'real_estate'
    proxy_ip = None
    region_index = 0
    list_region = list()

    def start_requests(self):
        self.get_proxy_ip()
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
            json_response = json.loads(response.text.replace("'", "\"").replace("\\", "\\\\").replace("\n", ""))
            if not isinstance(json_response, list):
                raise BaseException(u"返回数据错误")
            if len(json_response) == 0:
                self.region_index += 1
                if self.region_index >= len(self.list_region):
                    print u"所有区域收集完成"
                    raise CloseSpider()
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
                item["name"] = json_data.get("PROJECTNAME")
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
            if type(e) == CloseSpider:
                raise CloseSpider()
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


class BuildingSpider(scrapy.Spider):

    name = "building"
    build_index = 0
    proxy_ip = "113.200.214.164:9999"
    db_building = None
    base_build_sql = """select * from building where pre_sale_number is NULL order by id limit %s,1"""
    base_house_url = "http://www.cq315house.com/315web/HtmlPage/ShowRoomsNew.aspx?block=&buildingid=%s"

    def start_requests(self):
        self.get_proxy_ip()
        sql = self.base_build_sql % self.build_index
        self.db_building = pool.find_one(sql)
        url = self.base_house_url % self.db_building.get("web_build_id")
        return [Request(url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip})]

    def parse(self, response):
        has_house = False
        try:
            if "HtmlPage" in response.url:
                table_houses = response.xpath("//input[@id='DataHF']")
                if len(table_houses) == 0:
                    raise BaseException(u"没有获取到数据")
                if table_houses.attrib.get("value"):
                    for json_house in json.loads(table_houses.attrib.get("value")):
                        list_houses = json_house.get("rooms")
                        for one_house in list_houses:
                            if not validate_house_door_number(one_house.get("rn")):
                                continue
                            item = HouseItem()
                            item["door_number"] = str(one_house.get("flr")) + "-" + one_house.get("rn")
                            item["status"] = 6
                            item["inside_area"] = 0
                            item["built_area"] = 0
                            item["house_type"] = ""
                            item["inside_price"] = 0
                            item["built_price"] = 0
                            item["real_estate_id"] = self.db_building.get("real_estate_id")
                            item["source_id"] = self.db_building.get("source_id")
                            item["building_id"] = self.db_building.get("id")
                            item["unit"] = str(one_house.get("unitnumber")) + "单元"
                            item["web_house_id"] = one_house.get("id")
                            print u"%s：%s：%s：%s" % (self.db_building.get("real_estate_name"), item["unit"],
                                                    self.db_building.get("sale_building"), item["door_number"])
                            has_house = True
                            yield item
            # 保存预售许可证
            if "GetBuildingInfo" in response.url:
                if response.text:
                    if is_json(response.text):
                        json_build = json.loads(response.text)
                        sql = """update building set pre_sale_number=%s, updated=%s where id=%s"""
                        pool.commit(sql, (json_build.get("presaleCert"), datetime.datetime.now(), self.db_building.get("id")))
                        # 统计数据
                        building_static_data = get_building_statictics_data(self.db_building.get("id"), self.db_building.get("real_estate_id"))
                        update_building_count(self.db_building.get("id"), building_static_data.get("total_count"),
                                              building_static_data.get("sale_count"))
                        print "%s:%s::完成：" % (self.db_building.get("real_estate_name"), self.db_building.get("sale_building"))
        except BaseException as e:
            logger.error(e)
            self.get_proxy_ip()
        finally:
            if "GetBuildingInfo" in response.url:
                # 切换另外一个building
                self.db_building = pool.find_one((self.base_build_sql % self.build_index))
                house_url = self.base_house_url % self.db_building.get("web_build_id")
                yield Request(house_url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip})
            else:
                if not has_house:
                    if response.meta.get("proxy") == "http://" + self.proxy_ip:
                        self.get_proxy_ip()
                    house_url = self.base_house_url % self.db_building.get("web_build_id")
                    yield Request(house_url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip},
                                  dont_filter=True)
                else:
                    # 获得预售许可证
                    build_url = "http://www.cq315house.com/315web/webservice/GetBuildingInfo.ashx?buildingId=%s" \
                                % self.db_building.get("web_build_id")
                    yield Request(build_url, callback=self.parse, meta={"proxy": "http://" + self.proxy_ip})

    def get_proxy_ip(self):
        while True:
            proxy_pool.remove_proxy_ip(self.proxy_ip)
            self.proxy_ip = proxy_pool.get_proxy_ip(is_count_time=False)
            if self.proxy_ip:
                break
