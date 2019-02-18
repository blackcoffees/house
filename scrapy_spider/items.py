# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapySpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class RealEstateItem(scrapy.Item):
    address = scrapy.Field()
    region = scrapy.Field()
    name = scrapy.Field()
    developer = scrapy.Field()
    sale_building = scrapy.Field()
    source_id = scrapy.Field()
    sale_count = scrapy.Field()
    building_sale_buildings = scrapy.Field()
    building_sale_residence_counts = scrapy.Field()
    building_sale_none_residence_counts = scrapy.Field()
    building_web_build_ids = scrapy.Field()
    building_register_times = scrapy.Field()
    web_real_estate_id = scrapy.Field()


class HouseItem(scrapy.Item):
    door_number = scrapy.Field()
    status = scrapy.Field()
    inside_area = scrapy.Field()
    built_area = scrapy.Field()
    inside_price = scrapy.Field()
    built_price = scrapy.Field()
    real_estate_id = scrapy.Field()
    building_id = scrapy.Field()
    source_id = scrapy.Field()
    house_type = scrapy.Field()
    unit = scrapy.Field()
    web_house_id = scrapy.Field()