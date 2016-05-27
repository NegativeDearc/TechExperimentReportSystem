# -*- coding:utf-8 -*-
import os
from app import app
from app.models.dbModels import usrPwd
from urlparse import urlparse, urljoin
from flask import request, session, abort, render_template, redirect, flash



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
        # 如果查询到用户则返回app.Models.dbModels.usrPwd类,可调用该类的方法
        # 注意这边使用user = request.form.get('usr')还是使用user == request.form.get('usr'),为什么?
        usr = usrPwd.query.filter_by(user=request.form.get('usr')).first()
        if usr is not None and usr.verify_pwd(request.form.get('pwd')):
            session['is_active'] = True
            return redirect(next)
        else:
            flash('Wrong User Name or Password')
    return render_template('login.html', next=next)


@app.route('/developer')
def developer():
    return render_template('developer.html')


@app.route('/tester')
def tester():
    return 'OK'
