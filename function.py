#-*- coding=utf-8 -*-
from app.utils import *


if __name__=='__main__':
    func=sys.argv[1]
    if len(sys.argv)>2:
        args=sys.argv[2:]
        eval(func+str(tuple(args)))
    else:
        eval(func+'()')
