# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json
import random

import datetime
from scrapy import signals, Request
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.exceptions import CloseSpider
from scrapy.utils.response import response_status_message
from twisted.internet.error import TimeoutError

from db.PoolDB import pool
from util.CommonUtils import list_user_agent, logger
from util.ProxyIPUtil import proxy_pool


class ScrapySpiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapySpiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class HouseSpiderRetryMiddleware(RetryMiddleware):
    dict_error_building = dict()

    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            spider.is_change_proxy = True
            # building 爬虫，遇到无法处理的数据
            if spider.name == "building":
                logger.error(u"中间件切换代理ip:%s,%s" % (response.status, spider.building.get("id")))
                if not self.handle_error_building(spider.building.get('id')):
                    return self._retry(request, response_status_message(response.status), spider) or response
                else:
                    spider.building = self.handle_sql(spider.building_sql)
                    if not spider.building:
                        raise CloseSpider(u"数据收集完成，爬虫关闭")
                    request = request.replace(body=json.dumps({"buildingid": spider.building.get("id")}))
                    return request
        else:
            return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            if not isinstance(exception, TimeoutError):
                spider.is_change_proxy = True
                logger.error(u"中间件切换代理ip")
                logger.error(exception)
                return self._retry(request, exception, spider)

    def set_error_building_status(self, building_id):
        sql = """update building set status=3, updated=%s where id=%s and status=1"""
        pool.commit(sql, param=[datetime.datetime.now(), building_id])

    def handle_error_building(self, building_id):
        if building_id in self.dict_error_building:
            if self.dict_error_building.get(building_id) >= 5:
                self.set_error_building_status(building_id)
                logger.warning(u"数据错误%s" % building_id)
                return True
            else:
                self.dict_error_building[building_id] = self.dict_error_building.get(building_id) + 1
        else:
            self.dict_error_building[building_id] = 1
        return False

    def handle_sql(self, sql, param=None):
        return pool.find_one(sql, param=param)


class AgentMiddleware(UserAgentMiddleware):

    def process_request(self, request, spider):
        user_agent = random.choice(list_user_agent)
        request.headers["User-Agent"] = [user_agent]


class MyProxyMiddleware(HttpProxyMiddleware):
    proxy_ip = None

    def get_proxy_ip(self):
        proxy_pool.remove_proxy_ip(self.proxy_ip)
        self.proxy_ip = proxy_pool.get_proxy_ip(is_count_time=False)

    def process_request(self, request, spider):
        pass
        if not self.proxy_ip or spider.is_change_proxy:
            self.get_proxy_ip()
        if self.proxy_ip:
            request.meta["proxy"] = "http://%s" % self.proxy_ip
