from scrapy import cmdline

from db.DBUtil import get_real_estate_statictics_data, update_real_estate_count
from db.PoolDB import pool
from util.ProxyIPUtil import ProxyPool

# if __name__ == "__main__":
    # try:
    #     # a = ProxyPool("www.baidu.com")
    #     # a.__get_proxy_ip_conf__()
    #     static_data = get_real_estate_statictics_data(2)
    #     update_real_estate_count(2, static_data.get("sum(total_count)"),
    #                              static_data.get("sum(sale_count)"))
    # except BaseException as e:
    #     print e
cmdline.execute("scrapy crawl real_estate".split())