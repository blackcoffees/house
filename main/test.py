import urllib

from bs4 import BeautifulSoup
from selenium import webdriver

from util.CommonUtils import get_internet_validate_code

if __name__ == "__main__":
    try:
        url = "http://www.cq315house.com/315web/YanZhengCode/YanZhengPage.aspx?fid=30298371"
        validate_driver = webdriver.Firefox()
        validate_driver.get(url)
        validate_soup = BeautifulSoup(validate_driver.page_source)
        validate_driver.save_screenshot("e:/spider_img/temp.png")
        code = get_internet_validate_code(validate_driver.find_element_by_tag_name("img"), "")
    except BaseException as e:
        print e