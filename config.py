# -*- coding:utf-8 -*-
__author__ = 'SXChen'

import os
from sys import platform

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = 'e2e4c130-23a4-11e6-b47c-d4bed9840544'       #uuid生成
    SQLALCHEMY_ECHO = False                                   #日志显示
    SQLALCHEMY_TRACK_MODIFICATIONS = True                     #消除警告,默认配置为None
    PERMANENT_SESSION_LIFETIME = 3600                         #session过期时间 30 min
    ALLOWED_UPLOAD_FILE = set(['csv'])

    if platform.startswith('win'):
        DATABASE_PATH = basedir + '\\app\models\TIRE_TEST_DB'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + basedir + '\\app\models\TIRE_TEST_DB'
        TEST_TEMPLATE_FILES = basedir + "\\app\\static\\files\\"
    else:
        DATABASE_PATH = basedir + '/app/models/TIRE_TEST_DB'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + basedir + '/app/models/TIRE_TEST_DB'
        TEST_TEMPLATE_FILES = basedir + "/app/static/files/"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    SQLALCHEMY_ECHO = False


config = {
    'development':DevelopmentConfig,
    'production' :ProductionConfig,
    'default'    :DevelopmentConfig
}