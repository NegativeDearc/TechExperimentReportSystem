# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from cPickle import dumps, loads

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
    test_quantity= db.Column(db.Integer,default=1)
    test_type    = db.Column(db.String(10),nullable=False)
    if_test      = db.Column(db.BOOLEAN,nullable=False,default=False)

    # 注意这边初始化的参数顺序！
    def __init__(self,id=None,request_id=None,test_content=None,
                 quantity=None,type=None,test=False):
        self.uuid         = id
        self.req_num      = request_id
        self.test_content = test_content
        self.test_quantity= quantity
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
                db.session.add(testContent(uuid_id,request_id,k,1,'A',self.if_test))
            else:
                pass

        # 耐久实验
        if form.getlist('endurance') and \
           len(form.getlist('endurance')) != len(form.getlist('endurance_quantity')):
            raise Exception('''Two list length did't match.''')
        else:
            for k,v in zip(form.getlist('endurance'),form.getlist('endurance_quantity')):
                db.session.add(testContent(uuid_id,request_id,k,v,'B',self.if_test))

        # 高速实验仅有一种条件
        if form.getlist('highspeed'):
            # zip会对所有可递归对象解包，字符串会被逐字分解，是个隐秘的出错点，在这里嵌套一层list
            for k,v in zip([form.get('highspeed')],[form.get('highspeed_quantity')]):
                print k,v
                db.session.add(testContent(uuid_id,request_id,k,v,'C',self.if_test))
        else:
            pass

        # 提交,切记:try-except块会隐藏问题,如果有不明的的错误,在debug时打印Expection明细
        db.session.commit()
        db.session.close()


class Highspeed(db.Model):
    '''
    储存高速测试条件,
    以速度等级/测试标准区分
    '''
    __tablename__= 'highspeed_test'
    id                 = db.Column(db.Integer,nullable=False,primary_key=True)
    ref                = db.Column(db.String(10),nullable=False,unique=True)
    speed_level        = db.Column(db.String(5),nullable=False)
    load_capcity_ratio = db.Column(db.Float(2),nullable=False)
    remark             = db.Column(db.String(5))

    time_1       = db.Column(db.Integer,nullable=False)
    speed_1      = db.Column(db.Integer,nullable=False)
    mile_1       = db.Column(db.Float(3),nullable=False)
    total_1      = db.Column(db.Float(3))

    time_2       = db.Column(db.Integer,nullable=False)
    speed_2      = db.Column(db.Integer,nullable=False)
    mile_2       = db.Column(db.Float(3),nullable=False)
    total_2      = db.Column(db.Float(3))

    time_3       = db.Column(db.Integer,nullable=False)
    speed_3      = db.Column(db.Integer,nullable=False)
    mile_3       = db.Column(db.Float(3),nullable=False)
    total_3      = db.Column(db.Float(3))

    time_4       = db.Column(db.Integer,nullable=False)
    speed_4      = db.Column(db.Integer,nullable=False)
    mile_4       = db.Column(db.Float(3),nullable=False)
    total_4      = db.Column(db.Float(3))

    time_5       = db.Column(db.Integer,nullable=False)
    speed_5      = db.Column(db.Integer,nullable=False)
    mile_5       = db.Column(db.Float(3),nullable=False)
    total_5      = db.Column(db.Float(3))

    time_6       = db.Column(db.Integer)
    speed_6      = db.Column(db.Integer)
    mile_6       = db.Column(db.Float(3))
    total_6      = db.Column(db.Float(3))

    time_7       = db.Column(db.Integer)
    speed_7      = db.Column(db.Integer)
    mile_7       = db.Column(db.Float(3))
    total_7      = db.Column(db.Float(3))

    time_8       = db.Column(db.Integer)
    speed_8      = db.Column(db.Integer)
    mile_8       = db.Column(db.Float(3))
    total_8      = db.Column(db.Float(3))

    time_9       = db.Column(db.Integer)
    speed_9      = db.Column(db.Integer)
    mile_9       = db.Column(db.Float(3))
    total_9      = db.Column(db.Float(3))

    time_10       = db.Column(db.Integer)
    speed_10      = db.Column(db.Integer)
    mile_10       = db.Column(db.Float(3))
    total_10      = db.Column(db.Float(3))

    time_11       = db.Column(db.Integer)
    speed_11      = db.Column(db.Integer)
    mile_11       = db.Column(db.Float(3))
    total_11      = db.Column(db.Float(3))

    time_12       = db.Column(db.Integer)
    speed_12      = db.Column(db.Integer)
    mile_12       = db.Column(db.Float(3))
    total_12      = db.Column(db.Float(3))

    time_13       = db.Column(db.Integer)
    speed_13      = db.Column(db.Integer)
    mile_13       = db.Column(db.Float(3))
    total_13      = db.Column(db.Float(3))

    time_14       = db.Column(db.Integer)
    speed_14      = db.Column(db.Integer)
    mile_14       = db.Column(db.Float(3))
    total_14      = db.Column(db.Float(3))

    time_15       = db.Column(db.Integer)
    speed_15      = db.Column(db.Integer)
    mile_15       = db.Column(db.Float(3))
    total_15      = db.Column(db.Float(3))

    time_16       = db.Column(db.Integer)
    speed_16      = db.Column(db.Integer)
    mile_16       = db.Column(db.Float(3))
    total_16      = db.Column(db.Float(3))

    def __init__(self,kwargs):
        self.ref                     = kwargs['info'][0]
        self.speed_level             = kwargs['info'][1]
        self.load_capcity_ratio      = kwargs['info'][2]

        self.time_1      = kwargs['step_1'][0]
        self.speed_1     = kwargs['step_1'][1]
        self.mile_1      = kwargs['step_1'][2]
        self.total_1     = kwargs['step_1'][3]

        self.time_2      = kwargs['step_2'][0]
        self.speed_2     = kwargs['step_2'][1]
        self.mile_2      = kwargs['step_2'][2]
        self.total_2     = kwargs['step_2'][3]

        self.time_3      = kwargs['step_3'][0]
        self.speed_3     = kwargs['step_3'][1]
        self.mile_3      = kwargs['step_3'][2]
        self.total_3     = kwargs['step_3'][3]

        self.time_4      = kwargs['step_4'][0]
        self.speed_4     = kwargs['step_4'][1]
        self.mile_4      = kwargs['step_4'][2]
        self.total_4     = kwargs['step_4'][3]

        self.time_5      = kwargs['step_5'][0]
        self.speed_5     = kwargs['step_5'][1]
        self.mile_5      = kwargs['step_5'][2]
        self.total_5     = kwargs['step_5'][3]

        self.time_6      = kwargs['step_6'][0]
        self.speed_6     = kwargs['step_6'][1]
        self.mile_6      = kwargs['step_6'][2]
        self.total_6     = kwargs['step_6'][3]

        self.time_7      = kwargs['step_7'][0]
        self.speed_7     = kwargs['step_7'][1]
        self.mile_7      = kwargs['step_7'][2]
        self.total_7     = kwargs['step_7'][3]

        self.time_8      = kwargs['step_8'][0]
        self.speed_8     = kwargs['step_8'][1]
        self.mile_8      = kwargs['step_8'][2]
        self.total_8     = kwargs['step_8'][3]

        self.time_9      = kwargs['step_9'][0]
        self.speed_9     = kwargs['step_9'][1]
        self.mile_9      = kwargs['step_9'][2]
        self.total_9     = kwargs['step_9'][3]

        self.time_10     = kwargs['step_10'][0]
        self.speed_10    = kwargs['step_10'][1]
        self.mile_10     = kwargs['step_10'][2]
        self.total_10    = kwargs['step_10'][3]

        self.time_11     = kwargs['step_11'][0]
        self.speed_11    = kwargs['step_11'][1]
        self.mile_11     = kwargs['step_11'][2]
        self.total_11    = kwargs['step_11'][3]

        self.time_12     = kwargs['step_12'][0]
        self.speed_12    = kwargs['step_12'][1]
        self.mile_12     = kwargs['step_12'][2]
        self.total_12    = kwargs['step_12'][3]

        self.time_13     = kwargs['step_13'][0]
        self.speed_13    = kwargs['step_13'][1]
        self.mile_13     = kwargs['step_13'][2]
        self.total_13    = kwargs['step_13'][3]

        self.time_14     = kwargs['step_14'][0]
        self.speed_14    = kwargs['step_14'][1]
        self.mile_14     = kwargs['step_14'][2]
        self.total_14    = kwargs['step_14'][3]

        self.time_15     = kwargs['step_15'][0]
        self.speed_15    = kwargs['step_15'][1]
        self.mile_15     = kwargs['step_15'][2]
        self.total_15    = kwargs['step_15'][3]

        self.time_16     = kwargs['step_16'][0]
        self.speed_16    = kwargs['step_16'][1]
        self.mile_16     = kwargs['step_16'][2]
        self.total_16    = kwargs['step_16'][3]


# class Endurance(db.Model):
#     '''
#     耐久测试数据表
#     '''
#     __tablename__ = 'endurance_test'
#     id            = db.Column(db.Integer,primary_key=True,nullable=False)

class ReportDetail(db.Model):
    '''
    存储测试记录的表
    =============
    每次开发组用户提交了测试需求之后，本表自动生成一份记录,记录其uuid和测试数据已经测试名目，
    其中test_data，存储pickle之后的json(dict)文件，uuid作为唯一标识符
    '''
    __tablename__ = 'reportDetail'

    id           = db.Column(db.Integer,primary_key=True,nullable=False)
    uuid         = db.Column(db.String(20),nullable=False)
    test_content = db.Column(db.String(10),nullable=False,unique=True)
    test_data    = db.Column(db.BLOB)

    def __init__(self,uuid=None,test_content=None,test_data=None):
        self.uuid         = uuid
        self.test_content = test_content
        self.test_data    = test_data