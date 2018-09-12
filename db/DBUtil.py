# -*- coding: utf-8 -*-
import datetime

from db.PoolDB import pool

# ---------------------------  新增 start ---------------------------


def save(sql, param):
    return pool.commit(sql, param)
# ---------------------------  新增 end ---------------------------


# ---------------------------  查询 start ---------------------------


def get(sql, param):
    return pool.find_one(sql, param)


def get_real_estate_sale_status(real_estate_id):
    """
    查询该楼盘出售情况
    :param param:
    :return:
    """
    sql = """select house_total_count, house_sale_count from real_estate where id = %s"""
    param = [real_estate_id]
    return pool.find_one(sql, param)


def get_building_sale_status(building_id):
    """
    查询该大楼的出售情况
    :param building_id:
    :return:
    """
    sql = """select total_count, sale_count from building where id=%s"""
    param = [building_id]
    return pool.find_one(sql, param)


def get_house_status(house_id):
    sql = """select status from house where id=%s"""
    param = [house_id]
    return pool.find_one(sql, param)
# ---------------------------  查询 end ---------------------------


# ---------------------------  更新 start ---------------------------


def update_building(house_number, id):
    sql = """update building set house_number=%s where id=%s"""
    param = [house_number, id]
    pool.commit(sql, param)


def update_house_status(house_id, status):
    sql = """update house set status=%s, updated=%s where id=%s"""
    param = [status, datetime.datetime.now(), house_id]
    pool.commit(sql, param)
# ---------------------------  更新 end ---------------------------