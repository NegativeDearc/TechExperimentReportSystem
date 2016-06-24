# -*- coding:utf-8 -*-

from app import db
from app.models.dbModels import Highspeed
from collections import OrderedDict


def data_to_table(ref):
    '''
    接收一个参数来查询数据库记录，
    同时格式化数据供ajax使用
    '''
    df = db.session.query(Highspeed).filter(Highspeed.ref == ref).first()
    if df:
        # 全部转为字典,才能json化
        res = OrderedDict(
            info=dict(ref=df.ref,
                      level=df.speed_level,
                      load=df.load_capcity_ratio,
                      remark=df.remark)
        )
        # 处理阶段
        for v in range(17)[1:]:
            res.update({
                str(v):
                    {'time' :eval('df.time_' +str(v)),
                     'speed':eval('df.speed_'+str(v)),
                     'mile' :eval('df.mile_' +str(v)),
                     'total':eval('df.total_'+str(v))
                     }
            })
        return res
    else:
        raise Exception('Get Nothing From Database.')