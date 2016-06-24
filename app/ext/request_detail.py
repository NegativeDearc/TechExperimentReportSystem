# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import requestForms,testContent
from collections import OrderedDict
from prettytable import PrettyTable


class requestDetail(object):
    '''
    已经提出需求的明细,以人名筛选,progress达到100%后停止显示
    '''

    def __init__(self,session):
        self.name = session.get('usr')

        if self.name is None:
            raise Exception('''Request name can't be none.''')

    def summary(self):
        # 获取正在进行任务的唯一编号
        uid = db.session.query(requestForms.req_num).\
            filter(requestForms.name == self.name,
                   requestForms.check == False).\
            all()

        res = OrderedDict()
        for i in uid:
            tb = PrettyTable(field_names=[
                'Request id',
                'uuid',
                'User',
                'Request Date',
                'Max load',
                'Max Inflate',
                'Temperature',
                'Test item',
                'Test type',
                'Quantity',
                'Tested?'
            ])

            detail = db.session.query(requestForms,testContent).\
                outerjoin(testContent,requestForms.req_num == testContent.req_num).\
                filter(requestForms.req_num == i.req_num).\
                all()

            for v in detail:
                tb.add_row([
                    v.requestForms.req_num,
                    v.requestForms.uuid,
                    v.requestForms.name,
                    v.requestForms.date,
                    v.requestForms.load,
                    v.requestForms.inflate,
                    v.requestForms.temp,
                    v.testContent.test_content,
                    v.testContent.test_type,
                    v.testContent.test_quantity,
                    v.testContent.if_test
                ])
            res.update({
                i.req_num:tb
            })
        return res