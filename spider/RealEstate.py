# -*- coding:utf8 -*-
import json

import datetime
import time
import re
import urllib2
from urllib import unquote, quote

import os

import imagehash
import math

import operator
import pytesseract
from PIL import Image, ImageEnhance, ImageFile
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from base.BaseSpider import BaseSpider
from base.Model import RealEstate, Building, House
from util.CommonUtils import Region, send_request, WebSource, get_status, \
    div_list_return_dict, get_unit, rep, table, chinese_correct, proxy_list, logger, validate_house_door_number
from db.DBUtil import get_real_estate_sale_status, get_real_estate, get_building_sale_status, get_building, \
    get_house_status, update_building, update_house_status, update_real_estate_count, update_building_count, \
    get_real_estate_statictics_data, get_building_statictics_data, get_all_region, update_region
import sys

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
        options = webdriver.ChromeOptions()
        # options.add_argument("headless")
        web_driver_manager = WebDriverManager(3, "chrome", options)
        real_estate_driver = web_driver_manager.get_web_driver()
        driver_house = web_driver_manager.get_web_driver()
        validate_driver = web_driver_manager.get_web_driver()
        for region in get_all_region():
            now_page = region.get("now_page")
            while True:
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
                                and real_estate_result.get("house_sale_count") != 0 \
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
                            # 一栋楼里面的所有房子
                            houses_url = "http://www.cq315house.com/315web/HtmlPage/ShowRoomsNew.aspx?block=%s&buildingid=%s" %\
                                         (sale_building.encode("utf8"), int(build_id[index]))
                            driver_house.send_url(houses_url)
                            house_soup = BeautifulSoup(driver_house.page_source, "html.parser")
                            # 预售许可证
                            house_number = json.loads(unquote(house_soup.find("img", attrs={"id": "projectInfo_img"}).
                                                              attrs.get("src").split("text=")[1])).get("presaleCert")
                            house_number = house_number.replace("%u", "\\u").decode("raw_unicode_escape").encode("utf-8")
                            update_building(house_number, building_id)
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
                                            continue
                                        is_add_house = True
                                        # 未售出房子
                                        validate_url = "http://www.cq315house.com/315web/" + \
                                                       td.find("a").attrs.get("onclick").split("../")[1].split("');")[0]
                                        # 验证码
                                        self.get_internet_validate_code(validate_driver, validate_url)
                                        one_house_soup = BeautifulSoup(validate_driver.page_source, "html.parser")
                                        if not one_house_soup.find("img"):
                                            raise BaseException("无法获取房子数据")
                                        one_house_data = unquote(one_house_soup.find("img", attrs={"id": "roomInfo_img"}).attrs.get("src").split("text=")[1].replace("%u", "\\u").decode("unicode-escape"))
                                        if not one_house_data:
                                            raise BaseException("无法获取房子数据")
                                        if one_house_data and "undefined-undefined" in one_house_data:
                                            raise BaseException("无法获取房子数据")
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
                                        house.__add__()
                                        logger.info("套内单价：%s， 套内面积：%s" % (house.inside_price, house.inside_area))
                                    except BaseException as e:
                                        # is_exception = True
                                        web_driver_manager.destory_web_driver(validate_driver.get_id())
                                        logger.info(e)
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
                    except BaseException as e:
                        logger.info(e)
                        logger.info("%s 外层异常休眠5分钟" % datetime.datetime.now())
                        time.sleep(300)
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

    def get_internet_validate_code(self, validate_driver, validate_url):
        """
        图片识别
        :param validate_driver:
        :param validate_url:
        :return:
        """
        while True:
            expression = ""
            # 成功请求到网页
            if not validate_driver.send_url(validate_url, tag_name="img"):
                raise BaseException("无法获取验证网页")
            # 截图整个网页
            validate_driver.save_screenshot(self.base_image_path + "temp.png")
            try:
                img = validate_driver.find_element_by_tag_name("img")
                location_img_url = self.base_image_path + "temp.png"
                # 保存验证码图片
                left = img.location.get("x")
                top = img.location.get("y")
                width = left + img.size.get("width")
                height = top + img.size.get("height")
                # image = Image.open(BytesIO(response.read()))
                image = Image.open(location_img_url).crop((left, top, width, height))
                image.save(location_img_url)
                # 解析验证码
                # 防止图片没有保存下来
                time.sleep(3)
                location_img = Image.open(location_img_url)
                # 转到灰度
                imgry = location_img.convert("L")
                imgry.save(location_img_url)
                # 对比度增强
                sharpness = ImageEnhance.Contrast(imgry)
                sharp_img = sharpness.enhance(2.0)
                sharp_img.save(location_img_url)
                # 二值化，采用阈值分割法，threshold为分割点
                out = imgry.point(table, '1')
                out.save(location_img_url)
                # 识别图片
                int_code = -1
                if expression:
                    int_code = self.compute_code(expression)
                if int_code == -1:
                    code_str = pytesseract.image_to_string(out, lang="chi_sim")
                    location_img.close()
                    imgry.close()
                    sharp_img.close()
                    out.close()
                    if not code_str:
                        continue
                    code_str = code_str.strip()
                    code_str = code_str.upper()
                    # 替换字符
                    code_str = self.replace_character(code_str)
                    logger.info(code_str)
                    succ_dict = self.get_succ_dict(code_str[1], code_str[0], code_str[2])
                    if code_str[0].isdigit() and code_str[2].isdigit():
                        number1 = str(code_str[0])
                        number2 = str(code_str[2])
                        if code_str[1] == u"\u52a0":
                            expression = number1 + "+" + number2
                        elif code_str[1] == u"\u51cf":
                            expression = number1 + "-" + number2
                        elif code_str[1] == u"\u4e58":
                            expression = number1 + "*" + number2
                        elif code_str[1] == u"\u9664":
                            expression = number1 + "/" + number2
                        else:
                            expression = self.image_corde_correct(succ_dict)
                    else:
                        expression = self.image_corde_correct(succ_dict)
                    if not expression:
                        # TODO：成功图片比较，识别率较低
                        # 比较以前的成功图片
                        compare_code = self.compare_success_img(location_img_url, 0)
                        logger.info("成功图片比较：%s" % compare_code)
            except BaseException as e:
                continue
            logger.info("验证码:%s" % expression)
            int_code = self.compute_code(expression)
            # 发送验证码请求
            code_input = validate_driver.find_element_by_id("txtCode")
            code_input.send_keys(int_code)
            validate_driver.find_element_by_id("Button1").click()
            one_house_url = validate_driver.current_url
            if "bid" in one_house_url:
                self.save_success_image(self.base_image_path + "temp.png", expression)
                return True

    def image_corde_correct(self, succ_dict=None):
        """
        图片识别码修正
        :return:
        """
        succ_number1 = None
        succ_number2 = None
        succ_operation = None
        if succ_dict:
            succ_number1 = succ_dict.get("succ_number1")
            succ_number2 = succ_dict.get("succ_number2")
            succ_operation = succ_dict.get("succ_operation")
        operator_img_url = self.base_image_path + "operator.png"
        number1_img_url = self.base_image_path + "num1.png"
        number2_img_url = self.base_image_path + "num2.png"
        if succ_number1:
            number1_str = succ_number1
        else:
            number1_img = Image.open(self.base_image_path + "temp.png").crop((0, 0, 17, 20))
            number1_img.save(number1_img_url)
            number1_str = pytesseract.image_to_string(number1_img, lang="eng", config="-psm 8 digist")
            logger.info("图片识别修正number1:%s" % number1_str)
        if succ_number2:
            number2_str = succ_number2
        else:
            number2_img = Image.open(self.base_image_path + "temp.png").crop((53, 1, 66, 22))
            number2_img.save(number2_img_url)
            number2_str = pytesseract.image_to_string(number2_img, lang="eng", config="-psm 8 digist")
        logger.info("图片识别修正number2:%s" % number2_str)
        # 替换字符
        number1_str = self.replace_character(number1_str)
        number2_str = self.replace_character(number2_str)
        if number1_str.isdigit() and number2_str.isdigit():
            if succ_operation:
                operator_str = succ_operation
            else:
                operator_img = Image.open(self.base_image_path + "temp.png").crop((26, 1, 52, 21))
                operator_img.save(operator_img_url)
                operator_str = pytesseract.image_to_string(operator_img, lang="chi_sim", config="-psm 8")
                logger.info("图片识别修正operator:%s" % operator_str)
            # 替换字符
            operator_str = self.replace_character(operator_str)
            succ_dict = self.get_succ_dict(operator_str, number1_str, number2_str)
            if operator_str:
                if operator_str == u"\u52a0":
                    expression = number1_str + "+" + number2_str
                elif operator_str == u"\u51cf":
                    expression = number1_str + "-" + number2_str
                elif operator_str == u"\u4e58":
                    expression = number1_str + "*" + number2_str
                elif operator_str == u"\u9664":
                    expression = number1_str + "/" + number2_str
                else:
                    expression = self.compare_image_correct(operator_img_url, number1_img_url, number2_img_url, succ_dict)
            else:
                expression = self.compare_image_correct(operator_img_url, number1_img_url, number2_img_url, succ_dict)
        else:
            succ_dict = self.get_succ_dict("", number1_str, number2_str)
            expression = self.compare_image_correct(operator_img_url, number1_img_url, number2_img_url, succ_dict)
        try:
            operator_img.close()
            number1_img.close()
            number2_img.close()
        except BaseException:
            pass
        return expression

    def compare_image_correct(self, operator_img_url, number1_img_url, number2_img_url, succ_dict=None):
        """
        图片比较修正
        :param image1:
        :param image2:
        :return:
        """
        succ_operation = None
        succ_number1 = None
        succ_number2 = None
        if succ_dict:
            succ_operation = succ_dict.get("succ_operation")
            succ_number1 = succ_dict.get("succ_number1")
            succ_number2 = succ_dict.get("succ_number2")
        if succ_operation:
            operation_str = succ_operation
        else:
            operation_str = self.get_compare_image(operator_img_url)
            logger.info("图片比较修正operator:%s" % operation_str)
        if succ_number1:
            number1_str = succ_number1
        else:
            number1_str = self.get_compare_image(number1_img_url)
            logger.info("图片比较修正number1:%s" % number1_str)
        if succ_number2:
            number2_str = succ_number2
        else:
            number2_str = self.get_compare_image(number2_img_url)
            logger.info("图片比较修正number2:%s" % number2_str)
        if operation_str == "add":
            return number1_str + "+" + number2_str
        elif operation_str == "reduce":
            return number1_str + "-" + number2_str
        elif operation_str == "*":
            return number1_str + "*" + number2_str
        elif operation_str == "/":
            return number1_str + "/" + number2_str
        else:
            raise ""

    def get_compare_image(self, image_url):
        """
        图片比较
        :param image_url:
        :return:
        """
        with open(image_url, "rb") as fp:
            hash2 = imagehash.average_hash(Image.open(fp))
        image = Image.open(image_url)
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        compare_image_list = [u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"add", u"reduce"]
        for compare_image_str in compare_image_list:
            compare_image_str_url = self.base_image_path + ("%s.png" % compare_image_str)
            try:
                compare_image = Image.open(compare_image_str_url)
                if not compare_image:
                    image.close()
                    return ""
            except:
                image.close()
            # 比较图片
            the_same = compare_image == image
            if the_same:
                image.close()
                return compare_image_str
            # 计算hash
            hash1 = 0
            with open(compare_image_str_url, "rb") as fp:
                hash1 = imagehash.average_hash(Image.open(fp))
            dif = hash1 - hash2
            if dif < 0:
                dif = -dif
            if dif <= 2:
                image.close()
                return compare_image_str
            compare_image.close()

    def replace_character(self, code_str):
        """
        替换字符
        :param value:
        :return:
        """
        # 替換數字
        for r in rep:
            code_str = code_str.replace(r, rep[r])
        # 替換中文
        for chinese in chinese_correct:
            code_str = code_str.replace(chinese, chinese_correct[chinese])
        return code_str

    def save_success_image(self, image_url, expression_str):
        """
        保存识别成功的图片
        :param image_url:
        :param expression_str:
        :return:
        """
        success_base_url = self.base_image_path + "success\\"
        succ_img_url = os.listdir(success_base_url)
        if str(expression_str) + ".png" in succ_img_url:
            return True
        base_image = Image.open(image_url)
        base_image.save(success_base_url + str(expression_str) + ".png")
        base_image.close()

    def compute_code(self, expression_str):
        """
        计算表达式
        :param expression_str:
        :return:
        """
        if "+" in expression_str:
            return int(expression_str.split("+")[0]) + int(expression_str.split("+")[1])
        elif "-" in expression_str:
            return int(expression_str.split("-")[0]) - int(expression_str.split("-")[1])
        elif "*" in expression_str:
            return int(expression_str.split("*")[0]) * int(expression_str.split("*")[1])
        elif "/" in expression_str:
            return int(expression_str.split("/")[0]) / int(expression_str.split("/")[1])
        return

    def compare_success_img(self, image_url, maxhash=-1):
        """
        识别成功的图片比较
        :param image_url:
        :return:
        """
        operation_str = -1
        success_base_url = self.base_image_path +"success"
        compare_image_list = os.listdir(success_base_url)
        if not compare_image_list:
            return -1
        image1 = Image.open(image_url)
        image_histogram = image1.histogram()
        for compare_image_str in compare_image_list:
            image2 = Image.open(self.base_image_path + ("success\\%s" % compare_image_str))
            histogram2 = image2.histogram()
            if image_histogram == histogram2:
                differ = math.sqrt(
                    reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, image_histogram, histogram2))) / len(
                        image_histogram))
                if differ == 0.0:
                    operation_str = compare_image_str.split(".png")[0]
                    logger.info(u"%s 成功图片对比:%s" % (datetime.datetime.now(), operation_str))
                    break
            else:
                image2.close()
        image1.close()
        image2.close()
        return operation_str

    def get_succ_dict(self, operation_str, number1_str, number2_str):
        succ_dict = dict()
        if operation_str in [u"\u52a0", u"\u51cf", u"\u4e58", u"\u9664"]:
            succ_dict["succ_operation"] = operation_str
        if number1_str.isdigit():
            succ_dict["succ_number1"] = number1_str
        if number2_str.isdigit():
            succ_dict["succ_number2"] = number2_str
        return succ_dict