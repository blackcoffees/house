# -*- coding:utf8 -*-
import os

import math

import operator
from PIL import Image, ImageFile, ImageGrab, ImageEnhance
from pytesseract import pytesseract

from util.CommonUtils import chinese_correct, table

location_base_url = os.path.realpath("image_util").split("main")[0] + "image\\image_util\\"


def alpha_composite_simple():
    """
    融合两张图片
    :return:
    """
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    image2 = Image.open(location_base_url + "alpha_composite_simple_img2.png")
    new_image = Image.alpha_composite(image1, image2)
    new_image.show()


def blend():
    """
    融合两张图片
    :return:
    """
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    image2 = Image.open(location_base_url + "alpha_composite_simple_img2.png")
    new_image = Image.blend(image1, image2, 0.5)
    new_image.show()


def composite():
    """
    融合两张图片
    :return:
    """
    image1 = Image.open(location_base_url + "composite_img1.png")
    image2 = Image.open(location_base_url + "composite_img2.png")
    new_image = Image.composite(image1, image2, image1)
    new_image.show()


def test_eval():
    image = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    def f(x): return 2* x
    new_image = Image.eval(image, f)
    new_image.show()


def merge():
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    r1, g1, b1 = image1.split()
    new_image = Image.merge("RGB", [r1, g1, b1])
    new_image.show()


def cute():
    image = Image.open("E:/spider_img/1.png").crop((0, 0, 21, 24))
    image.save("E:/spider_img/2.png")
    image = Image.open("E:/spider_img/1.png").crop((51, 0, 72, 24))
    image.save("E:/spider_img/3.png")


def compare_image():
    image1 = Image.open("E:/spider_img/test1.png")
    image2 = Image.open("E:/spider_img/test2.png")
    print image1 == image2
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    print image1 == image2
    image1.close()
    image2.close()


def getbands():
    image1 = Image.open("E:/spider_img/temp1.png")
    print image1.getbands()


def getbbox():
    image1 = Image.open("E:/spider_img/temp1.png")
    print image1.getbbox()


def image_corde_correct():
    """
    图片识别码修正
    :return:
    """
    operator_img_url = "e:/spider_img/operator.png"
    number1_img_url = "e:/spider_img/num1.png"
    number2_img_url = "e:/spider_img/num2.png"
    operator_img = Image.open("e:/spider_img/temp1.png").crop((26, 1, 52, 21))
    operator_img.save(operator_img_url)
    number1_img = Image.open("e:/spider_img/temp1.png").crop((0, 0, 20, 22))
    number1_img.save(number1_img_url)
    number2_img = Image.open("e:/spider_img/temp1.png").crop((53, 1, 66, 22))
    number2_img.save(number2_img_url)
    number1_str = pytesseract.image_to_string(number1_img, lang="eng", config="-psm 8 digist")
    number2_str = pytesseract.image_to_string(number2_img, lang="eng", config="-psm 8 digist")
    print "图片识别修正number1:%s" % number1_str
    print "图片识别修正number2:%s" % number2_str
    if number1_str.isdigit() and number2_str.isdigit():
        number1 = int(number1_str)
        number2 = int(number2_str)
        operator_str = pytesseract.image_to_string(operator_img, lang="chi_sim", config="-psm 8")
        print "图片识别修正operator:%s" % operator_str
        if operator_str:
            for chinese in chinese_correct:
                operator_str = operator_str.replace(chinese, chinese_correct[chinese])
            if operator_str == u"\u52a0":
                code = number1 + number2
            elif operator_str == u"\u51cf":
                code = number1 - number2
            elif operator_str == u"\u4e58":
                code = number1 * number2
            elif operator_str == u"\u9664":
                code = number1 / number2
    operator_img.close()
    number1_img.close()
    number2_img.close()
    return code


def getcolors():
    image1 = Image.open("E:/spider_img/temp1.png")
    print image1.getcolors()


def compare_image():
    image1 = Image.open("E:/spider_img/temp.png")
    success_base_url = "e:/spider_img/success"
    compare_image_list = os.listdir(success_base_url)
    histogram1 = image1.histogram()
    for compare_img_url in compare_image_list:
        image2 = Image.open(success_base_url+"/" + compare_img_url)
        histogram2 = image2.histogram()
        if histogram2 == histogram1:
            differ = math.sqrt(
                reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, histogram1, histogram2))) / len(histogram1))
            if differ == 0:
                print histogram1
                print histogram2
                print compare_img_url
                break
        image2.close()
    image1.close()
