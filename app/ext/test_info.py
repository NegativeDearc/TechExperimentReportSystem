# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import testContent, requestForms


class testInfo(object):
    '''
    以request number为id 处理数据
    '''
    def __init__(self):
        __number_set = db.session.query(requestForms.req_num).\
            group_by(requestForms.req_num).\
            all()

        self.req_number = [x.req_num for x in __number_set]

    def test_info(self):
        d = []
        for num in self.req_number:
            # m ---> requestForms
            # n ---> testContent
            v = []
            data = db.session.query(requestForms,testContent).\
                outerjoin(testContent,requestForms.uuid == testContent.uuid).\
                filter(testContent.if_test == False, testContent.req_num == num).\
                order_by(requestForms.name).\
                all()
            for m,n in data:
                if n.test_type == 'A':
                    url = '/report/static/' + n.uuid + '/'
                if n.test_type == 'B':
                    url = 'report/endurance/' + n.uuid
                if n.test_type == 'C':
                    url = '/report/highspeed/' + n.uuid

                v.append([m.name,
                          m.date,
                          m.purpose,
                          n.test_content,
                          n.test_type,
                          n.test_quantity,
                          n.if_test,
                          url,
                          n.uuid])
            d.append(dict(id=num,content=v))
        return d