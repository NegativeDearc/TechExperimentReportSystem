# -*- coding:utf-8 -*-

import logging
import os
from app import app


class AppLog(object):
    # 必须加入object产生新式类，否则在子类继承使用super()复写父类的时候出错
    # 根据不同的需求制定不同的日志模块
    def __init__(self):
        # os.pardir -> parent directory
        self.__log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + '/logs/log.txt'
        self.handler = logging.FileHandler(self.__log_path)
        self.formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        # settings
        self.handler.setFormatter(self.formatter)
        self.handler.setLevel(logging.DEBUG)

    # 用户访问的ip
    def visitor_ip(self):
        logger = logging.getLogger('visitor_ip')
        logger.addHandler(self.handler)
        logger.warning('')

    # form post data
    def form_post(self):
        logger = logging.getLogger('form_post')
        logger.addHandler(self.handler)


class DebugFalseLog(AppLog):
    def __init__(self):
        super(DebugFalseLog, self).__init__()
        self.formatter = app.debug_log_format
        self.handler.setLevel(logging.ERROR)

    def get_handler(self):
        return self.handler