# -*- coding: utf-8 -*-
class threadList(object):
    def __init__(self):
        self.thread_list = list()

    def append(self, thread):
        self.thread_list.append(thread)

    def sleep(self, function_name):
        for thread in self.thread_list:
            if thread.name == function_name:
                thread.stop = True

    def get_all(self):
        return self.thread_list

    def remove(self, thread):
        self.thread_list.remove(thread)