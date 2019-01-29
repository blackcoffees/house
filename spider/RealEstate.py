# -*- coding:utf8 -*-
import json

import datetime
import time
from urllib import unquote, quote
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from base.BaseSpider import BaseSpider
from base.Model import RealEstate, Building, House
from util.CommonUtils import Region, send_request, WebSource, get_status, \
    div_list_return_dict, get_unit, proxy_list, logger, validate_house_door_number, delete_logs
from db.DBUtil import get_real_estate_sale_status, get_real_estate, get_building_sale_status, get_building, \
    get_house_status, update_building, update_house_status, update_real_estate_count, update_building_count, \
    get_real_estate_statictics_data, get_building_statictics_data, get_all_region, update_region, update_web_house_id
import sys

from util.ImageRecognitionUtil import ImageRecognition
from util.ProxyIPUtil import get_switch_proxy
from util.WebDriverUtil import WebDriverManager

reload(sys)
sys.setdefaultencoding('utf8')


class RealEstateSpider(BaseSpider):
    base_url = "http://www.cq315house.com/315web/webservice/GetMyData999.ashx?" \
               "projectname=&site=%s&kfs=&projectaddr=&pagesize=1&" \
               "pageindex=%s&roomtype=住宅&buildarea"
    base_image_path = os.path.realpath("image").split("main")[0] + "\\image\\"

    def work(self):
        delete_logs()
        options = webdriver.ChromeOptions()
        # options.add_argument("headless")
        web_driver_manager = WebDriverManager(3, "chrome", options)
        validate_driver = web_driver_manager.get_web_driver()
        for region in get_all_region():
            now_page = region.get("now_page")
            while True:
                real_estate_driver = web_driver_manager.get_web_driver()
                # 获得楼盘
                url = self.base_url % (region.get("region").encode("utf8"), now_page)
                if not real_estate_driver.send_url(url, "pre"):
                    logger.info(region.get("region").encode("utf8") + "房产信息收集完成")
                    update_region(region.get("id"), now_page)
                    break
                # 请求完成之后页数就加1
                logger.info(region.get("region") + "：" + str(now_page))
                now_page += 1
                real_estate = real_estate_driver.find_element_by_tag_name("pre").text
                # 关闭网页
                web_driver_manager.destory_web_driver(real_estate_driver.get_id())
                if not real_estate:
                    logger.info(region.get("region").encode("utf8") + "房产信息收集完成")
                    update_region(region.get("id"), 1)
                    break
                # 解析楼盘
                json_rep = json.loads(real_estate.encode("utf8").replace("[", "").replace("]", "").replace("'", "\""))
                list_json_rep = [json_rep]
                for item in list_json_rep:
                    try:
                        # 查询该楼盘出售情况，全部售完的就跳过
                        real_estate_name = item.get("ZPROJECT")
                        real_estate_result = get_real_estate_sale_status(real_estate_name=real_estate_name)
                        if real_estate_result and real_estate_result.get("house_total_count") != 0 \
                                and real_estate_result.get("house_sell_out_count") != 0 \
                                and real_estate_result.get("house_total_count") == real_estate_result.get("house_sell_out_count"):
                            continue
                        # 新增或查询楼盘
                        real_estate = get_real_estate(real_estate_name, region.get("id"))
                        if real_estate:
                            real_estate_id = real_estate.get("id")
                        else:
                            real_estate = RealEstate()
                            real_estate.name = real_estate_name
                            real_estate.region = region.get("id")
                            real_estate.address = item.get("F_ADDR")
                            real_estate.developer = item.get("ENTERPRISENAME")
                            real_estate.sale_building = item.get("F_BLOCK")
                            real_estate.sale_count = item.get("NUM")
                            real_estate.source_id = WebSource.RealEstate
                            real_estate.house_total_count = 0
                            real_estate.house_sell_out_count = 0
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
                                building.real_estate_name = real_estate.name
                                building_id = building.__add__()
                            # 查询该大楼出售情况，全部售完的就跳过
                            building_sale_result = get_building_sale_status(sale_building, real_estate_id)
                            if building_sale_result and building_sale_result.get("total_count") != 0 and building_sale_result.get("sale_count") != 0 \
                                and building_sale_result.get("total_count") == building_sale_result.get("sale_count"):
                                continue
                            # 一栋楼里面的所有房子
                            driver_house = web_driver_manager.get_web_driver()
                            houses_url = "http://www.cq315house.com/315web/HtmlPage/ShowRoomsNew.aspx?block=%s&buildingid=%s" %\
                                         (sale_building.encode("utf8"), int(build_id[index]))
                            driver_house.send_url(houses_url)
                            house_soup = BeautifulSoup(driver_house.page_source, "html.parser")
                            # 关闭网页
                            web_driver_manager.destory_web_driver(driver_house.get_id())
                            # 判断是否请求成功
                            if not house_soup.find("img", attrs={"id": "projectInfo_img"}):
                                continue
                            # 预售许可证
                            pre_sale_number = json.loads(unquote(house_soup.find("img", attrs={"id": "projectInfo_img"}).
                                                              attrs.get("src").split("text=")[1])).get("presaleCert")
                            pre_sale_number = pre_sale_number.replace("%u", "\\u").decode("raw_unicode_escape").encode("utf-8")
                            update_building(pre_sale_number, building_id)
                            tbody = house_soup.find("table", attrs={"id": "_mybuilding"}).find("tbody")
                            trs = tbody.find_all("tr")
                            # 单元列表
                            unit_td_list = house_soup.find_all("input", attrs={"name": "unitb"})
                            unit_list = list()
                            for unit_temp in unit_td_list:
                                unit_list.append(unit_temp.next)
                            # 是否新增了房子
                            is_add_house = False
                            house_count_dict = div_list_return_dict(range(len(trs[0].find_all("td")) - 2), len(unit_list))
                            for tr in trs:
                                tds = tr.find_all("td", attrs={"objt": "tdclass"})
                                for td_index, td in enumerate(tds):
                                    is_exception = False
                                    try:
                                        # 是不是房子
                                        if "display:none" in td.attrs.get("style").replace(" ", ""):
                                            continue
                                        # 单独每一套房子
                                        # 单元号
                                        house_unit = get_unit(house_count_dict, unit_list, td_index).encode("utf8").decode("utf8").replace(" ", "")
                                        # 门牌号
                                        door_number = td.find("font").text.replace(" ", "")
                                        logger.info( "%s %s %s %s %s %s" % (datetime.datetime.now(),
                                                                     region.get("region").encode("utf8").decode("utf8"),
                                                                     real_estate_name, sale_building, house_unit,
                                                                     door_number))
                                        if not validate_house_door_number(door_number):
                                            continue
                                        # 出售状态
                                        house_status_page = self.get_house_status_page(td)
                                        if house_status_page <= 0:
                                            # 没有获取到房间出售状态，跳过这间房间
                                            continue
                                        # 查询数据库中房间是否已经售出
                                        house_status = get_house_status(door_number, real_estate_id, building_id, house_unit)
                                        if house_status:
                                            # 已经售出跳过
                                            # 状态改变改状态
                                            if int(house_status.get("status")) != house_status_page:
                                                update_house_status(house_status.get("id"), house_status_page)
                                            if not house_status.get("web_house_id"):
                                                update_web_house_id(td.find("input").attrs.get("value"), house_status.get("id"))
                                            continue
                                        is_add_house = True
                                        # 未售出房子
                                        validate_url = "http://www.cq315house.com/315web/" + \
                                                       td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                        # 验证码
                                        # self.get_internet_validate_code(validate_driver, validate_url)
                                        image_recognition = ImageRecognition(os.path.realpath("image").split("main")[0] + "\\image\\")
                                        image_recognition.get_expression_code(validate_driver, validate_url)
                                        one_house_soup = BeautifulSoup(validate_driver.page_source, "html.parser")
                                        if not one_house_soup.find("img"):
                                            raise BaseException(u"无法获取房子数据")
                                        one_house_data = unquote(one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src").split("text=")[1].replace("%u", "\\u").decode("unicode-escape"))
                                        if not one_house_data:
                                            raise BaseException(u"无法获取房子数据")
                                        if one_house_data and "undefined-undefined" in one_house_data:
                                            raise BaseException(u"无法获取房子数据")
                                        json_data = json.loads(one_house_data)
                                        if json_data.get("HX") == u"其他":
                                            continue
                                        house = House()
                                        house.door_number = door_number
                                        house.status = house_status_page
                                        house.inside_area = json_data.get("TNMJ")
                                        house.built_area = json_data.get("JZMJ")
                                        house.house_type = json_data.get("HX")
                                        house.inside_price = json_data.get("NSDJ_TN")
                                        house.built_price = json_data.get("NSDJ_JM")
                                        house.buliding_id = building_id
                                        house.real_estate_id = real_estate_id
                                        house.source_id = 1
                                        house.unit = house_unit
                                        house.web_house_id = td.find("input").attrs.get("value")
                                        house.__add__()
                                        logger.info("套内单价：%s， 套内面积：%s" % (house.inside_price, house.inside_area))
                                    except BaseException as e1:
                                        # is_exception = True
                                        logger.error(u"内层")
                                        web_driver_manager.destory_web_driver(validate_driver.get_id())
                                        logger.error(e1)
                                        validate_driver = web_driver_manager.get_web_driver(True)
                                        continue
                                    finally:
                                        if is_exception:
                                            update_region(region.get("id"), now_page)
                            if is_add_house:
                                # 增加大楼，楼房总量和在售数量
                                building_static_data = get_building_statictics_data(building_id, real_estate_id)
                                update_building_count(building_id, building_static_data.get("total_count"), building_static_data.get("sale_count"))
                        # 统计楼盘数据
                        static_data = get_real_estate_statictics_data(real_estate_id)
                        update_real_estate_count(real_estate_id, static_data.get("sum(total_count)"),
                                                 static_data.get("sum(sale_count)"))
                    except BaseException as e2:
                        logger.error(u"外层")
                        # logger.error(e2)
                        continue
                    finally:
                        update_region(region.get("id"), now_page)
                update_region(region.get("id"), now_page)

    def get_house_status_page(self, house):
        """
        获得页面上这间房子的出售状态
        :param house:
        :return:
        """
        status = -1
        for temp in house.attrs.get("style").split(";"):
            if "background-color:" in temp or "background:" in temp:
                if "background-color" in temp:
                    status = get_status(temp.split("background-color:")[1])
                else:
                    status = get_status(temp.split("background:")[1])
                break
        return status

