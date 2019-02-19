#-*- coding=utf-8 -*-
from flask_caching import Cache
from flask_pymongo import PyMongo
from flask_redis import Redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


cache = Cache()
mongo = PyMongo()
redis_client=Redis()
limiter = Limiter(key_func=get_remote_address)
