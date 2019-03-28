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
    name = scrapy.Field()
    developer = scrapy.Field()
    count_house_number = scrapy.Field()
    web_source_id = scrapy.Field()
    web_real_estate_id = scrapy.Field()
    region_id = scrapy.Field()
    country_id = scrapy.Field()
    province_id = scrapy.Field()
    city_id = scrapy.Field()
    building_pre_sale_number = scrapy.Field()
    building_dict = scrapy.Field()


class HouseItem(scrapy.Item):
    door_number = scrapy.Field()
    status = scrapy.Field()
    inside_area = scrapy.Field()
    built_area = scrapy.Field()
    house_type = scrapy.Field()
    inside_price = scrapy.Field()
    built_price = scrapy.Field()
    real_estate_id = scrapy.Field()
    building_id = scrapy.Field()
    web_source_id = scrapy.Field()
    unit = scrapy.Field()
    web_house_id = scrapy.Field()
    physical_layer = scrapy.Field()
    nominal_layer = scrapy.Field()
    house_number = scrapy.Field()
    country_id = scrapy.Field()
    province_id = scrapy.Field()
    city_id = scrapy.Field()
    region_id = scrapy.Field()
    description = scrapy.Field()
    fjh = scrapy.Field()
    structure = scrapy.Field()