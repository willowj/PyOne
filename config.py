#-*- coding=utf-8 -*-
from self_config import config_dir
from function import GetConfig
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class config:
    SECRET_KEY = os.path.join(config_dir,'PyOne'+GetConfig('password'))
    CACHE_TYPE='redis'

    @staticmethod
    def init_app(app):
        pass



