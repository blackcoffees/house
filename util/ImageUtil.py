# -*- coding:utf8 -*-
import os
from PIL import Image

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