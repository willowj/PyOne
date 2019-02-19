#-*- coding=utf-8 -*-
from self_config import config_dir,password
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class config:
    SECRET_KEY = os.path.join(config_dir,'PyOne'+password)
    CACHE_TYPE='redis'
    MONGO_URI="mongodb://localhost:27017/three"
    REDIS2_URL='redis://localhost:6379/0'

    @staticmethod
    def init_app(app):
        pass



