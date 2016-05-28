# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

import datetime



class usrPwd(db.Model):
    '''
    存储用户名和密码的表
    user:    用户工号
    password:默认111111
    group:   分组，管理员0，开发组1，测试组2
    '''
    __tablename__ = 'USER_PASSWORD'
    user     = db.Column(db.Text(50), nullable=False, unique=True, primary_key=True)
    password = db.Column(db.Text(50), nullable=False)
    group    = db.Column(db.Text(10), nullable=False)

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


class requestForms(db.Model):
    '''
    记录/developer提交的数据
    id:uuid 生成
    name: 登陆的用户名

    本数据库一次直生成一条记录,req_num不可重复
    '''
    __tablename__ = 'requestForm'

    # 初始化内容
    id      = db.Column(db.Integer,nullable=False,unique=True,primary_key=True)
    uuid    = db.Column(db.String(50),nullable=False)
    name    = db.Column(db.String(15),nullable=False)
    date    = db.Column(db.DATE,nullable=False)
    check   = db.Column(db.BOOLEAN,nullable=False,default=False)
    process = db.Column(db.Float(5))

    # 轮胎基本信息
    purpose = db.Column(db.String(30),nullable=False)
    size    = db.Column(db.String(30),nullable=False)
    req_num = db.Column(db.String(50),nullable=False,unique=True)
    brand   = db.Column(db.String(50),nullable=False)
    temp    = db.Column(db.Float(10),nullable=False)
    load    = db.Column(db.Integer,nullable=False)
    inflate = db.Column(db.Integer,nullable=False)
    # 备注
    remark    = db.Column(db.String(50))

    def __init__(self,form,session):
        # 为了提高健壮性,初始化时应当做必要检查
        self.uuid    = session.get('uuid_id')
        self.name    = session.get('usr')
        self.date    = datetime.date.today()
        self.check   = False
        self.process = 0.0

        # 注意form中都是unicode 是否需要类型转换 酌情处理
        self.purpose = form.get('purpose')
        self.size    = form.get('size')
        self.req_num = form.get('request_id')
        self.brand   = form.get('pattern')
        self.temp    = form.get('temp')
        self.load    = form.get('max_load')
        self.inflate = form.get('max_inflate')

    def add_data(self):
        db.session.add(self)
        db.session.commit()
        db.session.close()

    # 更新测试进度指示,只有完成所有测试,self.check才会被更新成True,以示完成
    @hybrid_property
    def update_process(self):
        pass


class testContent(db.Model):
    '''
    uuid 对应的测试项目
    test_type: A 静态测试
               B 耐久测试
               C 高速测试

    本数据库一次会插入多条记录,目前仍有问题,数据有可能被重复插入
    '''
    __tablename__ = 'testForm'

    id           = db.Column(db.Integer,nullable=False,unique=True,primary_key=True)
    uuid         = db.Column(db.String(50),nullable=False)
    req_num      = db.Column(db.String(50),nullable=False)
    test_content = db.Column(db.String(20),nullable=False)
    test_type    = db.Column(db.String(10),nullable=False)
    if_test      = db.Column(db.BOOLEAN,nullable=False,default=False)

    def __init__(self,id=None,request_id=None,test_content=None,type=None,test=False):
        self.uuid         = id
        self.req_num      = request_id
        self.test_content = test_content
        self.test_type    = type
        self.if_test      = test

    def add_data(self,form,session):
        '''
        批量插入测试内容
        :param session: 来自session
        :param form: 来自request.form;
        :return:
        '''
        uuid_id   = session.get('uuid_id')
        request_id = form.get('request_id')
        # 若已经存在request_id,则产生错误阻止插入数据
        # first()提取第一条数据,one() 提取一条,若遇多条则报错
        if db.session. \
                query(testContent).\
                filter(testContent.req_num == request_id). \
                first():
            raise Exception('''Request id is already existed.Can't insert records.''')

        # 静态测试
        for k in form:
            if k in ['dim','unseat','plunger','footprint']:
                db.session.add(testContent(uuid_id,request_id,k,'A',self.if_test))
            else:
                pass

        # 耐久实验
        if form.getlist('endurance'):
            for k in form.getlist('endurance'):
                db.session.add(testContent(uuid_id,request_id,k,'B',self.if_test))
        else:
            pass

        # 高速实验
        if form.getlist('highspeed'):
            for k in form.getlist('highspeed'):
                db.session.add(testContent(uuid_id,request_id,k,'C',self.if_test))
        else:
            pass

        # 提交,切记:try-except块会隐藏问题,如果有不明的的错误,在debug时打印Expection明细
        db.session.commit()
        db.session.close()