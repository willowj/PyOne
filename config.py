#-*- coding=utf-8 -*-
from self_config import config_dir,password
import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


class config:
    SECRET_KEY = os.path.join(config_dir,'PyOne'+password)
    CACHE_TYPE='redis'
    SEND_FILE_MAX_AGE_DEFAULT=timedelta(seconds=1)
    version='4.190305'

    @staticmethod
    def init_app(app):
        pass



