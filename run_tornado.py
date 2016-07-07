__author__ = 'SXChen'

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from app import app

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(5555,address='0.0.0.0')
#http_server.listen(5555)
IOLoop.instance().start()

