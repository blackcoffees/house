# -*- coding:utf8 -*-
from db.PoolDB import pool


def get_switch_activity(switch_code):
    sql = """select status from sys_function_switch where switch_code=%s"""
    result = pool.find_one(sql, [switch_code])
    return result.get("status")
