# -*- coding:utf8 -*-
import threading

from spider.House import HouseSpider


class HouseThread(threading.Thread):
    thread_no = None

    def __init__(self, thread_no):
        super(HouseThread, self).__init__()
        self.thread_no = thread_no

    def get_thread_no(self):
        return self.thread_no

    def run(self):
        a = HouseSpider(self.get_thread_no())
        a.work()