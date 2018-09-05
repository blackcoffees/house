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
    sale_count = 0
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
        sql = """ insert into real_estate (""" + fields + """) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
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
        sql = """select id from building where source_id=%s and real_estate_id=%s"""
        param = [self.source_id, self.real_estate_id]
        result = DBUtil.get(sql, param)
        if result:
            return result.get("id")
        else:
            return False