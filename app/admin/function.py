#-*- coding=utf-8 -*-
from base_view import *



###
@admin.route('/login',methods=["POST","GET"])
def login():
    if request.method=='POST':
        password1=request.form.get('password')
        if password1==GetConfig('password'):
            session['login']='true'
            if not os.path.exists(os.path.join(config_dir,'.install')):
                resp=MakeResponse(redirect(url_for('admin.install',step=0,user='A')))
                return resp
            resp=MakeResponse(redirect(url_for('admin.setting')))
        else:
            resp=MakeResponse(render_template('admin/login.html'))
        return resp
    resp=MakeResponse(render_template('admin/login.html'))
    return resp



@admin.route('/logout',methods=['GET','POST'])
def logout():
    session.pop('login',None)
    return redirect('/')

@admin.route('/reload',methods=['GET','POST'])
def reload():
    cmd='supervisorctl -c {} restart pyone'.format(os.path.join(config_dir,'supervisoredis_client.conf'))
    subprocess.Popen(cmd,shell=True)
    flash('正在重启网站...如果更改了分享目录，请更新缓存')
    return redirect(url_for('admin.setting'))

@admin.route('/setPass',methods=['POST'])
def setPass():
    new_password=request.form.get('new_password')
    old_password=request.form.get('old_password')
    if old_password==GetConfig('password'):
        set('password',new_password)
        redis_client.set('password',new_password)
        data={'msg':'修改成功！'}
    else:
        data={'msg':'旧密码不正确'}
    return jsonify(data)

