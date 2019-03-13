# -*- coding: utf-8 -*-
import json
import time

import os
from urllib import unquote

import datetime
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver

from base.BaseSpider import BaseSpider
from base.Model import House
from db.PoolDB import pool
from util.CommonUtils import logger, delete_logs, chinese_status
from util.ImageRecognitionUtil import ImageRecognition
from util.WebDriverUtil import WebDriverManager


class HouseSpider(BaseSpider):
    base_image_path = os.path.dirname(os.getcwd()) + "\\image\\"
    base_house_url = "http://www.cq315house.com/315web/YanZhengCode/YanZhengPage.aspx?fid=%s"
    base_select_sql = """select * from house where status=6 order by buliding_id, real_estate_id limit %s, 1 """
    base_update_sql = """update house set status=%s, inside_area=%s, built_area=%s, house_type=%s, inside_price=%s, 
                        built_price=%s, updated=%s where id=%s"""
    thread_no = None

    def __init__(self, thread_no=0):
        super(HouseSpider, self).__init__()
        self.thread_no = thread_no
        self.base_select_sql = self.base_select_sql % self.thread_no
        self.save_image_url = self.base_image_path + ("thread_%s.png" % self.thread_no)

    def work(self):
        delete_logs()
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        web_driver_manager = WebDriverManager(1, "chrome", options)
        house_driver = web_driver_manager.get_web_driver(True)
        # 统计数据
        buliding_id = 0
        real_estate_id = 0
        while True:
            try:
                house = pool.find_one(self.base_select_sql)
                if not house:
                    logger.info(u"数据收集完成")
                    break
                if not house.get("web_house_id"):
                    continue
                house_driver.send_url((self.base_house_url % house.get("web_house_id")))
                # 截图整个网页
                house_driver.save_screenshot(self.save_image_url)
                # 保存图片
                img = house_driver.find_element_by_tag_name("img")
                location_img_url = self.save_image_url
                left = img.location.get("x")
                top = img.location.get("y")
                width = left + img.size.get("width")
                height = top + img.size.get("height")
                image = Image.open(location_img_url).crop((left, top, width, height))
                image.save(location_img_url)
                # 防止图片没有保存下来
                time.sleep(3)
                # 识别图片
                image_recognition = ImageRecognition(self.base_image_path)
                expression, int_code = image_recognition.get_expression_code()
                # 发送验证码请求
                code_input = house_driver.find_element_by_id("txtCode")
                code_input.send_keys(int_code)
                house_driver.find_element_by_id("Button1").click()
                one_house_url = house_driver.current_url
                if "bid" in one_house_url:
                    # 保存成功的图片
                    image_recognition.save_success_image(self.save_image_url, expression)
                    # 收集数据
                    one_house_soup = BeautifulSoup(house_driver.page_source, "html.parser")
                    if not one_house_soup.find("img"):
                        raise BaseException(u"无法获取房子数据")
                    one_house_data = unquote(
                        one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src").split("text=")[1].replace(
                            "%u", "\\u").decode("unicode-escape"))
                    if not one_house_data:
                        raise BaseException(u"无法获取房子数据")
                    if one_house_data and "undefined-undefined" in one_house_data:
                        raise BaseException(u"无法获取房子数据")
                    json_data = json.loads(one_house_data)
                    # if json_data.get("HX") == u"其他":
                    #     continue
                    house_status = chinese_status.get(json_data.get("FWZT")) if chinese_status.get(json_data.get("FWZT")) else 7
                    inside_area = json_data.get("TNMJ")
                    built_area = json_data.get("JZMJ")
                    house_type = json_data.get("HX")
                    inside_price = json_data.get("NSDJ_TN")
                    built_price = json_data.get("NSDJ_JM")
                    pool.commit(self.base_update_sql, [house_status, inside_area, built_area, house_type, inside_price,
                                                       built_price, datetime.datetime.now(), house.get("id")])
                    logger.info(u"thread:%s， %s：套内单价：%s， 套内面积：%s" %
                                (self.thread_no, house.get("door_number"), inside_price, inside_area))
                    # 统计数据
                    # 不同大楼,此时统计该栋楼的数据
                    if buliding_id and buliding_id != house.get("buliding_id"):
                        sql_count_house = """select * from
                                      (select count(1) as sale_number from house where buliding_id=%s and status=2) as a, 
                                      (select count(1) as total_number from house where buliding_id=%s) as b, 
                                      (select count(1) as sold_number from house where `status` in (3,4,5) and buliding_id=%s) as c"""
                        result_count_house = pool.find_one(sql_count_house, [buliding_id, buliding_id, buliding_id], sql_analysis=False)
                        sql_update_buliding = """update building set sale_residence_count=%s, total_count=%s, sale_count=%s, updated=%s where id=%s"""
                        pool.commit(sql_update_buliding, [result_count_house[0], result_count_house[1], result_count_house[2], datetime.datetime.now(), buliding_id])
                        buliding_id = house.get("buliding_id")
                    # 不同楼盘，此时统计楼盘数据
                    if real_estate_id and real_estate_id != house.get("real_estate_id"):
                        sql_count_buliding = """select sum(sale_residence_count), sum(total_count), sum(sale_count) from building where real_estate_id=%s"""
                        result_count_buliding = pool.find_one(sql_count_buliding, [real_estate_id])
                        sql_update_real_estate = """update real_estate set sale_count=%s, house_total_count=%s, house_sell_out_count=%s, updated=%s where id=%s"""
                        pool.commit(sql_update_real_estate, [result_count_buliding.get("sum(sale_residence_count)"),
                                                             result_count_buliding.get("sum(total_count)"),
                                                             result_count_buliding.get("sum(sale_count)"),
                                                             datetime.datetime.now(), real_estate_id])
                        real_estate_id = house.get("real_estate_id")
                    if not buliding_id:
                        buliding_id = house.get("buliding_id")
                        real_estate_id = house.get("real_estate_id")
            except BaseException as e:
                logger.error(e)
                try:
                    web_driver_manager.destory_web_driver(house_driver.get_id())
                except BaseException as e2:
                    print e2
                    command = u"taskkill /F /IM chromedriver.exe"
                    os.system(command)
                house_driver = web_driver_manager.get_web_driver(True)

