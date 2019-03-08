#-*- coding=utf-8 -*-
from flask import render_template,redirect,abort,make_response,jsonify,request,url_for,Response,session,flash
from flask_sqlalchemy import Pagination
from self_config import *
from ..utils import *
from ..extend import *
from .. import *
from . import admin
import os
import io
import re
import base64
import subprocess
import random
import string
import math
import urllib
from shelljob import proc

############功能函数
def set(key,value,user='A'):
    InfoLogger().print_r('set {}:{}'.format(key,value))
    config_path=os.path.join(config_dir,'self_config.py')
    with open(config_path,'r') as f:
        old_text=f.read()
    with open(config_path,'w') as f:
        if key in ['client_secret','client_id','share_path','other_name']:
            old_kv=re.findall('"{}":.*{{[\w\W]*}}'.format(user),old_text)[0]
            new_kv=re.sub('"{}":.*.*?,'.format(key),'"{}":"{}",'.format(key,value),old_kv,1)
            new_text=old_text.replace(old_kv,new_kv,1)
        elif key=='allow_site':
            value=value.split(',')
            new_text=re.sub('{}=.*'.format(key),'{}={}'.format(key,value),old_text)
        elif key in ['tj_code','cssCode','headCode','footCode']:
            new_text=re.sub('{}="""[\w\W]*?"""'.format(key),'{}="""{}"""'.format(key,value),old_text)
        else:
            new_text=re.sub('{}=.*'.format(key),'{}="{}"'.format(key,value),old_text)
        f.write(new_text)


############视图函数
@admin.before_request
def before_request():
    if request.endpoint.startswith('admin') and request.endpoint!='admin.login' and session.get('login') is None: #and request.endpoint!='admin.install'
        return redirect(url_for('admin.login'))


########web console
@admin.route('/web_console')
def web_console():
    g = proc.Group()
    action=request.args.get('action')
    allow_action=['UpdateFile','UploadDir','Upload']
    if action not in allow_action:
        return make_response('error')
    if action in ['UploadDir','Upload']:
        local=urllib.unquote(request.args.get('local'))
        remote=urllib.unquote(request.args.get('remote'))
        user=urllib.unquote(request.args.get('user'))
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action,local,remote,user]
    elif action=='UpdateFile':
        type_=request.args.get('type')
        cmd=["python","-u",os.path.join(config_dir,'function.py'),'UpdateFile',type_]
    else:
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action]
    p = g.run(cmd)
    def read_process():
        while g.is_pending():
            lines = g.readlines()
            for proc, line in lines:
                yield "data:" + line + "\n\n"
        yield "data:end\n\n"
    resp=Response(read_process(), mimetype= 'text/event-stream')
    return resp

########admin
@admin.route('/',methods=['GET','POST'])
@admin.route('/setting',methods=['GET','POST'])
def setting():
    if request.method=='POST':
        if request.files.keys()!=[]:
            favicon=request.files['favicon']
            favicon.save('./app/static/img/favicon.ico')
        title=request.form.get('title','PyOne')
        theme=request.form.get('theme','material')
        title_pre=request.form.get('title_pre','index of ')
        downloadUrl_timeout=request.form.get('downloadUrl_timeout',5*60)
        allow_site=request.form.get('allow_site','no-referrer')
        #Aria2
        ARIA2_HOST=request.form.get('ARIA2_HOST','localhost').replace('https://','').replace('http://','')
        ARIA2_PORT=request.form.get('ARIA2_PORT',6800)
        ARIA2_SECRET=request.form.get('ARIA2_SECRET','')
        ARIA2_SCHEME=request.form.get('ARIA2_SCHEME','http')

        #MongoDB
        MONGO_HOST=request.form.get('MONGO_HOST','localhost').replace('https://','').replace('http://','')
        MONGO_PORT=request.form.get('MONGO_PORT',27017)
        MONGO_DB=request.form.get('MONGO_DB','three')
        MONGO_USER=request.form.get('MONGO_USER','')
        MONGO_PASSWORD=request.form.get('MONGO_PASSWORD','')
        #Redis
        REDIS_HOST=request.form.get('REDIS_HOST','localhost').replace('https://','').replace('http://','')
        REDIS_PORT=request.form.get('REDIS_PORT',6379)
        REDIS_DB=request.form.get('REDIS_DB','0')
        REDIS_PASSWORD=request.form.get('REDIS_PASSWORD','')

        show_secret=request.form.get('show_secret','no')
        encrypt_file=request.form.get('encrypt_file','no')
        set('title',title)
        set('title_pre',title_pre)
        set('theme',theme)
        set('downloadUrl_timeout',downloadUrl_timeout)
        set('allow_site',allow_site)
        #Aria2
        set('ARIA2_HOST',ARIA2_HOST)
        set('ARIA2_PORT',ARIA2_PORT)
        set('ARIA2_SECRET',ARIA2_SECRET)
        set('ARIA2_SCHEME',ARIA2_SCHEME)
        #MongoDB
        set('MONGO_HOST',MONGO_HOST)
        set('MONGO_PORT',MONGO_PORT)
        set('MONGO_DB',MONGO_DB)
        set('MONGO_USER',MONGO_USER)
        set('MONGO_PASSWORD',MONGO_PASSWORD)
        #Redis
        set('REDIS_HOST',REDIS_HOST)
        set('REDIS_PORT',REDIS_PORT)
        set('REDIS_DB',REDIS_DB)
        set('REDIS_PASSWORD',REDIS_PASSWORD)

        set('show_secret',show_secret)
        set('encrypt_file',encrypt_file)
        # reload()
        redis_client.set('title',title)
        redis_client.set('title_pre',title_pre)
        redis_client.set('theme',theme)
        redis_client.set('downloadUrl_timeout',downloadUrl_timeout)
        redis_client.set('allow_site',','.join(allow_site.split(',')))
        #Aria2
        redis_client.set('ARIA2_HOST',ARIA2_HOST)
        redis_client.set('ARIA2_PORT',ARIA2_PORT)
        redis_client.set('ARIA2_SECRET',ARIA2_SECRET)
        redis_client.set('ARIA2_SCHEME',ARIA2_SCHEME)

        #MongoDB
        redis_client.set('MONGO_HOST',MONGO_HOST)
        redis_client.set('MONGO_PORT',MONGO_PORT)
        redis_client.set('MONGO_DB',MONGO_DB)
        redis_client.set('MONGO_USER',MONGO_USER)
        redis_client.set('MONGO_PASSWORD',MONGO_PASSWORD)

        #Redis
        redis_client.set('REDIS_HOST',REDIS_HOST)
        redis_client.set('REDIS_PORT',REDIS_PORT)
        redis_client.set('REDIS_DB',REDIS_DB)
        redis_client.set('REDIS_PASSWORD',REDIS_PASSWORD)

        redis_client.set('show_secret',show_secret)
        redis_client.set('encrypt_file',encrypt_file)
        flash('更新成功')
        resp=MakeResponse(redirect(url_for('admin.setting')))
        return resp
    resp=MakeResponse(render_template('admin/setting/setting.html'))
    return resp

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


@admin.route('/setCode',methods=['GET','POST'])
def setCode():
    if request.method=='POST':
        tj_code=request.form.get('tj_code','')
        headCode=request.form.get('headCode','')
        footCode=request.form.get('footCode','')
        cssCode=request.form.get('cssCode','')
        #redis
        set('tj_code',tj_code)
        set('headCode',headCode)
        set('footCode',footCode)
        set('cssCode',cssCode)
        # reload()
        redis_client.set('tj_code',tj_code)
        redis_client.set('headCode',headCode)
        redis_client.set('footCode',footCode)
        redis_client.set('cssCode',cssCode)
        flash('更新成功')
        resp=MakeResponse(render_template('admin/setCode/setCode.html'))
        return resp
    resp=MakeResponse(render_template('admin/setCode/setCode.html'))
    return resp


###upload
@admin.route('/upload',methods=["POST","GET"])
def upload():
    if request.method=='POST':
        user=request.form.get('user').encode('utf-8')
        local=request.form.get('local').encode('utf-8')
        remote=request.form.get('remote').encode('utf-8')
        if not os.path.exists(local):
            flash('本地目录/文件不存在')
            return redirect(url_for('admin.upload'))
        if os.path.isfile(local):
            filelists=[local]
        else:
            filelists=list_all_files(local)
        if local.endswith('/'):
            local=local[:-1]
        for file in filelists:
            print(file)
            info={}
            dir_,fname=os.path.dirname(file),os.path.basename(file)
            remote_path=remote+'/'+dir_.replace(local,'')+'/'+fname
            remote_path=remote_path.replace('//','/')
            info['user']=user
            info['localpath']=file
            info['remote']=remote_path
            info['status']=''
            info['speed']=''
            info['id']=base64.b64encode(str(int(round(time.time())))+file)
            info['add_time']=int(round(time.time()))
            mon_db.upload_queue.insert_one(info)
        cmd='python {}/function.py StartUploadQueue'.format(config_dir)
        subprocess.Popen(cmd,shell=True)
        resp=redirect(url_for('admin.upload'))
        return resp
    page=request.args.get('page',1,type=int)
    resp=MakeResponse(render_template('admin/upload.html',page=page))
    return resp

@admin.route('/upload/jsonrpc',methods=['POST'])
def UploadRPCserver():
    action=request.form.get('action')
    page=request.form.get('page',1,type=int)
    if action=='pagination':
        data={'code':1}
        total=get_upload_tasks_no()
        pagination=Pagination(query=None,page=page, per_page=50, total=total, items=None)
        data['page']=page
        data['pages']=pagination.pages
        page_lists=[]
        for p in pagination.iter_pages():
            page_lists.append(p)
        data['page_lists']=page_lists[::-1]
        data['has_prev']=pagination.has_prev
        data['has_next']=pagination.has_next
        return jsonify(data)
    elif action=='ClearHist':
        mon_db.upload_queue.delete_many({})
        ret={'msg':'清除成功！'}
        return jsonify(ret)
    elif action=='Restart':
        cmd='python {}/function.py StartUploadQueue'.format(config_dir)
        subprocess.Popen(cmd,shell=True)
        ret={'msg':'重启成功！'}
        return jsonify(ret)
    ret=get_upload_tasks(page)
    data={'code':1,'result':ret}
    return jsonify(data)



###upload end


@admin.route('/cache',methods=["POST","GET"])
def cache_control():
    if request.method=='POST':
        type=request.form.get('type')
        cmd="python -u {} UpdateFile {}".format(os.path.join(config_dir,'function.py'),type)
        subprocess.Popen(cmd,shell=True)
        msg='后台刷新数据中...请不要多次点击！否则服务器出问题别怪PyOne'
        return jsonify(dict(msg=msg))
    resp=MakeResponse(render_template('admin/cache.html'))
    return resp


@admin.route('/manage',methods=["POST","GET"])
def manage():
    if request.method=='POST':
        pass
    path=urllib.unquote(request.args.get('path','A:/'))
    user,n_path=path.split(':')
    if n_path=='':
        path=':'.join([user,'/'])
    page=request.args.get('page',1,type=int)
    image_mode=request.args.get('image_mode')
    sortby=request.args.get('sortby')
    order=request.args.get('order')
    if sortby:
        sortby=request.args.get('sortby')
    else:
        sortby=request.cookies.get('admin_sortby') if request.cookies.get('admin_sortby') is not None else 'lastModtime'
        sortby=sortby
    if order:
        order=request.args.get('order')
    else:
        order=request.cookies.get('admin_order') if request.cookies.get('admin_order') is not None else 'desc'
        order=order
    resp,total = FetchData(path=path,page=page,per_page=50,sortby=sortby,order=order)
    pagination=Pagination(query=None,page=page, per_page=50, total=total, items=None)
    if path.split(':',1)[-1]=='/':
        path=':'.join([path.split(':',1)[0],''])
    resp=MakeResponse(render_template('admin/manage/manage.html',pagination=pagination,items=resp,path=path,sortby=sortby,order=order,cur_user=user,endpoint='admin.manage'))
    resp.set_cookie('admin_sortby',str(sortby))
    resp.set_cookie('admin_order',str(order))
    return resp


@admin.route('/edit',methods=["GET","POST"])
def edit():
    if request.method=='POST':
        fileid=request.form.get('fileid')
        user=request.form.get('user')
        content=request.form.get('content').encode('utf-8')
        info=EditFile(fileid=fileid,content=content,user=user)
        return jsonify(info)
    fileid=request.args.get('fileid')
    user=request.args.get('user')
    name=GetName(fileid)
    ext=name.split('.')[-1]
    language=CodeType(ext)
    if language is None:
        language='Text'
    content=common._remote_content(fileid,user)
    resp=MakeResponse(render_template('admin/setFile/edit.html',content=content,fileid=fileid,name=name,language=language,cur_user=user))
    return resp

###本地上传文件只onedrive，通过服务器中转
@admin.route('/upload_local',methods=['POST','GET'])
def upload_local():
    user,remote_folder=request.args.get('path').split(':')
    resp=MakeResponse(render_template('admin/manage/upload_local.html',remote_folder=remote_folder,cur_user=user))
    return resp

@admin.route('/checkChunk', methods=['POST'])
def checkChunk():
    fileName=request.form.get('name').encode('utf-8')
    chunk=request.form.get('chunk',0,type=int)
    filename = u'./upload/{}-{}'.format(fileName, chunk)
    if os.path.exists(filename):
        exists=True
    else:
        exists=False
    return jsonify({'ifExist':exists})


@admin.route('/mergeChunks', methods=['POST'])
def mergeChunks():
    fileName=request.form.get('fileName').encode('utf-8')
    md5=request.form.get('fileMd5')
    chunk = 0  # 分片序号
    with open(u'./upload/{}'.format(fileName), 'wb') as target_file:  # 创建新文件
        while True:
            try:
                filename = u'./upload/{}-{}'.format(fileName, chunk)
                source_file = open(filename, 'rb')  # 按序打开每个分片
                target_file.write(source_file.read())  # 读取分片内容写入新文件
                source_file.close()
            except IOError as msg:
                break
            chunk += 1
            os.remove(filename)  # 删除该分片，节约空间
    return jsonify({'upload':True})


@admin.route('/recv_upload', methods=['POST'])
def recv_upload():  # 接收前端上传的一个分片
    md5=request.form.get('fileMd5')
    name=request.form.get('name').encode('utf-8')
    chunk_id=request.form.get('chunk',0,type=int)
    filename = '{}-{}'.format(name,chunk_id)
    upload_file = request.files['file']
    upload_file.save(u'./upload/{}'.format(filename))
    return jsonify({'upload_part':True})


@admin.route('/to_one',methods=['GET'])
def server_to_one():
    user=request.args.get('user')
    filename=request.args.get('filename').encode('utf-8')
    remote_folder=request.args.get('remote_folder').encode('utf-8')
    if remote_folder!='/':
        remote_folder=remote_folder+'/'
    local_dir=os.path.join(config_dir,'upload')
    filepath=urllib.unquote(os.path.join(local_dir,filename))
    _upload_session=Upload_for_server(filepath,remote_folder,user)
    def read_status():
        while 1:
            try:
                msg=_upload_session.next()['status']
                yield "data:" + msg + "\n\n"
            except Exception as e:
                exstr = traceback.format_exc()
                ErrorLogger().print_r(exstr)
                msg='end'
                yield "data:" + msg + "\n\n"
                os.remove(filepath)
                break
    return Response(read_status(), mimetype= 'text/event-stream')



###本地上传文件只onedrive，通过服务器中转
@admin.route('/setFile',methods=["GET","POST"])
@admin.route('/setFile/<filename>',methods=["GET","POST"])
def setFile(filename=None):
    if request.method=='POST':
        path=request.form.get('path')
        if path.split(':')[-1]=='':
            path=path.split(':')[0]+':/'
        user,n_path=path.split(':')
        filename=request.form.get('filename')
        content=request.form.get('content').encode('utf-8')
        info=CreateFile(filename=filename,path=n_path,content=content,user=user)
        return jsonify(info)
    path=urllib.unquote(request.args.get('path'))
    if path.split(':')[-1]=='':
        path=path.split(':')[0]+':/'
    user,n_path=path.split(':')
    _,fid,i=has_item(path,filename)
    if fid!=False and i!=False:
        resp=MakeResponse(redirect(url_for('admin.edit',fileid=fid,user=user)))
        return resp
    resp=MakeResponse(render_template('admin/setFile/setpass.html',path=path,filename=filename,cur_user=user))
    return resp


@admin.route('/delete',methods=["POST"])
def delete():
    ids=request.form.get('id')
    user=request.form.get('user')
    if ids is None:
        return jsonify({'msg':u'请选择要删除的文件','status':0})
    ids=ids.split('##')
    infos={}
    infos['status']=1
    infos['delete']=0
    infos['fail']=0
    for id in ids:
        InfoLogger().print_r('delete {}'.format(id))
        file=mon_db.items.find_one({'id':id})
        name=file['name']
        path=file['path'].replace(name,'')
        if len(path.split('/'))>2 and path.split('/')[-1]=='':
            path=path[:-1]
        key='has_item$#$#$#$#{}$#$#$#$#{}'.format(path,name)
        InfoLogger().print_r('delete key:{}'.format(key))
        redis_client.delete(key)
        kc='{}:content'.format(id)
        redis_client.delete(kc)
        status=DeleteRemoteFile(id,user)
        if status:
            infos['delete']+=1
        else:
            infos['fail']+=1
    return jsonify(infos)


@admin.route('/add_folder',methods=['POST'])
def AddFolder():
    folder_name=request.form.get('folder_name')
    path=request.args.get('path')
    user,grand_path=path.split(':')
    if grand_path=='' or grand_path is None:
        grand_path='/'
    else:
        if grand_path.startswith('/'):
            grand_path=grand_path[1:]
    result=CreateFolder(folder_name,grand_path,user)
    return jsonify({'result':result})

@admin.route('/move_file',methods=['POST'])
def MoveFileToNewFolder():
    fileid=request.form.get('fileid')
    user=request.form.get('user')
    new_folder_path=request.form.get('new_folder_path')
    if new_folder_path=='' or new_folder_path is None:
        new_folder_path='/'
    else:
        if new_folder_path.startswith('/'):
            new_folder_path=new_folder_path[1:]
    result=MoveFile(fileid,new_folder_path,user)
    return jsonify({'result':result})

@admin.route('/rename',methods=['POST'])
def Rename():
    fileid=request.form.get('fileid')
    user=request.form.get('user')
    new_name=request.form.get('new_name')
    if new_name=='' or new_name is None:
        return jsonify({'result':result})
    else:
        if new_name.startswith('/'):
            new_name=new_name[1:]
        if new_name.endswith('/'):
            new_name=new_name[:-1]
    result=ReName(fileid,new_name,user)
    return jsonify({'result':result})


######离线下载---调用aria2
@admin.route('/off_download',methods=['POST','GET'])
def off_download():
    if request.method=='POST':
        p,status=get_aria2()
        if not status:
            return jsonify({'status':False,'msg':p})
        urls=request.form.get('urls').split('\n')
        grand_path=request.form.get('grand_path')
        user=request.form.get('user')
        for url in urls:
            if url.strip()!='':
                # cmd=u'python {} download_and_upload "{}" "{}" {}'.format(os.path.join(config_dir,'function.py'),url,grand_path,user)
                cmd=u'nohup python {} download_and_upload "{}" "{}" {} &'.format(os.path.join(config_dir,'function.py'),url,grand_path,user)
                subprocess.Popen(cmd,shell=True)
        return jsonify({'status':True,'msg':'ok'})
    path=request.args.get('path')
    user,grand_path=path.split(':')
    msg=None
    p,status=get_aria2()
    if not status:
        msg=p
    resp=MakeResponse(render_template('admin/offdownload.html',grand_path=grand_path,cur_user=user,msg=msg))
    return resp


@admin.route('/jsonrpc',methods=['POST'])
def RPCserver():
    action=request.form.get('action')
    allow_action=['tellActive','tellSuccess','tellFail','tellUnselected','pause','pauseAll','unpause','unpauseAll','remove','removeAll','restart','unselected','selected']
    action_dict=dict(tellActive=1,tellSuccess=0,tellFail=-1,tellUnselected=2)
    if action not in allow_action:
        return jsonify({'code':0,'msg':'not allow action'})
    if action in ['tellActive','tellSuccess','tellFail','tellUnselected']:
        status=action_dict[action]
        ret={'code':1,'msg':'get data success','result':get_tasks(status)}
    elif action in ['pause','pauseAll','unpause','unpauseAll','remove','removeAll','restart','unselected','selected']:
        ret=None
        gids=request.form.get('gid').split('####')
        ret1=Aria2Method(action=action,gids=gids)
        ret2=DBMethod(action=action,gids=gids)
        if ret1 is not None:
            ret=ret1
        else:
            ret=ret2
    return jsonify(ret)

@admin.route('/clearHist',methods=['POST'])
def clearHist():
    mon_db.down_db.delete_many({})
    ret={'msg':'清除成功！'}
    return jsonify(ret)



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

###########################################安装
@admin.route('/install',methods=['POST','GET'])
def install():
    if request.method=='POST':
        step=request.form.get('step',type=int)
        user=request.form.get('user')
        if step==1:
            client_id=request.form.get('client_id')
            client_secret=request.form.get('client_secret')
            set('client_id',client_id,user)
            set('client_secret',client_secret,user)
            login_url=LoginUrl.format(client_id=client_id,redirect_uri=redirect_uri)
            return render_template('admin/install/install_1.html',client_secret=client_secret,client_id=client_id,login_url=login_url,cur_user=user)
        else:
            client_secret=request.form.get('client_secret')
            client_id=request.form.get('client_id')
            code=request.form.get('code')
            #授权
            headers={'Content-Type':'application/x-www-form-urlencoded'}
            headers.update(default_headers)
            data=AuthData.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri),client_secret=client_secret,code=code)
            url=OAuthUrl
            r=requests.post(url,data=data,headers=headers)
            Atoken=json.loads(r.text)
            if Atoken.get('access_token'):
                with open(os.path.join(config_dir,'data/{}_Atoken.json'.format(user)),'w') as f:
                    json.dump(Atoken,f,ensure_ascii=False)
                refresh_token=Atoken.get('refresh_token')
                token=ReFreshToken(refresh_token,user)
                with open(os.path.join(config_dir,'data/{}_token.json'.format(user)),'w') as f:
                    json.dump(token,f,ensure_ascii=False)
                with open(os.path.join(config_dir,'.install'),'w') as f:
                    f.write('4.0')
                config_path=os.path.join(config_dir,'self_config.py')
                with open(config_path,'r') as f:
                    text=f.read()
                redis_client.set('users',re.findall('od_users=([\w\W]*})',text)[0])
                return make_response('<h1>授权成功!<br>请先在<B><a href="/admin/cache" target="_blank">后台-更新列表</a></B>，全量更新数据<br>然后<a href="/?t={}">点击进入首页</a></h1><br>'.format(time.time()))
            else:
                return jsonify(Atoken)
    step=request.args.get('step',type=int)
    user=request.args.get('user','A')
    resp=MakeResponse(render_template('admin/install/install_0.html',step=step,cur_user=user,redirectUrl=redirect_uri))
    return resp

###########################################卸载
@admin.route('/uninstall',methods=['POST'])
def uninstall():
    type_=request.form.get('type')
    if type_=='mongodb':
        mon_db.items.remove()
        mon_db.down_db.remove()
        msg='删除mongodb数据成功'
    elif type_=='redis':
        redis_client.flushdb()
        msg='删除redis数据成功'
    elif type_=='directory':
        subprocess.Popen('rm -rf {}/data/*.json'.format(config_dir),shell=True)
        subprocess.Popen('rm -rf {}/.install'.format(config_dir),shell=True)
        msg='删除网站数据成功'
    else:
        msg='数据已清除！如果需要删除目录请运行:rm -rf {}'.format(config_dir)
    ret={'msg':msg}
    return jsonify(ret)



###########################################网盘管理
@admin.route('/',methods=['GET','POST'])
@admin.route('/panage',methods=['GET','POST'])
def panage():
    if request.method=='POST':
        ####网盘信息处理
        for k,v in request.form.to_dict().items():
            if 'share_path' in k or 'other_name' in k:
                user=re.findall('\[(.*?)\]',k)[0]
                key=re.findall('(.*)\[',k)[0]
                InfoLogger().print_r('setting {}\'s {}\'s value {}'.format(user,key,v))
                set(key,v,user)
        config_path=os.path.join(config_dir,'self_config.py')
        with open(config_path,'r') as f:
            text=f.read()
        redis_client.set('users',re.findall('od_users=([\w\W]*})',text)[0])
        flash('更新成功')
        resp=MakeResponse(render_template('admin/pan_manage/pan_manage.html'))
        return resp
    resp=MakeResponse(render_template('admin/pan_manage/pan_manage.html'))
    return resp


@admin.route('/add_pan',methods=["POST","GET"])
def add_pan():
    if request.method=='POST':
        title=request.form.get('title','PyOne')
        pan=request.form.get('pan',''.join(random.sample(string.ascii_letters,2)))
        if pan in od_users.keys():
            flash('盘位重复！')
            return redirect(url_for('admin.add_pan'))
        order=request.form.get('order',0,type=int)
        info={"client_id":"",
                "client_secret":"",
                "share_path":"/",
                "other_name":title,
                "order":order
            }
        od_users[pan]=info
        config_path=os.path.join(config_dir,'self_config.py')
        with open(config_path,'r') as f:
            old_text=f.read()
        with open(config_path,'w') as f:
            old_od=re.findall('od_users={[\w\W]*}',old_text)[0]
            new_od='od_users='+json.dumps(od_users,indent=4,ensure_ascii=False)
            print(new_od)
            new_text=old_text.replace(old_od,new_od,1)
            f.write(new_text)
        flash('添加盘符[{}]成功'.format(pan))
        key='users'
        redis_client.delete(key)
        return redirect(url_for('admin.add_pan'))
    return render_template('admin/pan_manage/add_pan.html')


@admin.route('/rm_pan',methods=["POST","GET"])
def rm_pan():
    if request.method=='POST':
        pan=request.form.get('user')
        od_users.pop(pan)
        config_path=os.path.join(config_dir,'self_config.py')
        with open(config_path,'r') as f:
            old_text=f.read()
        with open(config_path,'w') as f:
            old_od=re.findall('od_users={[\w\W]*}',old_text)[0]
            new_od='od_users='+json.dumps(od_users,indent=4,ensure_ascii=False)
            new_text=old_text.replace(old_od,new_od,1)
            f.write(new_text)
        key='users'
        redis_client.delete(key)
        mon_db.items.delete_many({'user':pan})
        data=dict(msg='删除盘符[{}]成功'.format(pan),status=1)
        return jsonify(data)
    return render_template('admin/pan_manage/rm_pan.html')



