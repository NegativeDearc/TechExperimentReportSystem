# -*- coding:utf-8 -*-
import os
from app import app, db
from app.models.dbModels import usrPwd, requestForms, testContent, requestDetail, Highspeed
from app.ext.allowed_upload_file import allow_file
from app.ext.formatted_dict import formatted_dict
from app.ext.login import login_required
from urlparse import urlparse, urljoin
from flask import request, session, abort, render_template, \
    redirect, flash, url_for, send_from_directory, jsonify
from uuid import uuid1

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


@app.route('/developer',methods=['GET','POST'])
def developer():
    if not session.get('is_active'):
        return redirect(url_for('login'),code=401)
    res = requestDetail(session).summary()
    if request.method == 'POST':
        print request.form
        print request.form.getlist('endurance')
        print request.form.getlist('endurance_quantity')
        session['uuid_id'] = str(uuid1())
        requestForms(request.form,session).add_data()
        testContent().add_data(request.form,session)
        #
        return redirect(url_for('developer'))
    return render_template('developer.html',res=res)


@app.route('/tester')
def tester():
    return render_template('tester.html')


@app.route('/maintain',methods=['GET','POST'])
def maintain():
    if request.method == 'POST':
        print request.form
        db.session.add(Highspeed(formatted_dict(request.form)))
        db.session.commit()
        return redirect(url_for('maintain'))
    return render_template('maintain.html')


@app.route('/download/files/<path:filename>')
def download_file(filename):
    return send_from_directory(directory=app.config['TEST_TEMPLATE_FILES'],
                               filename=filename,
                               as_attachment=True)


@app.route('/api/v1.0/highspeed/')
def test():
    df = db.session.query(Highspeed.ref,Highspeed.speed_level).all()
    return jsonify(df)