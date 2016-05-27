__author__ = 'SXChen'


from flask import Flask
from config import config
from flask.ext.sqlalchemy import SQLAlchemy


def create_app(conf):
    app = Flask(__name__)
    app.config.from_object(conf)
    return app

app = create_app(config['development'])
db  = SQLAlchemy(app)

if not app.debug:
    from app.logs.log import DebugFalseLog
    handler = DebugFalseLog().get_handler()
    app.logger.addHandler(handler)


from app.views import views