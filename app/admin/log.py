#-*- coding=utf-8 -*-
from base_view import *



@admin.route('/logs',methods=["POST","GET"])
def logs():
    logname=request.args.get('logname','running')
    resp=MakeResponse(render_template('admin/logs.html',logname=logname))
    return resp

@admin.route('/logstream',methods=["POST","GET"])
def logstream():
    logname=request.args.get('logname','running')
    command='tail -f {}/logs/PyOne.{}.log'.format(config_dir,logname)
    def generate():
        popen=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        while True:
            yield "data:" + popen.stdout.readline() + "\n\n"
        yield "data:end\n\n"
    return Response(generate(), mimetype= 'text/event-stream')
