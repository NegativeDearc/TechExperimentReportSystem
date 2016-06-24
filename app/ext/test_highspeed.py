# -*- coding:itf-8 -*-
__author__ = 'SXChen'

from app import db
from app.models.dbModels import Highspeed
from app.models.dbModels import requestForms
from app.models.dbModels import testContent


def highspeed_test_quantity(uuid):
    quantity = db.session.query(testContent.test_quantity).\
        filter(testContent.uuid == uuid,
               testContent.test_type == 'C').first()
    return int(quantity.req_num)

