# -*- coding: utf-8 -*-
import MySQLdb
from DBUtils.PooledDB import PooledDB

host = '127.0.0.1'
user = 'root'
password = "root"
db = "house"
port = 3306


class PoolDB(object):
    __conn__ = None
    __pool__ = None

    def __init__(self):
        if not self.__pool__:
            self.__pool__ = PooledDB(creator=MySQLdb, mincached=2, maxcached=5, maxshared=0, maxconnections=6,
                                     blocking=True, host=host, user=user, passwd=password, db=db, charset="utf8", use_unicode=True)

    def __get_connect__(self):
        self.__conn__ = self.__pool__.connection()
        cursor = self.__conn__.cursor()
        if not cursor:
            raise "数据库连接不上"
        return cursor

    def find(self, sql, param=None):
        cursor = self.__get_connect__()
        try:
            if param:
                cursor.execute(sql, param)
            else:
                cursor.execute(sql)
            result = cursor.fetchall()
            value = sql.split("select")[1].split("from")[0].split(",")
            data_list = list()
            for item in result:
                data_dict = dict()
                for (index, v) in enumerate(value):
                    data_dict[v.strip()] = item[index]
                data_list.append(data_dict)
            return data_list
        except BaseException as e:
            print e
        finally:
            cursor.close()
            self.__conn__.close()

    def commit(self, sql, param=None):
        cursor = self.__get_connect__()
        try:
            if param:
                cursor.execute(sql, param)
            else:
                cursor.execute(sql)
            self.__conn__.commit()
            return cursor.lastrowid
        except BaseException as e:
            print e
        finally:
            cursor.close()
            self.__conn__.close()

    def find_one(self, sql, param=None):
        result = self.find(sql, param)
        if result and len(result) > 0:
            return result[0]
        return None

pool = PoolDB()
