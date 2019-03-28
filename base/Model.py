# -*- coding: utf-8 -*-
import datetime

from db import DBUtil
from util.CommonUtils import get_fields


class BaseModel(object):
    def __init__(self):
        pass

    def __add__(self):
        pass

    def __delete__(self):
        pass


class RealEstate(BaseModel):
    address = None
    name = None
    created = 0
    updated = None
    count_house_number = 0
    web_source_id = 0
    web_real_estate_id = 0
    region_id = 0
    country_id = 0
    province_id = 0
    city_id = 0

    def __add__(self):
        real_estate_id = self.__find__()
        if real_estate_id:
            return real_estate_id
        self.created = datetime.datetime.now()
        list_field = get_fields(self)
        str_field = ",".join(list_field)
        list_param = list()
        list_value = list()
        for field in list_field:
            list_param.append(getattr(self, field))
            list_value.append("%s")
        sql = """ insert into real_estate (""" + str_field + """) values (%s)""" % ",".join(list_value)
        return DBUtil.save(sql, param=list_param)

    def __find__(self):
        sql = """select id from real_estate where address=%s and name=%s """
        param = [self.address, self.name]
        result = DBUtil.get(sql, param)
        if result:
            return result.get("id")
        else:
            False


class Building(BaseModel):
    pre_sale_number = None
    real_estate_name = None
    building_name = None
    count_residence_number = 0
    real_estate_id = 0
    web_source_id = 0
    web_building_id = 0
    count_house_number = 0
    country_id = 0
    province_id = 0
    city_id = 0
    region_id = 0

    def __add__(self):
        id = self.__get__()
        if id:
            return id
        self.created = datetime.datetime.now()
        list_field = get_fields(self)
        str_field = ",".join(list_field)
        list_param = list()
        list_value = list()
        for field in list_field:
            list_param.append(getattr(self, field))
            list_value.append("%s")
        sql = """insert into building(""" + str_field + """) values (%s)""" % ",".join(list_value)
        return DBUtil.save(sql, list_param)

    def __get__(self):
        sql = """select id from building where real_estate_id=%s and building_name=%s"""
        param = [self.real_estate_id, self.building_name]
        result = DBUtil.get(sql, param)
        if result:
            return result.get("id")
        else:
            return False


class House(BaseModel):
    door_number = None
    status = 0
    inside_area = 0
    built_area = 0
    house_type = None
    inside_price = 0
    built_price = 0
    real_estate_id = 0
    building_id = 0
    web_source_id = 0
    unit = None
    web_house_id = 0
    physical_layer = 0
    nominal_layer = 0
    house_number = 0
    country_id = 0
    province_id = 0
    city_id = 0
    region_id = 0
    fjh = None
    structure = None
    description = None

    def __add__(self):
        id = self.__get__()
        if id:
            return id
        self.created = datetime.datetime.now()
        list_field = get_fields(self)
        str_field = ",".join(list_field)
        list_param = list()
        list_value = list()
        for field in list_field:
            list_param.append(getattr(self, field))
            list_value.append("%s")
        sql = """insert into house(""" + str_field + """) VALUES (%s)""" % ",".join(list_value)
        return DBUtil.save(sql, list_param)

    def __get__(self):
        sql = """select id from house where door_number=%s and building_id=%s and real_estate_id=%s and unit=%s"""
        param = [self.door_number, self.building_id, self.real_estate_id, self.unit]
        result = DBUtil.get(sql, param)
        if result:
            return result.get("id")
        else:
            False