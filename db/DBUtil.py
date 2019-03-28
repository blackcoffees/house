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


def get_real_estate_sale_status(real_estate_id=None, real_estate_name=None):
    """
    查询该楼盘出售情况
    :param param:
    :return:
    """
    if real_estate_id and real_estate_name:
        sql = """select house_total_count, house_sell_out_count from real_estate where id = %s and name=%s"""
        param = [real_estate_id, real_estate_name]
    elif real_estate_name:
        sql = """select house_total_count, house_sell_out_count from real_estate where  name=%s"""
        param = [real_estate_name]
    elif real_estate_id:
        sql = """select house_total_count, house_sell_out_count from real_estate where id = %s"""
        param = [real_estate_id]
    else:
        return False
    return pool.find_one(sql, param)


def get_real_estate(real_estate_name, region):
    sql = """select id, house_total_count, house_sell_out_count from real_estate where name=%s and region=%s"""
    param = [real_estate_name, region]
    return pool.find_one(sql, param)


def get_building_sale_status(sale_building, real_estate_id):
    """
    查询该大楼的出售情况
    :param building_id:
    :return:
    """
    sql = """select total_count, sale_count, id from building where sale_building=%s and real_estate_id=%s"""
    param = [sale_building, real_estate_id]
    return pool.find_one(sql, param)


def get_building(building_id=None):
    """

    :param building_id:
    :return:
    """
    sql = """select * from building where id=%s"""
    param = [building_id]
    return pool.find_one(sql, param)


def get_house_status(door_number, real_estate_id, buliding_id, house_unit):
    """
    查询房间出售情况
    :param house_id:
    :return:
    """
    sql = """select status, id, web_house_id from house where door_number=%s and real_estate_id=%s and buliding_id=%s and unit=%s"""
    param = [door_number, real_estate_id, buliding_id, house_unit]
    return pool.find_one(sql, param)


def get_real_estate_statictics_data(real_estate_id):
    sql = """select sum(total_count), sum(sale_count) from building where real_estate_id=%s"""
    param = [real_estate_id]
    return pool.find_one(sql, param)


def get_building_statictics_data(buliding_id, real_estate_id):
    sql = """select total_count, sale_count from (select count(id) as total_count from house where buliding_id=%s and real_estate_id=%s) as a, 
            (SELECT count(id) as sale_count from house where `status`=4 and buliding_id=%s and real_estate_id=%s) as b"""
    param = [buliding_id, real_estate_id, buliding_id, real_estate_id]
    return pool.find_one(sql, param)


def get_all_region():
    sql = """select region.id as id,region, web_region.web_region_id as web_site_id, city_id, province_id, country_id
            from region,web_region where status=1 and country_id=1 
            and province_id=1 and city_id=1 and web_region.region_id=region.id order by sort desc"""
    region_list = pool.find(sql)
    if region_list:
        return region_list
    else:
        return list()


# ---------------------------  查询 end ---------------------------


# ---------------------------  更新 start ---------------------------


def update_building(pre_sale_number, id):
    """
    更改大楼预售许可证
    :param pre_sale_number:
    :param id:
    :return:
    """
    find_sql = """select * from building where id=%s"""
    result_find = pool.find_one(find_sql, [id])
    if result_find.get("per_sale_number"):
        return
    sql = """update building set pre_sale_number=%s where id=%s"""
    param = [pre_sale_number, id]
    pool.commit(sql, param)


def update_house_status(house_id, status):
    """
    更改房间出售情况
    :param house_id:
    :param status:
    :return:
    """
    sql = """update house set status=%s, updated=%s where id=%s"""
    param = [status, datetime.datetime.now(), house_id]
    pool.commit(sql, param)


def update_real_estate_count(real_estate_id, house_total_count, house_sell_out_count):
    """
    更改楼盘房子总数量，出售总数量
    :param real_estate_id:
    :param house_total_count:
    :param house_sell_out_count:
    :return:
    """
    sql = """update real_estate set house_total_count=%s, house_sell_out_count=%s, updated=%s where id=%s"""
    param = [house_total_count, house_sell_out_count, datetime.datetime.now(), real_estate_id]
    pool.commit(sql, param)


def update_building_count(building_id, total_count, sale_count):
    """
    更改大楼房子总数量，出售总数量
    :param building_id:
    :param total_count:
    :param sale_count:
    :return:
    """
    sql = """update building set total_count=%s, sale_count=%s, updated=%s where id=%s"""
    param = [total_count, sale_count, datetime.datetime.now(), building_id]
    pool.commit(sql, param)


def update_region(region_id, now_page):
    sql = """update region set now_page=%s, updated=%s where id=%s"""
    param = [now_page, datetime.datetime.now(), region_id]
    pool.commit(sql, param)


def update_web_house_id(web_house_id, id):
    """
    修改房子网页id
    :param web_house_id:
    :param id:
    :return:
    """
    sql = """update house set web_house_id=%s, updated=%s where id=%s"""
    pool.commit(sql, [web_house_id, datetime.datetime.now(), id])

# ---------------------------  更新 end ---------------------------