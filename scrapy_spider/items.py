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
    building = scrapy.Field()
    developer = scrapy.Field()
    sale_building = scrapy.Field()
    source_id = scrapy.Field()
    sale_count = scrapy.Field()
    building_sale_buildings = scrapy.Field()
    building_sale_residence_counts = scrapy.Field()
    building_sale_none_residence_counts = scrapy.Field()
    building_web_build_ids = scrapy.Field()
    building_register_times = scrapy.Field()