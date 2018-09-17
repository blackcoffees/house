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
from util.CommonUtils import Region, send_request, WebSource, get_internet_validate_code
from db.DBUtil import get_real_estate_sale_status, get_real_estate, get_building_sale_status, get_building, \
    get_house_status, update_building, update_house_status, update_real_estate_count, update_building_count, \
    get_real_estate_statictics_data, get_building_statictics_data

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
               "pageindex=1&roomtype=住宅&buildarea"

    def work(self):
        for region in Region.all_region:
            url = self.base_url % region
            while True:
                try:
                    response = send_request(url)
                    json_rep = json.loads(response.replace("'", '"'))
                    break
                except:
                    continue
            for item in json_rep:
                try:
                    # 查询该楼盘出售情况，全部售完的就跳过
                    real_estate_name = item.get("ZPROJECT")
                    real_estate_result = get_real_estate_sale_status(real_estate_name=real_estate_name)
                    if real_estate_result and real_estate_result.get("house_total_count") != 0 and \
                                    real_estate_result.get("house_sale_count") != 0 \
                            and real_estate_result.get("house_total_count") == real_estate_result.get("house_sale_count"):
                        continue
                    # 新增或查询楼盘
                    real_estate = get_real_estate(real_estate_name, region)
                    if real_estate:
                        real_estate_id = real_estate.get("id")
                    else:
                        real_estate = RealEstate()
                        real_estate.building = real_estate_name
                        real_estate.region = item.get("F_SITE")
                        real_estate.address = item.get("F_ADDR")
                        real_estate.developer = item.get("ENTERPRISENAME")
                        real_estate.sale_building = item.get("F_BLOCK")
                        real_estate.sale_count = item.get("NUM")
                        real_estate.source_id = WebSource.RealEstate
                        real_estate.house_total_count = 0
                        real_estate.house_sale_count = 0
                        real_estate_id = real_estate.__add__()
                    # 大楼数据
                    build_name = item.get("F_BLOCK").split(",")
                    build_id = item.get("BUILDID").split(",")
                    build_register = item.get("F_REGISTER_DATE").split(",")
                    build_residence_count = item.get("BUILDZZNUM").split(",")
                    build_none_residence_count = item.get("BUILDFZZNUM").split(",")
                    # 该楼盘下所有大楼
                    for index in range(len(build_id)):
                        sale_building = build_name[index].replace("'", "")
                        # 新增或查询大楼
                        building = get_building_sale_status(sale_building, real_estate_id)
                        if building:
                            building_id = building.get("id")
                        else:
                            building = Building()
                            building.sale_building = sale_building
                            building.web_build_id = int(build_id[index])
                            building.register_time = datetime.datetime.strptime(build_register[index], "%Y-%m-%d")
                            building.sale_residence_count = int(build_residence_count[index])
                            building.sale_none_residence_count = int(build_none_residence_count[index])
                            building.source_id = WebSource.RealEstate
                            building.real_estate_id = int(real_estate_id)
                            building.total_count = 0
                            building.sale_count = 0
                            building_id = building.__add__()
                        # 查询该大楼出售情况，全部售完的就跳过
                        building_sale_result = get_building_sale_status(sale_building, real_estate_id)
                        if building_sale_result and building_sale_result.get("total_count") != 0 and building_sale_result.get("sale_count") != 0 \
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
                                    # 出售
                                    for temp in td.attrs.get("style").split(";"):
                                        if "background-color:" in temp:
                                            status = ColorStatus.get(temp.split("background-color:")[1])
                                            break
                                    door_number = td.find("font").text
                                    # 查询房间是否已经售出
                                    house_status = get_house_status(door_number, real_estate_id, building_id)
                                    if house_status:
                                        # 已经售出跳过
                                        # 状态改变改状态
                                        if house_status.get("status") != status:
                                            update_house_status(house_status.get("id"), status)
                                        continue
                                    # 未售出房子
                                    validate_url = "http://www.cq315house.com/315web/" + \
                                                   td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                    validate_driver = webdriver.Firefox()
                                    while True:
                                        try:
                                            validate_driver.get(validate_url)
                                        except:
                                            continue
                                        # 截图整个网页
                                        validate_driver.save_screenshot("e:/spider_img/temp.png")
                                        # 获得验证码
                                        code = get_internet_validate_code(validate_driver.find_element_by_tag_name("img"))
                                        if code == -1:
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
                                            # one_house_data = one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src")
                                            one_house_data = unquote(one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src").split("text=")[1].replace("%u", "\\u").decode("unicode-escape"))
                                            if not one_house_data:
                                                continue
                                            if one_house_data and "undefined-undefined" in one_house_data:
                                                import time
                                                time.sleep(60)
                                                continue
                                            json_data = json.loads(one_house_data)
                                            house = House()
                                            house.door_number = json_data.get("FH")
                                            house.status = status
                                            house.inside_area = json_data.get("TNMJ")
                                            house.built_area = json_data.get("JZMJ")
                                            house.house_type = json_data.get("HX")
                                            house.inside_price = json_data.get("NSDJ_TN")
                                            house.built_price = json_data.get("NSDJ_JM")
                                            house.buliding_id = building_id
                                            house.real_estate_id = real_estate_id
                                            house.source_id = 1
                                            house.__add__()
                                            validate_driver.quit()
                                            break
                            # 增加大楼，楼房总量和在售数量
                            building_static_data = get_building_statictics_data(building_id, real_estate_id)
                            update_building_count(building_id, building_static_data.get("total_count"), building_static_data.get("sale_count"))
                            driver.quit()
                    # 统计楼盘数据
                    static_data = get_real_estate_statictics_data(real_estate_id)
                    update_real_estate_count(real_estate_id, static_data.get("total_count"),
                                             static_data.get("sale_count"))
                except BaseException as e:
                    print e
                    continue