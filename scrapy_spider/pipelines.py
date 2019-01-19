# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from base.Model import RealEstate
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
        real_estate.__add__()
