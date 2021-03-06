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
from util.SwitchUtil import get_switch_activity
reload(sys)
sys.setdefaultencoding( "utf-8" )


class RealEstateSpider(scrapy.Spider):
    name = 'real_estate'
    proxy_switch_code = "proxy_real_estate"
    is_change_proxy = False
    region_index = 0
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
                print "asdfsadfsadf"
        except BaseException as e:
            if type(e) == CloseSpider:
                logger.warning(u"爬虫停止")
                raise CloseSpider()
            logger.warning(e)
            self.is_change_proxy = True
        finally:
            yield self.create_request()

    def get_request_body(self):
        if self.region_index > len(self.list_region):
            logger.warning(u"爬虫停止")
            raise CloseSpider(u"收集完成")
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
    proxy_switch_code = "proxy_building"
    is_change_proxy = False
    building_sql = """select * from building where status in (1,4) limit %s, 1"""
    base_url = u"http://www.cq315house.com/WebService/Service.asmx/GetRoomJson"
    building = None
    now_index = 0
    total_building = 0

    def start_requests(self):
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
                    house["door_number"] = item_room.get("flr") + "-" + item_room.get("rn")
                    house["status"] = self.get_house_status(BuildingSpider, item_room.get("status"))
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
                    self.total_building = self.get_total_building()
                    yield house
            self.handle_building(origin_house_number)
        except BaseException as e:
            if type(e) == CloseSpider:
                logger.warning(u"爬虫停止")
                raise CloseSpider()
            logger.warning(e)
            self.is_change_proxy = True
        finally:
            yield self.create_request()

    def get_request_body(self):
        now_total_building = self.get_total_building()
        if now_total_building == self.total_building:
            self.now_index += 1
        self.building = pool.find_one(self.building_sql, [self.now_index])
        if not self.building:
            logger.warning(u"爬虫停止")
            raise CloseSpider()
        temp_dict = {"buildingid": self.building.get("web_building_id")}
        return json.dumps(temp_dict)

    def get_total_building(self):
        sql = """select count(1) from building where status in (1,4)"""
        result = pool.find_one(sql)
        if result:
            return result.get("count(1)")
        return 0

    def create_request(self, url=None, callback=None, method="POST"):
        if not url:
            url = self.base_url
        body = self.get_request_body()
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/javascript, */*; q=0.01",
                   "Host": "www.cq315house.com", "Origin": "http://www.cq315house.com",
                   "Referer": "http://www.cq315house.com/HtmlPage/ShowRooms.html?buildingid=%s&block=%s" %
                              (self.building.get("web_building_id"), self.building.get("building_name"))}
        if not callback:
            callback = self.parse
        return Request(url, callback=callback, method=method, body=body, headers=headers, dont_filter=True)

    @staticmethod
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
        update_status = 4
        if int(result.get("count(1)")) == origin_house_number:
            update_status = 2
        update_sql = """update building set status=%s, updated=%s where status=1 and id=%s"""
        pool.commit(update_sql, [update_status, datetime.datetime.now(), self.building.get("id")])


# class HouseSpider(scrapy.Spider):
#
#     name = "house"
#     base_url = "http://www.cq315house.com/WebService/Service.asmx/GetRoomInfo"
#     total_house = 0
#     now_index = 0
#     house = None
#     is_change_proxy = get_switch_activity("proxy_house")
#
#     def start_requests(self):
#         self.total_house = self.get_total_house()
#         return [self.get_request()]
#
#     def parse(self, response):
#         try:
#             if not response.text:
#                 raise BaseException(u"没有获取到数据")
#             if not is_json(response.text):
#                 raise BaseException(u"没有获取到数据")
#             json_response = json.loads(response.text)
#             room = json.loads(json_response.get("d"))
#             now_status = BuildingSpider.get_house_status(BuildingSpider, room.get("status"))
#             if now_status != int(self.house.get("status")):
#                 new_description = json.dumps(dict(json.loads(self.house.get("description")), **room))
#                 sql = """update house set status=%s, updated=%s, description=%s where id=%s"""
#                 pool.commit(sql, [now_status, datetime.datetime.now(), new_description, self.house.get("id")])
#                 logger.info(u"修改房屋状态:%s" % room.get("location"))
#                 self.total_house = self.get_total_house()
#             self.is_change_proxy = False
#         except BaseException as e:
#             logger.error(e)
#             if e.message:
#                 logger.error(e.message)
#             self.is_change_proxy = True
#         finally:
#             yield self.get_request()
#
#     def get_total_house(self):
#         sql = """select count(1) from house where status in (2,6)"""
#         result = pool.find_one(sql)
#         if result:
#             return result.get("count(1)")
#         return 0
#
#     def get_body(self):
#         now_total_house = self.get_total_house()
#         if now_total_house == self.total_house:
#             self.now_index += 1
#         sql = """select * from house where status in (2,6) limit %s,1"""
#         self.house = pool.find_one(sql, [self.now_index])
#         if self.house:
#             return json.dumps({"roomId": self.house.get("web_house_id")})
#         raise CloseSpider()
#
#     def get_request(self):
#         header = {
#             "Content-Type": "application/json",
#         }
#         request = Request(self.base_url, body=self.get_body(), headers=header, method="POST", dont_filter=True)
#         return request


class HouseSpider(scrapy.Spider):
    name = "house"
    proxy_switch_code = "proxy_house"
    is_change_proxy = False
    base_sql = """select * from building where id in (select building_id from house where status in (2,6) GROUP BY building_id) limit %s,1;"""
    all_houses_sql = """select * from house where building_id=%s"""
    base_url = u"http://www.cq315house.com/WebService/Service.asmx/GetRoomJson"
    now_db_index = 0
    dict_all_houses = dict()
    building = None
    list_house_key = list()

    def start_requests(self):
        return [self.create_request()]

    def parse(self, response):
        try:
            if not response.text:
                raise BaseException(u"需要切换代理")
            if not is_json(response.text):
                raise BaseException(u"需要切换代理")
            self.is_change_proxy = False
            if "GetRoomJson" in response._url:
                list_json_response = json.loads(json.loads(response.text).get("d").replace("\\", "\\\\"))
                if not isinstance(list_json_response, list):
                    raise BaseException(u"返回数据错误:%s" % list_json_response)
                for item_json_data in list_json_response:
                    for item_room in item_json_data.get("rooms"):
                        if not item_room.get("location"):
                            continue
                        status = self.get_house_status(BuildingSpider, item_room.get("status"))
                        key = item_room.get("id")
                        if int(self.dict_all_houses.get(key).get("status")) != status:
                            self.dict_all_houses.get(key)["status"] = status
                            self.list_house_key.append(key)
                            yield self.get_house_request()
                if len(self.list_house_key) == 0:
                    yield self.create_request()
            elif "GetRoomInfo" in response._url:
                json_response = json.loads(response.text)
                room = json.loads(json_response.get("d"))
                key = room.get("id")
                new_description = json.dumps(dict(json.loads(self.dict_all_houses.get(key).get("description")), **room))
                sql = """update house set status=%s, updated=%s, description=%s where id=%s"""
                pool.commit(sql, [self.dict_all_houses.get(key).get("status"), datetime.datetime.now(), new_description,
                                  self.dict_all_houses.get(key).get("id")])
                logger.info(u"修改房屋状态:%s" % room.get("location"))
                self.list_house_key.remove(key)
                if len(self.list_house_key) == 0:
                    yield self.create_request()
        except BaseException as e:
            if type(e) == CloseSpider:
                logger.warning(u"爬虫停止")
                raise CloseSpider()
            logger.warning(e)
            if e.message:
                logger.warning(e.message)
            self.is_change_proxy = True
            if "GetRoomJson" in response.request.url or "GetRoomInfo" in response.request.url:
                yield response.request
            else:
                yield self.create_request()

    def get_request_body(self):
        self.building = pool.find_one(self.base_sql, [self.now_db_index])
        if not self.building:
            logger.warning(u"爬虫停止")
            raise CloseSpider()
        self.now_db_index += 1
        list_all_houses = pool.find(self.all_houses_sql, [self.building.get("id")])
        self.dict_all_houses = dict()
        for item_house in list_all_houses:
            self.dict_all_houses[item_house.get("web_house_id")] = item_house
        temp_dict = {"buildingid": self.building.get("web_building_id")}
        return json.dumps(temp_dict)

    def create_request(self, url=None, callback=None, method="POST", body=None, headers=None):
        if not url:
            url = self.base_url
        if not body:
            body = self.get_request_body()
        if not headers:
            headers = {"Content-Type": "application/json", "Accept": "application/json, text/javascript, */*; q=0.01",
                       "Host": "www.cq315house.com", "Origin": "http://www.cq315house.com",
                       "Referer": "http://www.cq315house.com/HtmlPage/ShowRooms.html?buildingid=%s&block=%s" %
                                  (self.building.get("web_building_id"), self.building.get("building_name")),
                       "_body": body}
        if not callback:
            callback = self.parse
        return Request(url, callback=callback, method=method, body=body, headers=headers, dont_filter=True)

    def get_house_request(self):
        header = {
            "Content-Type": "application/json",
        }
        request = Request("http://www.cq315house.com/WebService/Service.asmx/GetRoomInfo",
                          body=json.dumps({"roomId": self.dict_all_houses.get(self.list_house_key[len(self.list_house_key)-1]).get("web_house_id")}),
                          headers=header, method="POST", dont_filter=True)
        return request

    @staticmethod
    def get_house_status(self, status):
        list_color = [
            {"val": 8, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 1, "type": 1,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 64, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 2,
             "type": 0,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 256, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 3,
             "type": 1,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 1024, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 4,
             "type": 1,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 2048, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 5,
             "type": 1,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 16777216, "name": "已售", "ab": "已售", "bgColor": "#ff00ff", "ftColor": "#000000", "priority": 5,
             "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 131072, "name": "不可售", "ab": "不可售", "bgColor": "#ffff00", "ftColor": "#000000", "priority": 6,
             "type": 1, "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 262146, "name": "未售", "ab": "可售", "bgColor": "#00ff00", "ftColor": "#000000", "priority": 7,
             "type": 1,
             "alarmType": 1, "showType": 0, "parentType": 0, "treeLevel": 0},
            {"val": 262150, "name": "未售", "ab": "可售", "bgColor": "#00ff00", "ftColor": "#000000", "priority": 8,
             "type": 1,
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