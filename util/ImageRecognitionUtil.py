# -*- coding:utf8 -*-
import datetime
import time
import os
import imagehash
import math
import operator
import pytesseract
from PIL import Image, ImageEnhance, ImageFile
from util.CommonUtils import logger

# 二值化
threshold = 140
image_two_valued_table = []
for i in range(256):
    if i < threshold:
        image_two_valued_table.append(0)
    else:
        image_two_valued_table.append(1)

# 由于都是数字
# 对于识别成字母的 采用该表进行修正
rep = {"O": "0", "I": "1", "L": "1", "Z": "2", "S": "8"}

chinese_correct = {
    u"夕刀": u"加", u"夕奴": u"加", u"潺": u"减", u"汐奴": u"加", u"遂夕": u"加", u"儡": u"1", u"喊": u"减", u"遂奴": u"加"
}


class ImageRecognition(object):
    base_image_path = None

    def __init__(self, base_path):
        self.base_image_path = base_path

    def get_expression_code(self, validate_driver, validate_url, local_file_name=None):
        """
        获得验证码
        :param validate_driver:
        :param validate_url:
        :return:
        """
        while True:
            expression = None
            try:
                # 成功请求到网页
                if not validate_driver.send_url(validate_url, tag_name="img"):
                    raise BaseException("无法获取验证网页")
                # 截图整个网页
                if local_file_name:
                    validate_driver.save_screenshot(self.base_image_path + local_file_name)
                else:
                    validate_driver.save_screenshot(self.base_image_path + "temp.png")
                # 保存图片
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
                # 防止图片没有保存下来
                time.sleep(3)
                # 识别图片
                try:
                    expression1 = self.get_internet_validate_code()
                except:
                    expression1 = None
                logger.error(u"图片识别：%s" % expression1)
                # 图片修正识别
                try:
                    expression2 = self.image_corde_correct()
                except:
                    expression2 = None
                logger.error(u"图片识别修正：%s" % expression2)
                # 图片比较识别
                try:
                    expression3 = self.compare_image_correct(operator_img_url=(self.base_image_path + "operator.png"),
                                                             number1_img_url=(self.base_image_path + "num1.png"),
                                                             number2_img_url=(self.base_image_path + "num2.png"))
                except:
                    expression3 = None
                logger.error(u"图片比较识别：%s" % expression3)
                # 成功图片比较
                try:
                    expression4 = self.compare_success_img(location_img_url)
                except:
                    expression4 = None
                logger.error(u"成功图片比较：%s" % expression4)
                if not (expression1 or expression2 or expression3):
                    if expression4:
                        expression = expression4
                    else:
                        logger.error(u"图片识别失败")
                else:
                    succ_size_expression1 = self.confirm_return_express(expression1, [expression2, expression3])
                    succ_size_expression2 = self.confirm_return_express(expression2, [expression1, expression3])
                    succ_size_expression3 = self.confirm_return_express(expression3, [expression1, expression2])
                    if succ_size_expression1 > succ_size_expression2:
                        if succ_size_expression1 > succ_size_expression3:
                            expression = expression1
                        else:
                            expression = expression3
                    else:
                        if succ_size_expression2 > succ_size_expression3:
                            expression = expression2
                        else:
                            expression = expression3
            except BaseException as e:
                logger.error(e)
            logger.info("验证码:%s" % expression)
            # 计算验证码
            int_code = self.compute_code(expression)
            # 发送验证码请求
            code_input = validate_driver.find_element_by_id("txtCode")
            code_input.send_keys(int_code)
            validate_driver.find_element_by_id("Button1").click()
            one_house_url = validate_driver.current_url
            if "bid" in one_house_url:
                # 保存成功的图片
                self.save_success_image(self.base_image_path + "temp.png", expression)
                return True

    def confirm_return_express(self, origin_expression, list_compare_expression):
        """
        比较确认那个多
        :param origin_expression: 待比较的表达式
        :param list_compare_expression: 需要比较的表达式
        :return:
        """
        succ_size = 0
        if not origin_expression:
            return succ_size
        for compare_expression in list_compare_expression:
            if not compare_expression:
                succ_size += 1
            elif origin_expression == compare_expression:
                succ_size += 1
        return succ_size

    def get_internet_validate_code(self):
        """
        图片识别
        :param validate_driver:
        :param validate_url:
        :return:
        """
        expression = ""
        # img = validate_driver.find_element_by_tag_name("img")
        location_img_url = self.base_image_path + "temp.png"
        # # 保存验证码图片
        # left = img.location.get("x")
        # top = img.location.get("y")
        # width = left + img.size.get("width")
        # height = top + img.size.get("height")
        # # image = Image.open(BytesIO(response.read()))
        # image = Image.open(location_img_url).crop((left, top, width, height))
        # image.save(location_img_url)
        # 解析验证码
        location_img = Image.open(location_img_url)
        # 转到灰度
        imgry = location_img.convert("L")
        imgry.save(location_img_url)
        # 对比度增强
        sharpness = ImageEnhance.Contrast(imgry)
        sharp_img = sharpness.enhance(2.0)
        sharp_img.save(location_img_url)
        # 二值化，采用阈值分割法，threshold为分割点
        out = imgry.point(image_two_valued_table, '1')
        out.save(location_img_url)
        # 识别图片
        # int_code = -1
        # if expression:
        #     int_code = self.compute_code(expression)
        # if int_code == -1:
        code_str = pytesseract.image_to_string(out, lang="chi_sim")
        location_img.close()
        imgry.close()
        sharp_img.close()
        out.close()
        if not code_str:
            return ""
        code_str = code_str.strip()
        code_str = code_str.upper()
        # 替换字符
        code_str = self.replace_character(code_str)
        # logger.info(code_str)
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
        return expression

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
            # logger.info("图片识别修正number1:%s" % number1_str)
        if succ_number2:
            number2_str = succ_number2
        else:
            number2_img = Image.open(self.base_image_path + "temp.png").crop((53, 1, 66, 22))
            number2_img.save(number2_img_url)
            number2_str = pytesseract.image_to_string(number2_img, lang="eng", config="-psm 8 digist")
        # logger.info("图片识别修正number2:%s" % number2_str)
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
                # logger.info("图片识别修正operator:%s" % operator_str)
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
            # logger.info("图片比较修正operator:%s" % operation_str)
        if succ_number1:
            number1_str = succ_number1
        else:
            number1_str = self.get_compare_image(number1_img_url)
            # logger.info("图片比较修正number1:%s" % number1_str)
        if succ_number2:
            number2_str = succ_number2
        else:
            number2_str = self.get_compare_image(number2_img_url)
            # logger.info("图片比较修正number2:%s" % number2_str)
        if operation_str == "add":
            return number1_str + "+" + number2_str
        elif operation_str == "reduce":
            return number1_str + "-" + number2_str
        elif operation_str == "*":
            return number1_str + "*" + number2_str
        elif operation_str == "/":
            return number1_str + "/" + number2_str
        else:
            return None

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
        if not expression_str:
            return 0
        if "+" in expression_str:
            return int(expression_str.split("+")[0]) + int(expression_str.split("+")[1])
        elif "-" in expression_str:
            return int(expression_str.split("-")[0]) - int(expression_str.split("-")[1])
        elif "*" in expression_str:
            return int(expression_str.split("*")[0]) * int(expression_str.split("*")[1])
        elif "/" in expression_str:
            return int(expression_str.split("/")[0]) / int(expression_str.split("/")[1])

    def compare_success_img(self, image_url, maxhash=-1):
        """
        识别成功的图片比较
        :param image_url:
        :return:
        """
        operation_str = None
        success_base_url = self.base_image_path +"success"
        compare_image_list = os.listdir(success_base_url)
        if not compare_image_list:
            return None
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
                    # logger.info(u"成功图片对比:%s" % operation_str)
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