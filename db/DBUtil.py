# -*- coding: utf-8 -*-
from db.PoolDB import pool

# ---------------------------  新增 start ---------------------------


def save(sql, param):
    return pool.commit(sql, param)
# ---------------------------  新增 end ---------------------------


# ---------------------------  查询 start ---------------------------


def get(sql, param):
    return pool.find_one(sql, param)
# ---------------------------  查询 end ---------------------------


# ---------------------------  更新 start ---------------------------


def update_building(house_number, id):
    sql = """update building set house_number=%s where id=%s"""
    param = [house_number, id]
    pool.commit(sql, param)
# ---------------------------  更新 end ---------------------------