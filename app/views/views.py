# -*- coding:utf-8 -*-
import os
from app import app, db
from app.models.dbModels import usrPwd, requestForms, testContent, Highspeed, ReportDetail, Endurance
from app.ext.test_info import testInfo
from app.ext.request_detail import requestDetail
from app.ext.test_staic import total_static_test_content, static_test_request_detail
from app.ext.test_highspeed import highspeed_test_quantity, data_to_table, formatted_dict
from app.ext.test_endurance import data_to_tb, endurance_test_quantity
from urlparse import urlparse, urljoin
from flask import request, session, abort, render_template, \
    redirect, flash, url_for, send_from_directory, jsonify
from uuid import uuid1
from cPickle import dumps, loads
import datetime


def csrf_protect():
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_crsf_token'):
            abort(403)


def generate_csrf_token():
    if '_crsf_token' not in session:
        session['_crsf_token'] = os.urandom(15).encode('hex')
    return session['_crsf_token']

app.jinja_env.globals['crsf_token'] = generate_csrf_token


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    def get_redirect_target():
        for target in request.values.get('next'), request.referrer:
            if not target:
                continue
            if target:
                return target

    # 使用nginx后，request.host_url将是服务器的地址
    # 然而app是在localhost运行的，这里无法判断target
    # 如何解决？
    def is_safe_url(target):
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and \
               ref_url.netloc == test_url.netloc

    next = get_redirect_target()
    if request.method == 'POST':
        usr = usrPwd.query.filter_by(user=request.form.get('usr')).first()
        if usr is not None and usr.verify_pwd(request.form.get('pwd')):
            session['is_active'] = True
            session['usr'] = request.form.get('usr')
            return redirect(next)
        else:
            flash('Wrong User Name or Password')
    return render_template('login.html', next=next)


@app.route('/developer', methods=['GET', 'POST'])
def developer():
    if not session.get('is_active'):
        return redirect(url_for('login'), code=401)
    res = requestDetail(session).summary()
    if request.method == 'POST':
        session['uuid_id'] = str(uuid1())
        requestForms(request.form, session).add_data()
        testContent().add_data(request.form, session)
        #
        return redirect(url_for('developer'))
    return render_template('developer.html', res=res)


@app.route('/tester',methods=['GET','POST'])
def tester():
    data = testInfo().test_info()
    if request.method == "POST":
        for v in request.form.keys():
            if v.startswith('sub'):
                _ , uuid , test_content = tuple(v.split('#'))
        db.session.query(testContent).\
            filter(testContent.uuid==uuid,testContent.test_content==test_content).\
            update({'if_test':True})
        db.session.commit()
        return redirect(url_for('tester'))
    return render_template('tester.html', data=data)


# 高速/耐久数据库维护
@app.route('/maintain', methods=['GET', 'POST'])
def maintain():
    # 注意高速那就数据的区别
    if request.method == 'POST':
        if request.form.get('sub1'):
            db.session.add(Highspeed(formatted_dict(request.form)))
            db.session.commit()
        if request.form.get('sub2'):
            # 考虑到数据修改的可能性，db.session.add 应改为 db.session.merge
            pass
        if request.form.get('sub3'):
            db.session.add(Endurance(request.form))
            db.session.commit()
        if request.form.get('sub4'):
            pass
        return redirect(url_for('maintain'))
    return render_template('maintain.html')


# 高速实验测试地址
@app.route('/report/highspeed/<uuid>/', methods=['GET', 'POST'])
def test_highspeed(uuid):
    detail           = static_test_request_detail(uuid)
    quantity,req_num = highspeed_test_quantity(uuid)

    pickled_data = db.session.query(ReportDetail.test_data). \
        filter(ReportDetail.uuid == uuid,
               ReportDetail.test_content == 'highspeed'). \
        first()

    if pickled_data:
        data = loads(pickled_data.test_data)
    else:
        data = {}
    try:
        database = {x:data_to_table(x) for x in quantity.keys()}
    except Exception:
        database = {}

    if request.method == 'POST':
        # 更新pickle化的数据
        ReportDetail(req_num=req_num,
                     uuid=uuid,
                     test_content='highspeed',
                     test_data=None,
                     update_date=datetime.date.today())\
            .add_data(form=request.form)
        return redirect(url_for('test_highspeed',uuid=uuid))
    return render_template('test_highspeed.html',
                           detail=detail,
                           data=data,
                           database=database,
                           quantity=quantity)


# 耐久测试地址
@app.route('/report/endurance/<uuid>/',methods=['GET','POST'])
def test_endurance(uuid):
    quantity,req_num = endurance_test_quantity(uuid)
    detail           = static_test_request_detail(uuid)
    pickled_data     = db.session.query(ReportDetail.test_data). \
        filter(ReportDetail.uuid == uuid,
               ReportDetail.test_content == 'endurance'). \
        first()

    if pickled_data:
        data = loads(pickled_data.test_data)
    else:
        data = {}
    try:
        database = {x : data_to_tb(x) for x in quantity.keys()}
    except Exception:
        database = {}

    if request.method == 'POST':
        # 更新pickle化的数据
        ReportDetail(req_num=req_num,
                     uuid=uuid,
                     test_content='endurance',
                     test_data=None,
                     update_date=datetime.date.today())\
            .add_data(form=request.form)
        return redirect(url_for('test_endurance',uuid=uuid))
    return render_template('test_endurance.html',
                           detail=detail,
                           data=data,
                           quantity=quantity,
                           database=database)


# 静态实验测试地址
@app.route('/report/static/<uuid>/', methods=['GET', 'POST'])
def test_static(uuid):
    total,req_num = total_static_test_content(uuid)
    detail        = static_test_request_detail(uuid)
    pickled_data  = db.session.query(ReportDetail.test_data). \
        filter(ReportDetail.uuid == uuid,
               ReportDetail.test_content == 'static'). \
        first()

    if pickled_data:
        data = loads(pickled_data.test_data)
    else:
        data = {}

    if request.method == 'POST':
        ReportDetail(req_num=req_num,
                     uuid=uuid,
                     test_content='static',
                     test_data=None,
                     update_date=datetime.date.today())\
            .add_data(form=request.form)
        return redirect(url_for('test_static',uuid=uuid))
    return render_template('test_static.html', total=total, detail=detail, data=data)


# 文件下载
@app.route('/download/files/<path:filename>')
def download_file(filename):
    return send_from_directory(directory=app.config['TEST_TEMPLATE_FILES'],
                               filename=filename,
                               as_attachment=True)


# APIs
@app.route('/api/v1.0/highspeed/')
def get_highspeed_lst():
    df = db.session.query(Highspeed.ref, Highspeed.speed_level).all()
    return jsonify(df)


@app.route('/api/v1.0/endurance/')
def get_endurance_lst():
    df = db.session.query(Endurance.ref,Endurance.ref).all()
    return jsonify(df),200


@app.route('/api/v1.0/highspeed/database/')
def get_highspeed_db():
    ref = request.args.get('term', '')
    # 整理数据，使其可以json化
    try:
        x = data_to_table(ref)
        return jsonify({ref: x})
    except Exception:
        return abort(500)


@app.route('/api/v1.0/endurance/database/')
def get_endurance_db():
    ref = request.args.get('term', '')
    # 整理数据，使其可以json化
    try:
        x = data_to_tb(ref)
        return jsonify({ref: x})
    except Exception:
        return abort(500)


# 周向破坏形式
@app.route('/api/v1.0/pic/condition/circum/')
def get_condition_circum_pic():
    # 配合JS插件ddslick使用，需提供指定格式的JSON数据
    b = {}
    path = app.config['TEST_TEMPLATE_FILES'] + '/circum/'
    if os.listdir(path):
        a = 0
        for k in os.listdir(path):
            a += 1
            data = {
                'text':k,
                'value': a,
                'selected':'false',
                'description': k,
                'imageSrc':'/static/files/circum/' + k
            }
            b.update({a:data})
        return jsonify(b)


# 断宽破坏形式
@app.route('/api/v1.0/pic/condition/section/')
def get_condition_section_pic():
    # 配合JS插件ddslick使用，需提供指定格式的JSON数据
    b = {}
    path = app.config['TEST_TEMPLATE_FILES'] + '/section/'
    if os.listdir(path):
        a = 0
        for k in os.listdir(path):
            a += 1
            data = {
                'text':k,
                'value': a,
                'selected':'false',
                'description': k,
                'imageSrc':'/static/files/section/' + k
            }
            b.update({a:data})
        return jsonify(b)


# 获取指定SPEC重量,外径,总宽,断宽,数据来自EXCEL
@app.route('/api/v1.0/spec_info/')
def get_spec_info():
    pass