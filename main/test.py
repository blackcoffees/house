import time
from scrapy import cmdline

from db.DBUtil import get_real_estate_statictics_data, update_real_estate_count
from db.PoolDB import pool
from util.HouseThread import HouseThread
from util.ProxyIPUtil import ProxyPool

# if __name__ == "__main__":
#     try:
#         a = HouseThread(1)
#         a.start()
#         b = HouseThread(2)
#         b.start()
#     except BaseException as e:
#         print e
cmdline.execute("scrapy crawl real_estate".split())