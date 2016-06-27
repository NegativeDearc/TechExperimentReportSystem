# -*- coding:utf-8 -*-
import os
from app import app, db
from app.models.dbModels import usrPwd, requestForms, testContent, Highspeed, ReportDetail
from app.ext.test_info import testInfo
from app.ext.request_detail import requestDetail
from app.ext.formatted_dict import formatted_dict
from app.ext.db_to_table import data_to_table
from app.ext.test_staic import total_static_test_content, static_test_request_detail
from app.ext.test_highspeed import highspeed_test_ref
from urlparse import urlparse, urljoin
from flask import request, session, abort, render_template, \
    redirect, flash, url_for, send_from_directory, jsonify
from uuid import uuid1
from cPickle import dumps, loads


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


@app.route('/tester')
def tester():
    data = testInfo().test_info()
    print data
    return render_template('tester.html', data=data)


@app.route('/maintain', methods=['GET', 'POST'])
def maintain():
    if request.method == 'POST':
        print request.form
        # 考虑到数据修改的可能性，db.session.add 应改为 db.session.merge
        db.session.add(Highspeed(formatted_dict(request.form)))
        db.session.commit()
        return redirect(url_for('maintain'))
    return render_template('maintain.html')


@app.route('/report/endurance/<uuid>/',methods=['GET','POST'])
def test_endurance(uuid):
    return '%s' % uuid


# 高速实验测试地址
@app.route('/report/highspeed/<uuid>/', methods=['GET', 'POST'])
def test_highspeed(uuid):
    detail = static_test_request_detail(uuid)
    ref = highspeed_test_ref(uuid)

    pickled_data = db.session.query(ReportDetail.test_data). \
        filter(ReportDetail.uuid == uuid,
               ReportDetail.test_content == 'highspeed'). \
        first()

    if pickled_data:
        data = loads(pickled_data.test_data)
    else:
        data = {}
    try:
        database = data_to_table(ref.get('ref'))
    except Exception:
        database = {}

    if request.method == 'POST':
        data.update({str(x):y for x,y in request.form.items()})
        try:
            db.session.add(
                ReportDetail(uuid=uuid, test_content='highspeed', test_data=dumps(data))
            )
            db.session.commit()
        except Exception:
            db.session.rollback()      # 注意如果add失败，session需要回滚才能恢复初始状态
            db.session.query(ReportDetail).\
                filter(ReportDetail.test_content == 'highspeed',
                       ReportDetail.uuid == uuid).\
                update({ReportDetail.test_data: dumps(data)})
            db.session.commit()
        finally:
            db.session.close()
            return redirect(url_for('test_highspeed',uuid=uuid))
    return render_template('test_highspeed.html',
                           detail=detail,
                           data=data,
                           ref=ref,
                           database=database)


# 静态实验测试地址
@app.route('/report/static/<uuid>/', methods=['GET', 'POST'])
def test_static(uuid):
    total = total_static_test_content(uuid)
    detail = static_test_request_detail(uuid)
    pickled_data = db.session.query(ReportDetail.test_data). \
        filter(ReportDetail.uuid == uuid,
               ReportDetail.test_content == 'static'). \
        first()

    if pickled_data:
        data = loads(pickled_data.test_data)
    else:
        data = {}

    if request.method == 'POST':
        data.update({str(x):y for x,y in request.form.items()})
        try:
            db.session.add(
                ReportDetail(uuid=uuid, test_content='static', test_data=dumps(data))
            )
            db.session.commit()
        except Exception:
            db.session.rollback()      # 注意如果add失败，session需要回滚才能恢复初始状态
            db.session.query(ReportDetail).\
                filter(ReportDetail.test_content == 'static',
                       ReportDetail.uuid == uuid).\
                update({ReportDetail.test_data: dumps(data)})
            db.session.commit()
        finally:
            db.session.close()
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


@app.route('/api/v1.0/highspeed/database/')
def get_highspeed_db():
    ref = request.args.get('term', '')
    # 整理数据，使其可以json化
    try:
        x = data_to_table(ref)
        return jsonify({ref: x})
    except Exception:
        return abort(500)