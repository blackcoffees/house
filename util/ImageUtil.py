# -*- coding:utf8 -*-
import os
from PIL import Image

location_base_url = os.path.realpath("image_util").split("main")[0] + "image\\image_util\\"


def alpha_composite_simple():
    """
    复合两张图片
    :return:
    """
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    image2 = Image.open(location_base_url + "alpha_composite_simple_img2.png")
    new_image = Image.alpha_composite(image1, image2)
    new_image.show()


def blend():
    """

    :return:
    """
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    image2 = Image.open(location_base_url + "alpha_composite_simple_img2.png")
    new_image = Image.blend(image1, image2, 0.5)
    new_image.show()


def composite():
    image1 = Image.open(location_base_url + "alpha_composite_simple_img1.png")
    image2 = Image.open(location_base_url + "alpha_composite_simple_img2.png")
    new_image = Image.composite(image1, image2, image1)
    new_image.show()