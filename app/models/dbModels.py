# -*- coding:utf-8 -*-
__author__ = 'SXChen'

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from cPickle import dumps, loads
import datetime


class usrPwd(db.Model):
    """
    存储用户名和密码的表
    user:    用户工号
    password:默认111111
    group:   分组，管理员0，开发组1，测试组2
    """
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
    """
    记录/developer提交的数据
    id:uuid 生成
    name: 登陆的用户名

    本数据库一次直生成一条记录,req_num不可重复
    """
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
    temp    = db.Column(db.String(10),nullable=False)            # A or B
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
    """
    uuid 对应的测试项目
    test_type: A 静态测试
               B 耐久测试
               C 高速测试

    本数据库一次会插入多条记录,目前仍有问题,数据有可能被重复插入
    """
    __tablename__ = 'testForm'

    id           = db.Column(db.Integer,nullable=False,unique=True,primary_key=True)
    uuid         = db.Column(db.String(50),nullable=False)
    req_num      = db.Column(db.String(50),nullable=False)
    test_content = db.Column(db.String(20),nullable=False)
    test_quantity= db.Column(db.Integer,default=1)
    test_type    = db.Column(db.String(10),nullable=False)
    if_test      = db.Column(db.BOOLEAN,nullable=False,default=False)
    # test_progress= db.Column(db.Float(3),default=0)

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
        """
        批量插入测试内容
        :param session: 来自session
        :param form: 来自request.form;
        :return:
        """
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

        # 高速实验
        if form.getlist('highspeed'):
            # zip会对所有可递归对象解包，字符串会被逐字分解，是个隐秘的出错点，在这里嵌套一层list
            for k,v in zip(form.getlist('highspeed'),form.getlist('highspeed_quantity')):
                db.session.add(testContent(uuid_id,request_id,k,v,'C',self.if_test))
        else:
            pass

        if form.getlist('highspeed_1'):
            for k,v in zip(form.getlist('highspeed_1'),form.getlist('highspeed_quantity_1')):
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


class Endurance(db.Model):
    '''
    耐久测试数据表,到底是逐条数据维护呢，还是直接填入pickle化的数据
    '''
    __tablename__ = 'endurance_test'
    id            = db.Column(db.Integer,primary_key=True,nullable=False)
    ref           = db.Column(db.String(10),nullable=False)

    time_1       = db.Column(db.Integer,nullable=False)
    speed_1      = db.Column(db.Float(3),nullable=False)
    mile_1       = db.Column(db.Float(3),nullable=False)
    total_1      = db.Column(db.Float(3))
    load_1       = db.Column(db.Float(3))

    time_2       = db.Column(db.Integer,nullable=False)
    speed_2      = db.Column(db.Float(3),nullable=False)
    mile_2       = db.Column(db.Float(3),nullable=False)
    total_2      = db.Column(db.Float(3))
    load_2       = db.Column(db.Float(3))

    time_3       = db.Column(db.Integer,nullable=False)
    speed_3      = db.Column(db.Float(3),nullable=False)
    mile_3       = db.Column(db.Float(3),nullable=False)
    total_3      = db.Column(db.Float(3))
    load_3       = db.Column(db.Float(3))

    time_4       = db.Column(db.Integer,nullable=False)
    speed_4      = db.Column(db.Float(3),nullable=False)
    mile_4       = db.Column(db.Float(3),nullable=False)
    total_4      = db.Column(db.Float(3))
    load_4       = db.Column(db.Float(3))

    time_5       = db.Column(db.Integer,nullable=False)
    speed_5      = db.Column(db.Float(3),nullable=False)
    mile_5       = db.Column(db.Float(3),nullable=False)
    total_5      = db.Column(db.Float(3))
    load_5       = db.Column(db.Float(3))

    time_6       = db.Column(db.Integer)
    speed_6      = db.Column(db.Float(3))
    mile_6       = db.Column(db.Float(3))
    total_6      = db.Column(db.Float(3))
    load_6       = db.Column(db.Float(3))

    time_7       = db.Column(db.Integer)
    speed_7      = db.Column(db.Float(3))
    mile_7       = db.Column(db.Float(3))
    total_7      = db.Column(db.Float(3))
    load_7       = db.Column(db.Float(3))

    time_8       = db.Column(db.Integer)
    speed_8      = db.Column(db.Float(3))
    mile_8       = db.Column(db.Float(3))
    total_8      = db.Column(db.Float(3))
    load_8      = db.Column(db.Float(3))

    time_9       = db.Column(db.Integer)
    speed_9      = db.Column(db.Float(3))
    mile_9       = db.Column(db.Float(3))
    total_9      = db.Column(db.Float(3))
    load_9       = db.Column(db.Float(3))

    time_10       = db.Column(db.Integer)
    speed_10      = db.Column(db.Float(3))
    mile_10       = db.Column(db.Float(3))
    total_10      = db.Column(db.Float(3))
    load_10       = db.Column(db.Float(3))

    time_11       = db.Column(db.Integer)
    speed_11      = db.Column(db.Float(3))
    mile_11       = db.Column(db.Float(3))
    total_11      = db.Column(db.Float(3))
    load_11       = db.Column(db.Float(3))

    time_12       = db.Column(db.Integer)
    speed_12      = db.Column(db.Float(3))
    mile_12       = db.Column(db.Float(3))
    total_12      = db.Column(db.Float(3))
    load_12       = db.Column(db.Float(3))

    time_13       = db.Column(db.Integer)
    speed_13      = db.Column(db.Float(3))
    mile_13       = db.Column(db.Float(3))
    total_13      = db.Column(db.Float(3))
    load_13       = db.Column(db.Float(3))

    time_14       = db.Column(db.Integer)
    speed_14      = db.Column(db.Float(3))
    mile_14       = db.Column(db.Float(3))
    total_14      = db.Column(db.Float(3))
    load_14       = db.Column(db.Float(3))

    time_15       = db.Column(db.Integer)
    speed_15      = db.Column(db.Float(3))
    mile_15       = db.Column(db.Float(3))
    total_15      = db.Column(db.Float(3))
    load_15       = db.Column(db.Float(3))

    time_16       = db.Column(db.Integer)
    speed_16      = db.Column(db.Float(3))
    mile_16       = db.Column(db.Float(3))
    total_16      = db.Column(db.Float(3))
    load_16       = db.Column(db.Float(3))

    low_pressure_time_1       = db.Column(db.Integer)
    low_pressure_speed_1      = db.Column(db.Float(3))
    low_pressure_mile_1       = db.Column(db.Float(3))
    low_pressure_total_1      = db.Column(db.Float(3))
    low_pressure_load_1       = db.Column(db.Float(3))

    def __init__(self,kwargs):
        '''
        **kwargs --> request.form
        '''
        d = {}
        for k,v in kwargs.items():
            if len(v) == 0:
                v = 0
            d.update({k:v})

        kwargs = d

        def mile(time,speed):
            try:
                float(time)
            except ValueError:
                time = 0
            try:
                float(speed)
            except ValueError:
                speed = 0
            return round(float(time) * float(speed),2)

        self.ref         = kwargs.get('endurance_ref')

        self.time_1      = kwargs.get('endurance_time_1',0)
        self.speed_1     = kwargs.get('endurance_speed_1',0)
        self.mile_1      = mile(kwargs.get('endurance_time_1',0),kwargs.get('endurance_speed_1',0))
        self.total_1     = kwargs.get('endurance_total_1',0)
        self.load_1      = kwargs.get('endurance_load_1',0)

        self.time_2      = kwargs.get('endurance_time_2',0)
        self.speed_2     = kwargs.get('endurance_speed_2',0)
        self.mile_2      = mile(kwargs.get('endurance_time_2',0),kwargs.get('endurance_speed_2',0))
        self.total_2     = kwargs.get('endurance_total_2',0)
        self.load_2      = kwargs.get('endurance_load_2',0)

        self.time_3      = kwargs.get('endurance_time_3',0)
        self.speed_3     = kwargs.get('endurance_speed_3',0)
        self.mile_3      = mile(kwargs.get('endurance_time_3',0),kwargs.get('endurance_speed_3',0))
        self.total_3     = kwargs.get('endurance_total_3',0)
        self.load_3      = kwargs.get('endurance_load_3',0)

        self.time_4      = kwargs.get('endurance_time_4',0)
        self.speed_4     = kwargs.get('endurance_speed_4',0)
        self.mile_4      = mile(kwargs.get('endurance_time_4',0),kwargs.get('endurance_speed_4',0))
        self.total_4     = kwargs.get('endurance_total_4',0)
        self.load_4      = kwargs.get('endurance_load_4',0)

        self.time_5      = kwargs.get('endurance_time_5',0)
        self.speed_5     = kwargs.get('endurance_speed_5',0)
        self.mile_5      = mile(kwargs.get('endurance_time_5',0),kwargs.get('endurance_speed_5',0))
        self.total_5     = kwargs.get('endurance_total_5',0)
        self.load_5      = kwargs.get('endurance_load_5',0)

        self.time_6      = kwargs.get('endurance_time_6',0)
        self.speed_6     = kwargs.get('endurance_speed_6',0)
        self.mile_6      = mile(kwargs.get('endurance_time_6',0),kwargs.get('endurance_speed_6',0))
        self.total_6     = kwargs.get('endurance_total_6',0)
        self.load_6      = kwargs.get('endurance_load_6',0)

        self.time_7      = kwargs.get('endurance_time_7',0)
        self.speed_7     = kwargs.get('endurance_speed_7',0)
        self.mile_7      = mile(kwargs.get('endurance_time_7',0),kwargs.get('endurance_speed_7',0))
        self.total_7     = kwargs.get('endurance_total_7',0)
        self.load_7      = kwargs.get('endurance_load_7',0)

        self.time_8      = kwargs.get('endurance_time_8',0)
        self.speed_8     = kwargs.get('endurance_speed_8',0)
        self.mile_8      = mile(kwargs.get('endurance_time_8',0),kwargs.get('endurance_speed_8',0))
        self.total_8     = kwargs.get('endurance_total_8',0)
        self.load_8      = kwargs.get('endurance_load_8',0)

        self.time_9      = kwargs.get('endurance_time_9',0)
        self.speed_9     = kwargs.get('endurance_speed_9',0)
        self.mile_9      = mile(kwargs.get('endurance_time_9',0),kwargs.get('endurance_speed_9',0))
        self.total_9     = kwargs.get('endurance_total_9',0)
        self.load_9      = kwargs.get('endurance_load_9',0)

        self.time_10      = kwargs.get('endurance_time_10',0)
        self.speed_10     = kwargs.get('endurance_speed_10',0)
        self.mile_10      = mile(kwargs.get('endurance_time_10',0),kwargs.get('endurance_speed_10',0))
        self.total_10     = kwargs.get('endurance_total_10',0)
        self.load_10      = kwargs.get('endurance_load_10',0)

        self.time_11      = kwargs.get('endurance_time_11',0)
        self.speed_11     = kwargs.get('endurance_speed_11',0)
        self.mile_11      = mile(kwargs.get('endurance_time_11',0),kwargs.get('endurance_speed_11',0))
        self.total_11     = kwargs.get('endurance_total_11',0)
        self.load_11      = kwargs.get('endurance_load_11',0)

        self.time_12      = kwargs.get('endurance_time_12',0)
        self.speed_12     = kwargs.get('endurance_speed_12',0)
        self.mile_12      = mile(kwargs.get('endurance_time_12',0),kwargs.get('endurance_speed_12',0))
        self.total_12     = kwargs.get('endurance_total_12',0)
        self.load_12      = kwargs.get('endurance_load_12',0)

        self.time_13      = kwargs.get('endurance_time_13',0)
        self.speed_13     = kwargs.get('endurance_speed_13',0)
        self.mile_13      = mile(kwargs.get('endurance_time_13',0),kwargs.get('endurance_speed_13',0))
        self.total_13     = kwargs.get('endurance_total_13',0)
        self.load_13      = kwargs.get('endurance_load_13',0)

        self.time_14      = kwargs.get('endurance_time_14',0)
        self.speed_14     = kwargs.get('endurance_speed_14',0)
        self.mile_14      = mile(kwargs.get('endurance_time_14',0),kwargs.get('endurance_speed_14',0))
        self.total_14     = kwargs.get('endurance_total_14',0)
        self.load_14      = kwargs.get('endurance_load_14',0)

        self.time_15      = kwargs.get('endurance_time_15',0)
        self.speed_15     = kwargs.get('endurance_speed_15',0)
        self.mile_15      = mile(kwargs.get('endurance_time_15',0),kwargs.get('endurance_speed_15',0))
        self.total_15     = kwargs.get('endurance_total_15',0)
        self.load_15      = kwargs.get('endurance_load_15',0)

        self.time_16      = kwargs.get('endurance_time_16',0)
        self.speed_16     = kwargs.get('endurance_speed_16',0)
        self.mile_16      = mile(kwargs.get('endurance_time_16',0),kwargs.get('endurance_speed_16',0))
        self.total_16     = kwargs.get('endurance_total_16',0)
        self.load_16      = kwargs.get('endurance_load_16',0)

        self.low_pressure_time_1   = kwargs.get('low_pressure_endurance_time_1',0)
        self.low_pressure_speed_1  = kwargs.get('low_pressure_endurance_speed_1',0)
        self.low_pressure_mile_1   = mile(kwargs.get('low_pressure_endurance_time_1',0),kwargs.get('low_pressure_endurance_speed_1',0))
        self.low_pressure_total_1  = kwargs.get('low_pressure_endurance_total_1',0)
        self.low_pressure_load_1   = kwargs.get('low_pressure_endurance_load_1',0)


class Pressure(db.Model):
    """
    储存高速/耐久类型以及轮胎类型对应的气压。
    应当考虑未来需求，能够自增数据库的列

    ref : 类型名称,如EH-15 ，PE-15
    type: in ['Highspeed','Endurance']
    """
    __tablename__  = 'test_pressure'
    id                = db.Column(db.Integer,primary_key=True,nullable=False)
    ref               = db.Column(db.String(10),unique=True,nullable=False)
    type              = db.Column(db.String(10))
    tire_type_STD     = db.Column(db.Integer)
    tire_type_XL      = db.Column(db.Integer)
    tire_type_T       = db.Column(db.Integer)
    tire_type_LTR_C   = db.Column(db.Integer)
    tire_type_LTR_D   = db.Column(db.Integer)
    tire_type_LTR_E   = db.Column(db.Integer)
    tire_type_LTR_F   = db.Column(db.Integer)
    tire_type_LTR_G   = db.Column(db.Integer)
    tire_type_LTR_H   = db.Column(db.Integer)
    tire_type_LTR_J   = db.Column(db.Integer)
    tire_type_LTR_L   = db.Column(db.Integer)
    tire_type_LTR_N   = db.Column(db.Integer)


class SpecInfo(db.Model):
    '''记录SPEC基本静态信息的表'''
    __tablename__ = 'SPEC_INFO'
    id = db.Column(db.Integer,primary_key=True)


class ReportDetail(db.Model):
    """
    存储测试记录的表
    =============
    每次开发组用户提交了测试需求之后，本表自动生成一份记录,记录其uuid和测试数据已经测试名目，
    其中test_data，存储pickle之后的json(dict)文件，uuid作为唯一标识符
    但pickle化的数据并不安全

    由于无法指定数据唯一的列！容易出现多条记录！
    不能使用db.session.add(RepportDetail(1...2...3..))的提交方式
    """
    __tablename__ = 'reportDetail'

    id           = db.Column(db.Integer,primary_key=True,nullable=False)
    req_num      = db.Column(db.String(20),nullable=False)
    uuid         = db.Column(db.String(20),nullable=False)
    test_content = db.Column(db.String(10),nullable=False)
    test_data    = db.Column(db.BLOB)               # 后续考虑采用json，研究下sqlite json插件
    test_date    = db.Column(db.DATE,nullable=False)
    update_date  = db.Column(db.DATE,nullable=False)

    def __init__(self,req_num=None,uuid=None,test_content=None,test_data=None,update_date=None):
        self.req_num      = req_num
        self.uuid         = uuid
        self.test_content = test_content
        self.test_data    = test_data
        self.test_date    = datetime.date.today()
        self.update_date  = update_date

    def add_data(self,form):
        """
        在提交之前对数据进行必要的检查，以防止重复的记录产生
        :param form:form --> request.form
        :return:数据库记录
        """
        # 判断数据库记录条数
        exist = db.session.query(ReportDetail).\
            filter(ReportDetail.uuid == self.uuid,
                   ReportDetail.test_content == self.test_content).\
            count()

        # 读取数据库记录
        pickled_data = db.session.query(ReportDetail.test_data). \
            filter(ReportDetail.uuid == self.uuid,
                   ReportDetail.test_content == self.test_content). \
            first()

        if pickled_data:
            data = loads(pickled_data.test_data)
        else:
            data = {}
        data.update({str(x):y for x,y in form.items()})

        # 更新更新数据
        if exist == 1:
            db.session.rollback()      # 注意如果add失败，session需要回滚才能恢复初始状态
            db.session.query(ReportDetail).\
                filter(ReportDetail.test_content == self.test_content,
                       ReportDetail.uuid == self.uuid).\
                update({ReportDetail.test_data: dumps(data),
                        ReportDetail.update_date:datetime.date.today()})
            db.session.commit()
            db.session.close()
        # 重复记录报错
        elif exist > 1:
            raise Exception("Database has duplicate records of %s" % ReportDetail.uuid)
        # 插入数据
        else:
            db.session.add(ReportDetail(
                req_num     = self.req_num,
                uuid        = self.uuid,
                test_content= self.test_content,
                test_data   = dumps(data),
                update_date = self.update_date
            ))
            db.session.commit()
            db.session.close()