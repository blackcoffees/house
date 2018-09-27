# -*- coding:utf8 -*-
import json

import datetime
import time
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
from util.CommonUtils import Region, send_request, WebSource, get_internet_validate_code, get_status, \
    div_list_return_dict, get_unit
from db.DBUtil import get_real_estate_sale_status, get_real_estate, get_building_sale_status, get_building, \
    get_house_status, update_building, update_house_status, update_real_estate_count, update_building_count, \
    get_real_estate_statictics_data, get_building_statictics_data, get_all_region, update_region


class RealEstateSpider(BaseSpider):
    base_url = "http://www.cq315house.com/315web/webservice/GetMyData999.ashx?" \
               "projectname=&site=%s&kfs=&projectaddr=&pagesize=1&" \
               "pageindex=%s&roomtype=住宅&buildarea"

    def work(self):
        now_page = 0
        for region in get_all_region():
            while True:
                if now_page and now_page != region.get("now_page"):
                    pass
                else:
                    # 第一次启动程序的时候
                    now_page = region.get("now_page")
                url = self.base_url % (region.get("region").encode("utf8"), now_page)
                while True:
                    try:
                        response = send_request(url)
                        json_rep = json.loads(response.replace("'", '"'))
                        break
                    except:
                        continue
                # 没有数据之后跳出
                if not json_rep:
                    print region.get("region").encode("utf8") + "房产信息收集完成"
                    break
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
                        real_estate = get_real_estate(real_estate_name, region.get("id"))
                        if real_estate:
                            real_estate_id = real_estate.get("id")
                        else:
                            real_estate = RealEstate()
                            real_estate.building = real_estate_name
                            real_estate.region = region.get("id")
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
                            # options = webdriver.FirefoxOptions()
                            # options.add_argument("-headless")
                            # driver = webdriver.Firefox(firefox_options=options)
                            options = webdriver.ChromeOptions()
                            options.add_argument("headless")
                            driver = webdriver.Chrome(chrome_options=options)
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
                                house_soup = BeautifulSoup(driver.page_source, "html.parser")
                                tbody = house_soup.find("table", attrs={"id": "_mybuilding"}).find("tbody")
                                trs = tbody.find_all("tr")
                                # 单元列表
                                unit_td_list = house_soup.find_all("input", attrs={"name": "unitb"})
                                unit_list = list()
                                for unit_temp in unit_td_list:
                                    unit_list.append(unit_temp.next)
                                # 是否新增了房子
                                is_add_house = False
                                for tr in trs:
                                    tds = tr.find_all("td", attrs={"objt": "tdclass"})
                                    house_count_dict = div_list_return_dict(range(len(tr.find_all("td")) - 2), len(unit_list))
                                    for td_index, td in enumerate(tds):
                                        # 是不是房子
                                        if "display:none" in td.attrs.get("style").replace(" ", ""):
                                            continue
                                        # 单独每一套房子
                                        # 单元号
                                        house_unit = get_unit(house_count_dict, unit_list, td_index).encode("utf8").decode("utf8").replace(" ", "")
                                        # 门牌号
                                        door_number = td.find("font").text
                                        print "%s %s %s %s" % (real_estate_name, sale_building, house_unit, door_number)
                                        # 出售状态
                                        for temp in td.attrs.get("style").split(";"):
                                            if "background-color:" in temp or "background:" in temp:
                                                if "background-color" in temp:
                                                    status = get_status(temp.split("background-color:")[1])
                                                else:
                                                    status = get_status(temp.split("background:")[1])
                                                break
                                        if status == 0:
                                            continue
                                        # 查询房间是否已经售出
                                        house_status = get_house_status(door_number, real_estate_id, building_id, house_unit)
                                        if house_status:
                                            # 已经售出跳过
                                            # 状态改变改状态
                                            if int(house_status.get("status")) != status:
                                                update_house_status(house_status.get("id"), status)
                                            continue
                                        is_add_house = True
                                        # 未售出房子
                                        validate_url = "http://www.cq315house.com/315web/" + \
                                                       td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                        # validate_driver = webdriver.Firefox()
                                        validate_driver = webdriver.Chrome(chrome_options=options)
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
                                                if not one_house_soup.find("img"):
                                                    continue
                                                one_house_data = unquote(one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src").split("text=")[1].replace("%u", "\\u").decode("unicode-escape"))
                                                if not one_house_data:
                                                    continue
                                                if one_house_data and "undefined-undefined" in one_house_data:
                                                    time.sleep(60)
                                                    continue
                                                json_data = json.loads(one_house_data)
                                                house = House()
                                                house.door_number = door_number
                                                house.status = status
                                                house.inside_area = json_data.get("TNMJ")
                                                house.built_area = json_data.get("JZMJ")
                                                house.house_type = json_data.get("HX")
                                                house.inside_price = json_data.get("NSDJ_TN")
                                                house.built_price = json_data.get("NSDJ_JM")
                                                house.buliding_id = building_id
                                                house.real_estate_id = real_estate_id
                                                house.source_id = 1
                                                house.unit = house_unit
                                                house.__add__()
                                                validate_driver.quit()
                                                break
                                if is_add_house:
                                    # 增加大楼，楼房总量和在售数量
                                    building_static_data = get_building_statictics_data(building_id, real_estate_id)
                                    update_building_count(building_id, building_static_data.get("total_count"), building_static_data.get("sale_count"))
                                    print "正常休眠2分钟"
                                    time.sleep(120)
                                driver.quit()
                        # 统计楼盘数据
                        static_data = get_real_estate_statictics_data(real_estate_id)
                        update_real_estate_count(real_estate_id, static_data.get("total_count"),
                                                 static_data.get("sale_count"))
                    except BaseException as e:
                        if e.msg:
                            print e.msg.encode("utf8")
                        else:
                            print e
                        print "异常休眠5分钟"
                        time.sleep(300)
                        continue
                    finally:
                        update_region(region.get("id"), now_page)
                        try:
                            if validate_driver:
                                validate_driver.quit()
                            if driver:
                                driver.quit()
                        except:
                            pass
                now_page = now_page + 1
                update_region(region.get("id"), now_page)