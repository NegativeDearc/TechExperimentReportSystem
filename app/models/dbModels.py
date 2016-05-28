# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


class usrPwd(db.Model):
    '''
    存储用户名和密码的表
    user:    用户工号
    password:默认111111
    group:   分组，管理员0，开发组1，测试组2
    '''
    __tablename__ = 'USER_PASSWORD'
    user = db.Column(db.Text(50), nullable=False, unique=True, primary_key=True)
    password = db.Column(db.Text(50), nullable=False)
    group = db.Column(db.Text(10), nullable=False)

    def __init__(self, user=None, password=None, group=None):
        self.user = user
        self.password = password
        self.group = group

    @property
    def pwd(self):
        raise AttributeError('Password is not a readable attribute')

    @pwd.setter
    def pwd(self, pwd):
        self.password = generate_password_hash(pwd, salt_length=16)

    def verify_pwd(self, pwd):
        return check_password_hash(self.password, pwd)
