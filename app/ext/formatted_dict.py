# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from collections import OrderedDict


def formatted_dict(form):
        '''
        格式化request.form
        供数据库插入
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