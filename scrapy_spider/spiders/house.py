# -*- coding: utf-8 -*-
import logging
from urllib import unquote

import datetime

import os
import scrapy
import sys

from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.exceptions import CloseSpider

from db.DBUtil import get_all_region, get_building_statictics_data, update_building_count, get_house_attribute
from db.PoolDB import pool
import json

from scrapy_spider.items import RealEstateItem, HouseItem
from util.CommonUtils import WebSource, validate_house_door_number, is_json, logger, ColorStatus, is_number, HOUSE_TYPE, \
    HOUSE_STRUC
from util.ProxyIPUtil import proxy_pool


class RealEstateSpider(scrapy.Spider):
    name = 'real_estate'
    region_index = 0
    is_change_proxy = True
    list_region = list()
    base_url = u"http://www.cq315house.com/WebService/Service.asmx/getParamDatas2"
    web_page = 0
    web_size = 40

    def start_requests(self):
        self.list_region = get_all_region()
        return [self.create_request()]

    def parse(self, response):
        self.is_change_proxy = False
        try:
            if not response.text:
                raise BaseException(u"需要切换代理")
            if not is_json(response.text):
                yield self.create_request()
            json_response = json.loads(json.loads(response.text).get("d").replace("\\", "\\\\"))
            if not isinstance(json_response, list):
                raise BaseException(u"返回数据错误:%s" % json_response)
            if len(json_response) == 0:
                self.region_index += 1
                self.web_page = 0
                if self.region_index >= len(self.list_region):
                    logger.info(u"所有区域收集完成")
                    return
                region = self.list_region[self.region_index]
                logger.info(u"切换区域:%s" % region.get("region"))
            for json_data in json_response:
                if not json_data.get("location"):
                    break
                item = RealEstateItem()
                item["address"] = json_data.get("location")
                item["name"] = json_data.get("projectname")
                item["developer"] = json_data.get("enterprisename")
                item["count_house_number"] = 0
                item["web_source_id"] = WebSource.RealEstate
                item["web_real_estate_id"] = json_data.get("projectid")
                item["region_id"] = self.list_region[self.region_index].get("id")
                item["country_id"] = self.list_region[self.region_index].get("country_id")
                item["province_id"] = self.list_region[self.region_index].get("province_id")
                item["city_id"] = self.list_region[self.region_index].get("city_id")
                item["building_pre_sale_number"] = json_data.get("f_presale_cert")
                dict_building = dict()
                list_building_name = json_data.get("blockname").split(",")
                list_building_id = json_data.get("buildingid").split(",")
                # 当不等于的时候
                if len(list_building_name) != len(list_building_id):
                    logger.warning(u"数组长度不等:%s" % json_data)
                    list_building_name = list_building_name[:len(list_building_id)]
                len_building = len(list_building_name)
                for index_building in range(len_building):
                    dict_building[list_building_id[index_building]] = list_building_name[index_building]
                item["building_dict"] = dict_building
                logger.info("%s:%s" % (datetime.datetime.now(),
                                       json_data.get("location") + " " + json_data.get("projectname")))
                yield item
        except BaseException as e:
            if type(e) == CloseSpider:
                raise CloseSpider()
            logger.warning(e)
            self.is_change_proxy = True
        finally:
            yield self.create_request()

    def get_request_body(self):
        temp_dict = {"areaType": "", "entName": "", "location": "", "maxrow": (self.web_page + 1) * self.web_size,
                     "minrow": self.web_page * self.web_size,
                     "projectname": "", "siteid": self.list_region[self.region_index].get("web_site_id"), "useType": "1"}
        self.web_page += 1
        return json.dumps(temp_dict)

    def create_request(self, url=None, callback=None, method="POST"):
        if not url:
            url = self.base_url
        headers = {"Content-Type": "application/json"}
        return Request(url, callback=callback, method=method, body=self.get_request_body(), headers=headers,
                       dont_filter=True)


class BuildingSpider(scrapy.Spider):
    name = "building"
    is_change_proxy = True
    building_sql = """select * from building where status=1 limit 1"""
    base_url = u"http://www.cq315house.com/WebService/Service.asmx/GetRoomJson"
    building = None

    def start_requests(self):
        self.is_change_proxy = False
        return [self.create_request()]

    def parse(self, response):
        self.is_change_proxy = False
        try:
            if not response.text:
                raise BaseException(u"需要切换代理")
            if not is_json(response.text):
                raise BaseException(u"需要切换代理")
            list_json_response = json.loads(json.loads(response.text).get("d").replace("\\", "\\\\"))
            if not isinstance(list_json_response, list):
                raise BaseException(u"返回数据错误:%s" % list_json_response)
            origin_house_number = 0
            for item_json_data in list_json_response:
                unit = u"%s单元" % item_json_data.get("name")
                for item_room in item_json_data.get("rooms"):
                    if not item_room.get("location"):
                        continue
                    house = HouseItem()
                    house["door_number"] = item_room.get("flr") + "-"+ item_room.get("rn")
                    house["status"] = self.get_house_status(item_room.get("status"))
                    house["inside_area"] = item_room.get("iArea")
                    house["built_area"] = item_room.get("bArea")
                    house["attribute_house_type_id"] = get_house_attribute(HOUSE_TYPE, item_room.get("rType"))
                    house["inside_price"] = item_room.get("nsjg")
                    house["built_price"] = item_room.get("nsjmjg")
                    house["real_estate_id"] = self.building.get("real_estate_id")
                    house["building_id"] = self.building.get("id")
                    house["web_source_id"] = self.building.get("web_source_id")
                    house["unit"] = unit
                    house["web_house_id"] = item_room.get("id")
                    house["physical_layer"] = item_room.get("y")
                    if is_number(item_room.get("flr")):
                        house["nominal_layer"] = item_room.get("flr")
                    else:
                        house["nominal_layer"] = item_room.get("y")
                    house["house_number"] = item_room.get("x")
                    house["country_id"] = self.building.get("country_id")
                    house["province_id"] = self.building.get("province_id")
                    house["city_id"] = self.building.get("city_id")
                    house["region_id"] = self.building.get("region_id")
                    house["description"] = json.dumps(item_room)
                    house["fjh"] = item_room.get("fjh")
                    house["attribute_structure_id"] = get_house_attribute(HOUSE_STRUC, item_room.get("stru"))
                    logger.info("%s-%s" % (self.building.get("real_estate_name"), item_room.get("location")))
                    origin_house_number += 1
                    yield house
            self.handle_building(origin_house_number)
        except BaseException as e:
            if type(e) == CloseSpider:
                raise CloseSpider()
            logger.warning(e)
            self.is_change_proxy = True
        finally:
            yield self.create_request()

    def get_request_body(self):
        self.building = pool.find_one(self.building_sql)
        if not self.building:
            raise CloseSpider()
        temp_dict = {"buildingid": self.building.get("web_building_id")}
        return json.dumps(temp_dict)

    def create_request(self, url=None, callback=None, method="POST"):
        if not url:
            url = self.base_url
        body = self.get_request_body()
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/javascript, */*; q=0.01",
                   "Host": "www.cq315house.com", "Origin": "http://www.cq315house.com",
                   "Referer": "http://www.cq315house.com/HtmlPage/ShowRooms.html?buildingid=%s&block=%s" %
                              (self.building.get("web_building_id"), self.building.get("building_name"))}
        return Request(url, callback=callback, method=method, body=body, headers=headers)

    def get_house_status(self, status):
        list_color = [{"val": 8, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 1, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 64, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 2, "type": 0,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 256, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 3, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 1024, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 4, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 2048, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 5, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 16777216, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 5,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 131072, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 6,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 262146, "name": "未售", "ab": "可售", "bgColor": "#00ff00", "ftColor": "#000000", "priority": 7, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 262150, "name": "未售", "ab": "可售", "bgColor": "#00ff00", "ftColor": "#000000", "priority": 8, "type": 1,
            "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 524292, "name": "未售", "ab": "可售", "bgColor": "#00ff00", "ftColor": "#000000", "priority": 10,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 2097152, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 11,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 2621444, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 12,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 20176833, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 14,
            "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0}]
        for item_color in list_color:
            if item_color.get("val") & status == item_color.get("val"):
                return ColorStatus.get(item_color.get("bgColor"))
        return 6

    def handle_building(self, origin_house_number):
        select_sql = """select count(1) from house where building_id=%s"""
        result = pool.find_one(select_sql, [self.building.get("id")])
        if int(result.get("count(1)")) == origin_house_number:
            update_sql = """update building set status=2, updated=%s where status=1 and id=%s"""
            pool.commit(update_sql, [datetime.datetime.now(), self.building.get("id")])