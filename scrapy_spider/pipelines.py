# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from base.Model import RealEstate, Building
from db.PoolDB import pool


class RealEstatePipeline(object):
    def process_item(self, item, spider):
        real_estate = RealEstate()
        real_estate.address = item["address"]
        real_estate.region = item["region"]
        real_estate.building = item["building"]
        real_estate.developer = item["developer"]
        real_estate.sale_building = item["sale_building"]
        real_estate.source_id = item["source_id"]
        real_estate.sale_count = item["sale_count"]
        real_estate_id = real_estate.__add__()
        list_building = item["building_sale_buildings"].split(",")
        list_sale_residence_count = item["building_sale_residence_counts"].split(",")
        list_sale_none_residence_count = item["building_sale_none_residence_counts"].split(",")
        list_web_build_id = item["building_web_build_ids"].split(",")
        list_register_time = item["building_register_times"].split(",")
        for building_index in range(len(list_building)):
            building = Building()
            building.building_name = real_estate.building
            building.sale_building = list_building[building_index]
            building.sale_residence_count = list_sale_residence_count[building_index]
            building.sale_none_residence_count = list_sale_none_residence_count[building_index]
            building.real_estate_id = real_estate_id
            building.source_id = real_estate.source_id
            building.web_build_id = list_web_build_id[building_index]
            if list_register_time[building_index]:
                building.register_time = list_register_time[building_index]
            building.__add__()