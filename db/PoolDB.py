# -*- coding: utf-8 -*-
import logging
from logging.handlers import TimedRotatingFileHandler

import MySQLdb
import os

import time
from DBUtils.PooledDB import PooledDB

from util.CommonUtils import logger

host = '127.0.0.1'
user = 'root'
password = "root"
db = "house"
port = 3306

# db_pool_formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(msg)s")
# db_pool_logger = logging.getLogger()
# db_pool_logger.setLevel(logging.INFO)
# db_pool_log_path = os.path.dirname(os.getcwd()) + '/logs/'
# log_filename = db_pool_log_path + time.strftime("%Y%m%d", time.localtime()) + ".log"
# db_pool_fh = TimedRotatingFileHandler(log_filename, when="d", encoding='utf-8', backupCount=7)
# db_pool_fh.setLevel(logging.INFO)
# db_pool_fh.setFormatter(db_pool_formatter)
# db_pool_console_handler = logging.StreamHandler()
# db_pool_console_handler.setLevel(logging.INFO)
# db_pool_console_handler.setFormatter(db_pool_formatter)
# db_pool_logger.addHandler(db_pool_fh)
# db_pool_logger.addHandler(db_pool_console_handler)


class PoolDB(object):
    __conn__ = None
    __pool__ = None
    __dict_table__ = dict()

    def __init__(self):
        if not self.__pool__:
            self.__pool__ = PooledDB(creator=MySQLdb, mincached=2, maxcached=5, maxshared=0, maxconnections=6,
                                     blocking=True, host=host, user=user, passwd=password, db=db, charset="utf8", use_unicode=True)

    def __get_connect__(self):
        self.__conn__ = self.__pool__.connection()
        cursor = self.__conn__.cursor()
        if not cursor:
            raise BaseException(u"数据库连接不上")
        return cursor

    def find(self, sql, param=None, sql_analysis=True):
        cursor = self.__get_connect__()
        # self.__get_sql_query_param__(sql)
        try:
            if param:
                cursor.execute(sql, param)
            else:
                cursor.execute(sql)
            result = cursor.fetchall()
            if sql_analysis:
                list_query_param = self.__get_sql_query_param__(sql)
                data_list = list()
                for item in result:
                    data_dict = dict()
                    for (index, v) in enumerate(list_query_param):
                        data_dict[v.strip()] = item[index]
                    data_list.append(data_dict)
                return data_list
            else:
                return result
        except BaseException as e:
            # db_pool_logger.error("sql：%s" % sql)
            # db_pool_logger.error("sql param：%s" % param)
            # db_pool_logger.error(e)
            logger.error("sql：%s" % sql)
            logger.error("sql param：%s" % param)
            logger.error(e)
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
            # db_pool_logger.error("sql：%s" % sql)
            # db_pool_logger.error("sql param：%s" % param)
            # db_pool_logger.error(e)
            logger.error("sql：%s" % sql)
            logger.error("sql param：%s" % param)
            logger.error(e)
        finally:
            cursor.close()
            self.__conn__.close()

    def find_one(self, sql, param=None, sql_analysis=True):
        result = self.find(sql, param, sql_analysis)
        if result and len(result) > 0:
            return result[0]
        return None

    def __get_sql_query_param__(self, sql):
        """
        获得sql的所有查询的参数
        :param sql:
        :return: list
        """
        sql = sql.lower()
        result_list = list()
        split_word = ""
        # if "on" in sql:
        #     split_word = "on"
        # elif "where" in sql:
        #     split_word = "where"
        # elif not "on" in sql and not "where" in "sql":
        #     split_word = ";"
        split_word = "from"
        # 1:寻找子查询语句
        # TODO:寻找到所有子查询，做成数组，循环数组,暂不支持子查询
        if "(" in sql.split(split_word)[0]:
            if "select" in sql.split(split_word)[0].split("select")[1]:
                print u"暂不支持子查询"
                return list()
            else:
                temp_list = sql.split(split_word)[0].split("select")[1].split(",")
                for temp in temp_list:
                    result_list.append(temp.replace(" ", ""))
                return result_list
            return list()
        # 2：获得子查询语句的查询字段
        else:
            list_query_param = sql.split("select")[1].split("from")[0].split(",")
            # 存储查询的表名
            table_list = list()
            if "*" in sql:
                table_list = sql.split("from")[1].split("where")[0].split("left join")
                if len(table_list) == 0:
                    table_list = sql.split("from")[1].split("where")[0].split("right join")
                if len(table_list) == 0:
                    table_list = sql.split("from")[1].split("where")[0].split(",")
                if len(table_list) > len(list_query_param):
                    # 当使用 * 查询多张表数据时，一个*代表获取一张表的所有字段
                    list_query_param.append("*")
            for index, item_query_param in enumerate(list_query_param):
                if "*" in item_query_param:
                    list_all_coumns = self.__get_all_column_name_from_table__(table_list[index])
                    # 查询字段集做差集，寻找相同字段的查询
                    if result_list and len(set(result_list) ^ set(list_all_coumns)) > 0:
                        raise BaseException("column %s param is ambiguous" % list(set(result_list) ^ set(list_all_coumns)))
                    result_list += list_all_coumns
                    continue
                elif "as" in item_query_param:
                    item_query_param = item_query_param.split("as")[1].replace(" ", "")
                if item_query_param in result_list:
                    raise BaseException("column %s param is ambiguous" % item_query_param)
                result_list.append(item_query_param.replace(" ", ""))
            return result_list
        return result_list

    def __get_all_column_name_from_table__(self, table_name):
        table_name = table_name.replace(" ", "")
        if self.__dict_table__.get(table_name):
            return self.__dict_table__.get(table_name)
        cursor = self.__get_connect__()
        sql = """select COLUMN_NAME from information_schema.COLUMNS where table_name=%s and table_schema=%s"""
        result_list = list()
        try:
            cursor.execute(sql, [table_name, db])
            result = cursor.fetchall()
            for item in result:
                result_list.append(item[0])
            self.__dict_table__[table_name] = result_list
            return result_list
        except BaseException as e:
            print e
        finally:
            cursor.close()
            self.__conn__.close()

    # def _get_sub_sql_column_name(self, sql):
    #     """
    #     获得子查询查询的字段名称
    #     :param sql:
    #     :return:
    #     """
    #     dict_sub_sql = list()
    #     while True:
    #         sub_sql = sql.split("(")[1].split(")")[0]
    #
    #         sql = sql.replace("("+ sub_sql + ")", "")
    #         if not "(" in sql:
    #             break

pool = PoolDB()
