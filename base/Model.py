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
    region = None
    building = None
    developer = None
    sale_building = None
    source_id = 0
    created = datetime.datetime.now()
    updated = None

    def __add__(self):
        real_estate_id = self.__find__()
        if real_estate_id:
            return real_estate_id
        fields = get_fields(self)
        fields = ",".join(fields)
        values = list()
        for field in fields.split(","):
            values.append(getattr(self, field))
        sql = """ insert into real_estate (""" + fields + """) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        return DBUtil.save(sql, param=values)

    def __find__(self):
        sql = """select id from real_estate where address=%s and building=%s """
        param = [self.address, self.building]
        result = DBUtil.get(sql, param)
        if result:
            return result.get("id")
        else:
            False


class Building(BaseModel):
    house_number = None
    building_name = None
    sale_building = None
    sale_residence_count = 0
    sale_none_residence_count = 0
    real_estate_id = 0
    source_id = 0
    created = datetime.datetime.now()
    updated = None
    web_build_id = None
    register_time = None

    def __add__(self):
        id = self.__get__()
        if id:
            return id
        sql = """insert into building(web_build_id, register_time, created, real_estate_id, sale_residence_count, 
                  sale_none_residence_count , source_id, sale_building) values (%s, %s, %s, %s, %s, %s, %s, %s)"""
        param = [self.web_build_id, self.register_time, self.created, self.real_estate_id, self.sale_residence_count,
                 self.sale_none_residence_count, self.source_id, self.sale_building]
        return DBUtil.save(sql, param)

    def __get__(self):
        sql = """select id from building where source_id=%s and real_estate_id=%s and sale_building=%s"""
        param = [self.source_id, self.real_estate_id, self.sale_building]
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
    buliding_id =0
    source_id = 0
    created = datetime.datetime.now()
    unit = None

    def __add__(self):
        id = self.__get__()
        if id:
            return id
        sql = """insert into house(door_number, status, inside_area, built_area, house_type, inside_price, built_price,
                  real_estate_id, buliding_id, source_id, created, unit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        param = [self.door_number, self.status, self.inside_area, self.built_area, self.house_type, self.inside_price,
                 self.built_price, self.real_estate_id, self.buliding_id, self.source_id, self.created, self.unit]
        return DBUtil.save(sql, param)

    def __get__(self):
        sql = """select id from house where source_id=%s and buliding_id=%s and real_estate_id=%s and door_number=%s and unit=%s"""
        param = [self.source_id, self.buliding_id, self.real_estate_id, self.door_number, self.unit]
        result = DBUtil.get(sql, param)
        if result:
            old_status = DBUtil.get_house_status(self.door_number, self.real_estate_id, self.buliding_id, self.unit)
            if not old_status == self.status:
                DBUtil.update_house_status(result.get("id"), self.status)
            return result.get("id")
        else:
            False