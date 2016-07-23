# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import testContent, requestForms
from itertools import chain


def total_static_test_content(uuid):
    # 静态测试有4种，实际情况可能测试其中若干种
    # total 提取所有测试名称
    total = db.session.query(testContent.test_content).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'A').\
        all()
    # 解包
    total = list(chain(*total))
    res = db.session.query(testContent.req_num).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'A').\
        first()
    return total,res.req_num


def static_test_request_detail(uuid):
    # 获取当初测试需求的信息
    df = db.session.query(requestForms.size,
                          requestForms.req_num,
                          requestForms.brand,
                          requestForms.purpose,
                          requestForms.load,
                          requestForms.inflate,
                          requestForms.name).\
        filter(requestForms.uuid == uuid).\
        all()
    # 生成字典
    df = list(chain(*df))
    d  = {}

    for item in zip(['size','req_num','brand','purpose','load','inflate','proposer'],df):
        d.update({item[0]:item[1]})

    return d