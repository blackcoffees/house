# -*- coding:utf8 -*-
import json

import datetime
import re
import urllib2
from urllib import unquote

import pytesseract
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from base.BaseSpider import BaseSpider
from base.Model import RealEstate, Building, House
from db.DBUtil import update_building, get_real_estate_sale_status, get_building_sale_status
from util.CommonUtils import Region, send_request, WebSource, get_internet_validate_code

ColorStatus = {
    "#c0c0c0": 1, # 限制销售
    "#00ff00": 2, # 可售
    "#ff00ff": 3, # 预定
    "#ffff00": 4, # 已售
    "#ff0000": 5 # 已登记
}


class RealEstateSpider(BaseSpider):
    base_url = "http://www.cq315house.com/315web/webservice/GetMyData999.ashx?" \
               "projectname=&site=%s&kfs=&projectaddr=&pagesize=10&" \
               "pageindex=1&roomtype=住宅&buildarea="

    def work(self):
        for region in Region.all_region:
            url = self.base_url % region
            response = send_request(url)
            json_rep = json.loads(response.replace("'", '"'))
            for item in json_rep:
                # 楼盘
                real_estate = RealEstate()
                real_estate.building = item.get("ZPROJECT")
                real_estate.region = item.get("F_SITE")
                real_estate.address = item.get("F_ADDR")
                real_estate.developer = item.get("ENTERPRISENAME")
                real_estate.sale_building = item.get("F_BLOCK")
                real_estate.sale_count = item.get("NUM")
                real_estate.source_id = WebSource.RealEstate
                real_estate_id = real_estate.__add__()
                # 查询该楼盘出售情况，全部售完的就跳过
                real_estate_result = get_real_estate_sale_status(real_estate_id)
                if real_estate_result.get("house_total_count") != 0 and real_estate_result.get("house_sale_count") != 0\
                        and real_estate_result.get("house_total_count") == real_estate_result.get("house_sale_count"):
                    continue
                build_name = item.get("F_BLOCK").split(",")
                build_id = item.get("BUILDID").split(",")
                build_register = item.get("F_REGISTER_DATE").split(",")
                build_residence_count = item.get("BUILDZZNUM").split(",")
                build_none_residence_count = item.get("BUILDFZZNUM").split(",")
                # 该楼盘下所有大楼
                for index in range(len(build_id)):
                    sale_building = build_name[index].replace("'", "")
                    building = Building()
                    building.sale_building = sale_building
                    building.web_build_id = int(build_id[index])
                    building.register_time = datetime.datetime.strptime(build_register[index], "%Y-%m-%d")
                    building.sale_residence_count = int(build_residence_count[index])
                    building.sale_none_residence_count = int(build_none_residence_count[index])
                    building.source_id = WebSource.RealEstate
                    building.real_estate_id = int(real_estate_id)
                    building_id = building.__add__()
                    # 查询该大楼出售情况，全部售完的就跳过
                    building_sale_result = get_building_sale_status(building_id)
                    if building_sale_result.get("total_count") != 0 and building_sale_result.get("sale_count") != 0 \
                        and building_sale_result.get("total_count") == building_sale_result.get("sale_count"):
                        continue
                    building_url = "http://www.cq315house.com/315web/webservice/GetBuildingInfo.ashx?buildingId=%s" %\
                                   build_id[index]
                    response = send_request(building_url)
                    house_number = json.loads(response).get("presaleCert")
                    update_building(house_number, building_id)
                    # 一栋楼里面的所有房子
                    houses_url = "http://www.cq315house.com/315web/HtmlPage/ShowRoomsNew.aspx?block=%s&buildingid=%s" %\
                                 (sale_building.encode("utf8"), int(build_id[index]))
                    options = webdriver.FirefoxOptions()
                    options.add_argument("-headless")
                    driver = webdriver.Firefox(firefox_options=options)
                    driver.get(houses_url)
                    exit = False
                    # 循环加载，直到页面的ajax加载完成之后
                    while True:
                        try:
                            exit = WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located((By.ID, "_mybuilding")))
                            if exit:
                                break
                        except:
                            continue
                    if exit:
                        house_soup = BeautifulSoup(driver.page_source)
                        tbody = house_soup.find("table", attrs={"id": "_mybuilding"}).find("tbody")
                        trs = tbody.find_all("tr")
                        for tr in trs:
                            tds = tr.find_all("td", attrs={"objt": "tdclass"})
                            for td in tds:
                                # 单独每一套房子
                                status = td.find("font").attrs.get("color")
                                door_number = td.find("font").text
                                validate_url = "http://www.cq315house.com/315web/" + \
                                               td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                validate_driver = webdriver.Firefox()
                                while True:
                                    try:
                                        validate_driver.get(validate_url)
                                    except:
                                        continue
                                    # validate_soup = BeautifulSoup(validate_driver.page_source)
                                    # cookies = validate_driver.get_cookies()
                                    # cookies_str = ""
                                    # for key, cookie_item in cookies[0].items():
                                    #     cookies_str += str(key) + "=" + str(cookie_item) + ";"
                                    # validate_form = validate_soup.find("form", attrs={"id": "form1"})
                                    # validate_img_url = "http://www.cq315house.com/315web/YanZhengCode/" + \
                                    #                    validate_form.find("img").attrs.get("src")
                                    # validate_img_url = validate_form.find("img")
                                    # code = get_internet_validate_code(validate_img_url, cookies_str)
                                    validate_driver.save_screenshot("e:/spider_img/temp.png")
                                    code = get_internet_validate_code(validate_driver.find_element_by_tag_name("img"))
                                    if code == 0:
                                        continue
                                    # 发送验证码请求
                                    code_input = validate_driver.find_element_by_id("txtCode")
                                    code_input.send_keys(code)
                                    validate_driver.find_element_by_id("Button1").click()
                                    one_house_url = validate_driver.current_url
                                    if "bid" in one_house_url:
                                        # validate_driver.quit()
                                        # one_house_response = send_request(one_house_url, cookies=cookies)
                                        one_house_soup = BeautifulSoup(validate_driver.page_source, "html.parser")
                                        one_house_data = one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src")
                                        one_house_data = unquote(one_house_data).split(".ashx?")[1]
                                        if not one_house_data:
                                            continue
                                        if one_house_data and "undefined-undefined" in one_house_data:
                                            import time
                                            time.sleep(10)
                                            continue
                                        json_data = json.loads(one_house_data.split("text=")[1])
                                        house = House()
                                        house.door_number = json_data.get("flr") + "-" + json_data.get("x")
                                        house.status = json_data.get("S_ISONLINESIGN")
                                        house.inside_area = json_data.get("iArea")
                                        house.built_area = json_data.get("bArea")
                                        house.house_type = json_data.get("rType")
                                        house.inside_price = json_data.get("nsjg")
                                        house.built_price = json_data.get("nsjmjg")
                                        house.buliding_id = building_id
                                        house.real_estate_id = real_estate_id
                                        house.source_id = 1
                                        house.__add__()
                                        break
                        driver.quit()