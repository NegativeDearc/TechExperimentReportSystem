__author__ = 'SXChen'

from config import config

def allow_file(name):
    return '.' in name and \
           name.rsplit('.',1)[1] in \
           config['default'].ALLOWED_UPLOAD_FILE