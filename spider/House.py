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
    base_select_sql = """select * from house where status=6 limit 0, 1"""
    base_update_sql = """update house set status=%s, inside_area=%s, built_area=%s, house_type=%s, inside_price=%s, 
                        built_price=%s, updated=%s where id=%s"""

    def work(self):
        delete_logs()
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        web_driver_manager = WebDriverManager(1, "chrome", options)
        house_driver = web_driver_manager.get_web_driver(True)
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
                house_driver.save_screenshot(self.base_image_path + "temp.png")
                # 保存图片
                img = house_driver.find_element_by_tag_name("img")
                location_img_url = self.base_image_path + "temp.png"
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
                    image_recognition.save_success_image(self.base_image_path + "temp.png", expression)
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
                    if json_data.get("HX") == u"其他":
                        continue
                    house_status = chinese_status.get(json_data.get("FWZT"))
                    inside_area = json_data.get("TNMJ")
                    built_area = json_data.get("JZMJ")
                    house_type = json_data.get("HX")
                    inside_price = json_data.get("NSDJ_TN")
                    built_price = json_data.get("NSDJ_JM")
                    pool.commit(self.base_update_sql, [house_status, inside_area, built_area, house_type, inside_price,
                                                       built_price, datetime.datetime.now(), house.get("id")])
                    logger.info("套内单价：%s， 套内面积：%s" % (inside_price, inside_area))
            except BaseException as e:
                logger.error(e)
                web_driver_manager.destory_web_driver(house_driver.get_id())
                house_driver = web_driver_manager.get_web_driver(True)