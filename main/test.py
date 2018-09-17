import urllib

from bs4 import BeautifulSoup
from selenium import webdriver

from util.CommonUtils import get_internet_validate_code
from util.ImageUtil import alpha_composite_simple, blend, composite

if __name__ == "__main__":
    try:
        composite()
    except BaseException as e:
        print e