# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import Highspeed
from app.models.dbModels import testContent
from collections import OrderedDict


def highspeed_test_quantity(uuid):
    # 高速测试条件可能有多种，每一种测试的条数也不一样
    quantity = db.session.query(testContent.test_content,testContent.test_quantity).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'C').all()
    data = dict(quantity)

    res = db.session.query(testContent.req_num).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'C').first()
    return data,res.req_num


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
            if eval('df.time_' +str(v)) != 0:
                res.update({
                    str(v):
                        {'time' :eval('df.time_' +str(v)),
                         'speed':eval('df.speed_'+str(v)),
                         'mile' :eval('df.mile_' +str(v)),
                         'total':eval('df.total_'+str(v))
                         }
                })
        return res
        # res 是有序字典，这个特性在以后可以被使用到
    else:
        raise Exception('Get Nothing From Database.')


def formatted_dict(form):
        '''
        格式化request.form
        供数据库Highspeed插入数据
        '''
        d  = OrderedDict(form)
        dd = {}

        step = ['step_' + str(x) for x in range(17)[1:]]
        a = ['a' + str(x) for x in range(17)[1:]]
        b = ['b' + str(x) for x in range(17)[1:]]
        e = ['e' + str(x) for x in range(17)[1:]]
        c = ['c' + str(x) for x in range(4)[1:]]

        for x,y,w,z in zip(a,b,e,step):
            j = d.get(x,0)
            k = d.get(y,0)
            m = d.get(w,0)

            if j != '' and k != '' and m !='':
                j = float(j)
                k = float(k)
                m = float(m)
            else:
                j = 0
                k = 0
                m = 0

            l = round(k/60*j,2)
            dd[z] = (j,k,l,m)

        dd['info'] = tuple([d.get(n) for n in c])
        return dd