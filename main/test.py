from db.PoolDB import pool
from util.ProxyIPUtil import ProxyPool

if __name__ == "__main__":
    try:
        # a = ProxyPool("www.baidu.com")
        # a.__get_proxy_ip_conf__()
        pool.__get_sql_query_param__("""select sum(total_count), sum(sale_count) from building where real_estate_id=3438""")
    except BaseException as e:
        print e
