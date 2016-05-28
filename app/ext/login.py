from functools import wraps
from flask import g, request, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.get('usr',None) is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function