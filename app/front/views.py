#-*- coding=utf-8 -*-
from flask import render_template,redirect,abort,make_response,jsonify,request,url_for,Response
from flask_sqlalchemy import Pagination
from ..utils import *
from ..extend import limiter
from . import front

################################################################################
###################################前台函数#####################################
################################################################################
@front.before_request
def before_request():
    bad_ua=['Googlebot-Image','FeedDemon ','BOT/0.1 (BOT for JCE)','CrawlDaddy ','Java','Feedly','UniversalFeedParser','ApacheBench','Swiftbot','ZmEu','Indy Library','oBot','jaunty','YandexBot','AhrefsBot','MJ12bot','WinHttp','EasouSpider','HttpClient','Microsoft URL Control','YYSpider','jaunty','Python-urllib','lightDeckReports Bot','PHP','vxiaotou-spider','spider']
    global referrer
    try:
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    except:
        ip = request.remote_addr
    try:
        ua = request.headers.get('User-Agent')
    except:
        ua="null"
    if sum([i.lower() in ua.lower() for i in bad_ua])>0:
        return redirect('http://www.baidu.com')
    # print '{}:{}:{}'.format(request.endpoint,ip,ua)
    referrer=request.referrer if request.referrer is not None else 'no-referrer'

@front.errorhandler(500)
def page_not_found(e):
    # note that we set the 500 status explicitly
    return render_template('theme/{}/500.html'.format(GetConfig('theme')),cur_user=''), 500

@front.route('/<path:path>',methods=['POST','GET'])
@front.route('/',methods=['POST','GET'])
@limiter.limit("200/minute;50/second")
def index(path='A:/'):
    path=urllib.unquote(path).replace('&action=play','')
    if path=='favicon.ico':
        return redirect('https://onedrive.live.com/favicon.ico')
    if od_users.get('A').get('client_id')=='':
        resp=make_response(redirect(url_for('admin.install',step=0,user='A')))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    try:
        path.split(':')
    except:
        path='A:/'+path
    #参数
    user,n_path=path.split(':')
    if n_path=='':
        path=':'.join([user,'/'])
    page=request.args.get('page',1,type=int)
    image_mode=GetCookie(key='image_mode',default=0)
    sortby=GetCookie(key='sortby',default='lastModtime')
    order=GetCookie(key='order',default='desc')
    action=request.args.get('action','download')
    # try:
    #     action=re.findall('action=(.*)',request.url)[0]
    # except:
    #     action='download'
    data,total = FetchData(path=path,page=page,per_page=50,sortby=sortby,order=order,dismiss=True)
    #是否有密码
    password,_,cur=has_item(path,'.password')
    md5_p=md5(path)
    has_verify_=has_verify(path)
    if request.method=="POST":
        password1=request.form.get('password')
        if password1==password:
            resp=make_response(redirect(url_for('.index',path=path)))
            resp.delete_cookie(md5_p)
            resp.set_cookie(md5_p,password)
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
            return resp
    if password!=False:
        if (not request.cookies.get(md5_p) or request.cookies.get(md5_p)!=password) and has_verify_==False:
            if total=='files' and GetConfig('encrypt_file')=="no":
                return show(data['id'],user,action)
            resp=make_response(render_template('theme/{}/password.html'.format(GetConfig('theme')),path=path,cur_user=user))
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
            return resp
    if total=='files':
        return show(data['id'],user,action)
    readme,ext_r=GetReadMe(path)
    head,ext_d=GetHead(path)
    #参数
    all_image=False if sum([file_ico(i)!='image' for i in data])>0 else True
    pagination=Pagination(query=None,page=page, per_page=50, total=total, items=None)
    if path.split(':',1)[-1]=='/':
        path=':'.join([path.split(':',1)[0],''])
    resp=make_response(render_template('theme/{}/index.html'.format(GetConfig('theme'))
                    ,pagination=pagination
                    ,items=data
                    ,path=path
                    ,image_mode=image_mode
                    ,readme=readme
                    ,ext_r=ext_r
                    ,head=head
                    ,ext_d=ext_d
                    ,sortby=sortby
                    ,order=order
                    ,cur_user=user
                    ,all_image=all_image
                    ,endpoint='.index'))
    resp.set_cookie('image_mode',str(image_mode))
    resp.set_cookie('sortby',str(sortby))
    resp.set_cookie('order',str(order))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@front.route('/file/<user>/<fileid>/<action>')
def show(fileid,user,action='download'):
    name=GetName(fileid)
    ext=name.split('.')[-1].lower()
    path=GetPath(fileid)
    url=request.url.replace(':80','').replace(':443','').encode('utf-8').split('?')[0]
    inner_url='/'+urllib.quote('/'.join(url.split('/')[3:]))
    if request.method=='POST' or action=='share':
        print(u'share page:{}'.format(path))
        if ext in ['csv','doc','docx','odp','ods','odt','pot','potm','potx','pps','ppsx','ppsxm','ppt','pptm','pptx','rtf','xls','xlsx']:
            downloadUrl,play_url=GetDownloadUrl(fileid,user)
            url = 'https://view.officeapps.live.com/op/view.aspx?src='+urllib.quote(downloadUrl)
            resp=make_response(redirect(url))
        elif ext in ['bmp','jpg','jpeg','png','gif']:
            resp=make_response(render_template('theme/{}/show/image.html'.format(GetConfig('theme')),url=url,inner_url=inner_url,path=path,cur_user=user))
        elif ext in ['mp4','webm']:
            resp=make_response(render_template('theme/{}/show/video.html'.format(GetConfig('theme')),url=url,inner_url=inner_url,path=path,cur_user=user))
        elif ext in ['avi','mpg', 'mpeg', 'rm', 'rmvb', 'mov', 'wmv', 'mkv', 'asf']:
            resp=make_response(render_template('theme/{}/show/video2.html'.format(GetConfig('theme')),url=url,inner_url=inner_url,path=path,cur_user=user))
        elif ext in ['ogg','mp3','wav']:
            resp=make_response(render_template('theme/{}/show/audio.html'.format(GetConfig('theme')),url=url,inner_url=inner_url,path=path,cur_user=user))
        elif CodeType(ext) is not None:
            content=common._remote_content(fileid,user)
            resp=make_response(render_template('theme/{}/show/code.html'.format(GetConfig('theme')),content=content,url=url,inner_url=inner_url,language=CodeType(ext),path=path,cur_user=user))
        elif name=='.password':
            resp=make_response(abort(404))
        else:
            downloadUrl,play_url=GetDownloadUrl(fileid,user)
            resp=make_response(redirect(downloadUrl))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    print('action:{}'.format(action))
    if name=='.password':
        resp=make_response(abort(404))
    if 'no-referrer' in GetConfig('allow_site').split(',') or sum([i in referrer for i in GetConfig('allow_site').split(',')])>0:
        downloadUrl,play_url=GetDownloadUrl(fileid,user)
        if ext in ['webm','avi','mpg', 'mpeg', 'rm', 'rmvb', 'mov', 'wmv', 'mkv', 'asf']:
            if action=='play':
                resp=make_response(redirect(play_url))
            else:
                resp=make_response(redirect(downloadUrl))
        else:
            resp=make_response(redirect(play_url))
    else:
        resp=make_response(abort(404))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp



@front.route('/py_find/<key_word>')
def find(key_word):
    page=request.args.get('page',1,type=int)
    ajax=request.args.get('ajax','no')
    image_mode=request.args.get('image_mode')
    sortby=request.args.get('sortby')
    order=request.args.get('order')
    action=request.args.get('action','download')
    data,total=FetchData(path=key_word,page=page,per_page=50,sortby=sortby,order=order,dismiss=True,search_mode=True)
    pagination=Pagination(query=None,page=page, per_page=50, total=total, items=None)
    if ajax=='yes':
        retdata={}
        retdata['code']=0
        retdata['msg']=""
        retdata['total']=total
        retdata['data']=[]
        for d in data:
            info={}
            if d['type']=='folder':
                info['name']='<a href="'+url_for('.index',path=d['path'])+'">'+d['name']+'</a>'
            else:
                info['name']='<a href="'+url_for('.index',path=d['path'],action='share')+'" target="_blank">'+d['name']+'</a>'
            info['type']=d['type']
            info['lastModtime']=d['lastModtime']
            info['size']=d['size']
            info['path']=d['path']
            info['id']=d['id']
            retdata['data'].append(info)
        return jsonify(retdata)
    resp=make_response(render_template('theme/{}/find.html'.format(GetConfig('theme'))
                    ,pagination=pagination
                    ,items=data
                    ,path='/'
                    ,sortby=sortby
                    ,order=order
                    ,key_word=key_word
                    ,cur_user='搜索:"{}"'.format(key_word)
                    ,endpoint='.find'))
    resp.set_cookie('image_mode',str(image_mode))
    resp.set_cookie('sortby',str(sortby))
    resp.set_cookie('order',str(order))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@front.route('/robots.txt')
def robot():
    resp="""
User-agent:  *
Disallow:  /
    """
    resp=make_response(resp)
    resp.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return resp
