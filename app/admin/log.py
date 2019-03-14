#-*- coding=utf-8 -*-
from base_view import *



@admin.route('/logs',methods=["POST","GET"])
def logs():
    logname=request.args.get('logname','running')
    command='tail -30f {}/logs/PyOne.{}.log'.format(config_dir,logname)
    resp=MakeResponse(render_template('admin/logs.html',command=command))
    return resp

