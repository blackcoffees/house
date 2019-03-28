# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime

from base.Model import RealEstate, Building, House
from db.PoolDB import pool


class RealEstatePipeline(object):
    def process_item(self, item, spider):
        if spider.name == "real_estate":
            real_estate = RealEstate()
            real_estate.address = item["address"]
            real_estate.name = item["name"]
            real_estate.developer = item["developer"]
            real_estate.count_house_number = item["count_house_number"]
            real_estate.web_source_id = item["web_source_id"]
            real_estate.web_real_estate_id = item["web_real_estate_id"]
            real_estate.region_id = item["region_id"]
            real_estate.country_id = item["country_id"]
            real_estate.province_id = item["province_id"]
            real_estate.city_id = item["city_id"]
            real_estate_id = real_estate.__add__()
            if not real_estate_id:
                raise BaseException("real estate id not found")
            for building_id, building_name in item["building_dict"].items():
                building = Building()
                building.pre_sale_number = item["building_pre_sale_number"]
                building.real_estate_name = real_estate.name
                building.building_name = building_name
                building.count_residence_number = 0
                building.real_estate_id = real_estate_id
                building.web_source_id = real_estate.web_source_id
                building.web_building_id = building_id
                building.count_house_number = 0
                building.country_id = real_estate.country_id
                building.province_id = real_estate.province_id
                building.city_id = real_estate.city_id
                building.region_id = real_estate.region_id
                building.__add__()
        elif spider.name == "building":
            house = House()
            house.door_number = item["door_number"]
            house.status = item["status"]
            house.inside_area = item["inside_area"]
            house.built_area = item["built_area"]
            house.attribute_house_type_id = item["attribute_house_type_id"]
            house.inside_price = item["inside_price"]
            house.built_price = item["built_price"]
            house.real_estate_id = item["real_estate_id"]
            house.building_id = item["building_id"]
            house.unit = item["unit"]
            house.web_source_id = item["web_source_id"]
            house.web_house_id = item["web_house_id"]
            house.physical_layer = item["physical_layer"]
            house.nominal_layer = item["nominal_layer"]
            house.house_number = item["house_number"]
            house.country_id = item["country_id"]
            house.province_id = item["province_id"]
            house.city_id = item["city_id"]
            house.region_id = item["region_id"]
            house.fjh = item["fjh"]
            house.attribute_structure_id = item["attribute_structure_id"]
            house.description = item["description"]
            house.__add__()