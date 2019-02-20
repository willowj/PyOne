#-*- coding=utf-8 -*-
from self_config import config_dir,password
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class config:
    SECRET_KEY = os.path.join(config_dir,'PyOne'+password)
    CACHE_TYPE='redis'

    @staticmethod
    def init_app(app):
        pass



