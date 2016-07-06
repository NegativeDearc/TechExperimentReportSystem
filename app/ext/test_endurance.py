# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import testContent
from app.models.dbModels import Endurance
from collections import OrderedDict


def endurance_test_quantity(uuid):
    # 耐久试条件未来也可能有多种，每一种测试的条数也不一样
    quantity = db.session.query(testContent.test_content,testContent.test_quantity).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'B').all()
    data = dict(quantity)
    return data


def data_to_tb(ref):
    '''
    接收一个参数来查询数据库记录，
    同时格式化数据供ajax使用
    '''
    df = db.session.query(Endurance).filter(Endurance.ref == ref).first()
    if df:
        # 全部转为字典,才能json化
        res = OrderedDict(info=dict(ref=df.ref))
        # 处理阶段
        for v in range(17)[1:]:
            if eval('df.time_' +str(v)) != 0:
                res.update({
                    str(v):
                        {'time' :eval('df.time_' +str(v)),
                         'speed':eval('df.speed_'+str(v)),
                         'mile' :eval('df.mile_' +str(v)),
                         'total':eval('df.total_'+str(v)),
                         'load' :eval('df.load_'+str(v))
                         }
                })
        # 处理低压数据
        if eval('df.low_pressure_time_1') != 0:
            res.update({
                'low pressure':{
                    'time' :eval('df.low_pressure_time_1'),
                    'speed':eval('df.low_pressure_speed_1'),
                    'mile' :eval('df.low_pressure_mile_1'),
                    'total':eval('df.low_pressure_total_1'),
                    'load' :eval('df.low_pressure_load_1')
                }
            })
        return res
        # res 是有序字典，这个特性在以后可以被使用到
    else:
        raise Exception('Get Nothing From Database.')