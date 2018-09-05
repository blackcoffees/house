# -*- coding:utf8 -*-
import json

import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from base.BaseSpider import BaseSpider
from base.Model import RealEstate, Building
from db.DBUtil import update_building
from util.CommonUtils import Region, send_request, WebSource


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
                    building_url = "http://www.cq315house.com/315web/webservice/GetBuildingInfo.ashx?buildingId=%s" %\
                                   build_id[index]
                    response = send_request(building_url)
                    house_number = json.loads(response).get("presaleCert")
                    update_building(house_number, building_id)

                    # 一栋楼里面的所有房子
                    houses_url = "http://www.cq315house.com/315web/HtmlPage/ShowRoomsNew.aspx?block=%s&buildingid=%s" %\
                                 (sale_building.encode("utf8"), int(build_id[index]))
                    driver = webdriver.PhantomJS()
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
                                status = td.find("font").attrs.get("color")
                                door_number = td.find("font").text
                                validate_url = "http://www.cq315house.com/315web/" + \
                                               td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                valdate_data = {"__VIEWSTATE": "/wEPDwUKLTQyNDAzOTY4MWRk3g6AVf/ZtFkfRXOtHKIYFTcNXOw=",
                                    "__VIEWSTATEGENERATOR": "150E47F4",
                                    "__EVENTVALIDATION" :"/wEWBAL60+2KDQLChPzDDQKM54rGBgKdxMCnCb3faZAm0FhFVHWli/crzfEQ4VIv",
                                    "txtCode": 9,
                                    "Button1": "确定",
                                    "hfTableNum": 9
                                }
                                valdate_data = json.dumps(valdate_data)
                                validate_response = send_request(validate_url, data=valdate_data)
                                print validate





