#-*- coding=utf-8 -*-
import json
import requests
import collections
import sys
if sys.version_info[0]==3:
    import urllib.parse as urllib
else:
    import urllib
    reload(sys)
    sys.setdefaultencoding('utf-8')
import os
import re
import time
import shutil
import base64
import humanize
import StringIO
import subprocess
import signal
from dateutil.parser import parse
from Queue import Queue
from threading import Thread,Event
from pymongo import MongoClient,ASCENDING,DESCENDING
from self_config import *
from aria2 import PyAria2
from ..extend import *

#######授权链接
LoginUrl=BaseAuthUrl+'/common/oauth2/v2.0/authorize?response_type=code\
&client_id={client_id}&redirect_uri={redirect_uri}&scope=offline_access%20files.readwrite.all'
OAuthUrl=BaseAuthUrl+'/common/oauth2/v2.0/token'
AuthData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}&grant_type=authorization_code'
ReFreshData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token'

default_headers={'User-Agent':'ISV|PyOne|PyOne/4.0'}

#转字符串
def convert2unicode(string):
    return string.encode('utf-8')

#获取
def get_value(key,user='A'):
    allow_key=['client_secret','client_id']
    #print('get user {}\'s {}'.format(user,key))
    if key not in allow_key:
        return u'禁止获取'
    config_path=os.path.join(config_dir,'self_config.py')
    with open(config_path,'r') as f:
        text=f.read()
    kv=re.findall('"{}":.*{{[\w\W]*}}'.format(user),text)[0]
    value=re.findall('"{}":.*"(.*?)"'.format(key),kv)[0]
    return value

def GetName(id):
    key='name:{}'.format(id)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        item=mongo.db.items.find_one({'id':id})
        redis_client.set(key,item['name'])
        return item['name']

def GetPath(id):
    key='path:{}'.format(id)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        item=mongo.db.items.find_one({'id':id})
        redis_client.set(key,item['path'])
        return item['path']

def GetConfig(key):
    if key=='allow_site':
        value=redis_client.get('allow_site') if redis_client.exists('allow_site') else ','.join(allow_site)
    else:
        value=redis_client.get(key) if redis_client.exists(key) else eval(key)
    #这里是为了储存
    if key=='od_users' and isinstance(value,dict):
        value=json.dumps(value)
    if not redis_client.exists(key):
        redis_client.set(key,value)
    #这里是为了转为字典
    if key=='od_users':
        value=json.loads(value)
    return value

def GetThemeList():
    tlist=[]
    theme_dir=os.path.join(config_dir,'app/templates/theme')
    lists=os.listdir(theme_dir)
    for l in lists:
        p=os.path.join(theme_dir,l)
        if os.path.isdir(p):
            tlist.append(l)
    return tlist


def open_json(filepath):
    token=False
    with open(filepath,'r') as f:
        try:
            token=json.load(f)
        except:
            for i in range(1,10):
                try:
                    token=json.loads(f.read()[:-i])
                except:
                    token=False
                if token!=False:
                    return token
    return token

def ReFreshToken(refresh_token,user='A'):
    client_id=get_value('client_id',user)
    client_secret=get_value('client_secret',user)
    headers={'Content-Type':'application/x-www-form-urlencoded'}
    headers.update(default_headers)
    data=ReFreshData.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri),client_secret=client_secret,refresh_token=refresh_token)
    url=OAuthUrl
    r=requests.post(url,data=data,headers=headers)
    return json.loads(r.text)


def GetToken(Token_file='token.json',user='A'):
    Token_file='{}_{}'.format(user,Token_file)
    token_path=os.path.join(data_dir,Token_file)
    if os.path.exists(token_path):
        token=open_json(token_path)
        try:
            if time.time()>float(token.get('expires_on')):
                print 'token timeout'
                refresh_token=token.get('refresh_token')
                token=ReFreshToken(refresh_token,user)
                if token.get('access_token'):
                    with open(token_path,'w') as f:
                        json.dump(token,f,ensure_ascii=False)
                else:
                    print token
        except:
            with open(os.path.join(data_dir,'{}_Atoken.json'.format(user)),'r') as f:
                Atoken=json.load(f)
            refresh_token=Atoken.get('refresh_token')
            token=ReFreshToken(refresh_token,user)
            token['expires_on']=str(time.time()+3599)
            if token.get('access_token'):
                    with open(token_path,'w') as f:
                        json.dump(token,f,ensure_ascii=False)
        return token.get('access_token')
    else:
        return False

def GetAppUrl():
    return 'https://graph.microsoft.com/'


def GetExt(name):
    try:
        return name.split('.')[-1]
    except:
        return 'file'

def date_to_char(date):
    return date.strftime('%Y/%m/%d')

def CheckTimeOut(fileid):
    app_url=GetAppUrl()
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    headers.update(default_headers)
    url=app_url+'v1.0/me/drive/mongo.db.items/'+fileid
    r=requests.get(url,headers=headers)
    data=json.loads(r.content)
    if data.get('@microsoft.graph.downloadUrl'):
        downloadUrl=data.get('@microsoft.graph.downloadUrl')
        start_time=time.time()
        for i in range(10000):
            r=requests.head(downloadUrl)
            print '{}\'s gone, status:{}'.format(time.time()-start_time,r.status_code)
            if r.status_code==404:
                break

def RemoveRepeatFile():
    """
    db.mongo.db.items.aggregate([
        {
            $group:{_id:{id:'$id'},count:{$sum:1},dups:{$addToSet:'$_id'}}
        },
        {
            $match:{count:{$gt:1}}
        }

        ]).forEach(function(it){

             it.dups.shift();
            db.mongo.db.items.remove({_id: {$in: it.dups}});

        });
    """
    deleteData=mongo.db.items.aggregate([
    {'$group': {
        '_id': { 'id': "$id"},
        'uniqueIds': { '$addToSet': "$_id" },
        'count': { '$sum': 1 }
      }},
      { '$match': {
        'count': { '$gt': 1 }
      }}
    ]);
    first=True
    try:
        for d in deleteData:
            first=True
            for did in d['uniqueIds']:
                if not first:
                    mongo.db.items.delete_one({'_id':did});
                first=False
    except Exception as e:
        print(e)
        return

def get_aria2():
    try:
        p=PyAria2()
        return p,True
    except Exception as e:
        return e,False


def _filesize(path):
    size=os.path.getsize(path)
    # print('{}\'s size {}'.format(path,size))
    return size

def list_all_files(rootdir):
    import os
    _files = []
    if len(re.findall('[:#\|\?]+',rootdir))>0:
        newf=re.sub('[:#\|\?]+','',rootdir)
        shutil.move(rootdir,newf)
        rootdir=newf
    if rootdir.endswith(' '):
        shutil.move(rootdir,rootdir.rstrip())
        rootdir=rootdir.rstrip()
    if len(re.findall('/ ',rootdir))>0:
        newf=re.sub('/ ','/',rootdir)
        shutil.move(rootdir,newf)
        rootdir=newf
    flist = os.listdir(rootdir) #列出文件夹下所有的目录与文件
    for f in flist:
        path = os.path.join(rootdir,f)
        if os.path.isdir(path):
            _files.extend(list_all_files(path))
        if os.path.isfile(path):
            _files.append(path)
    return _files


def _file_content(path,offset,length):
    size=_filesize(path)
    offset,length=map(int,(offset,length))
    if offset>size:
        print('offset must smaller than file size')
        return False
    length=length if offset+length<size else size-offset
    endpos=offset+length-1 if offset+length<size else size-1
    # print("read file {} from {} to {}".format(path,offset,endpos))
    with open(path,'rb') as f:
        f.seek(offset)
        content=f.read(length)
    return content



def AddResource(data,user='A'):
    #检查父文件夹是否在数据库，如果不在则获取添加
    grand_path=data.get('parentReference').get('path').replace('/drive/root:','') #空值或者/path
    share_path=od_users.get(user).get('share_path')
    if share_path!='/' and share_path.startswith('/'):
        share_path=share_path[1:]
    if grand_path=='':
        parent_id=''
        grandid=0
    else:
        g=GetItemThread(Queue(),user)
        parent_id=data.get('parentReference').get('id')
        grand_path=grand_path[1:]
        grand_path=grand_path.replace(share_path,'',1)
        grandid=len(grand_path.split('/'))-1
        if grand_path.startswith('/'):
            grand_path=grand_path[1:]
        if grand_path!='':
            parent_path='/'
            pid=''
            for idx,p in enumerate(grand_path.split('/')):
                parent=mongo.db.items.find_one({'name':p,'grandid':idx,'parent':pid})
                if parent is not None:
                    pid=parent['id']
                    parent_path='/'.join([parent_path,parent['name']])
                else:
                    parent_path='/'.join([parent_path,p])
                    fdata=g.GetItemByPath(parent_path)
                    path=user+':/'+parent_path.replace('///','/')
                    path=path.replace('///','/').replace('//','/')
                    item={}
                    item['type']='folder'
                    item['user']=user
                    item['order']=0
                    item['name']=fdata.get('name')
                    item['id']=fdata.get('id')
                    item['size']=humanize.naturalsize(fdata.get('size'), gnu=True)
                    item['size_order']=fdata.get('size')
                    item['lastModtime']=date_to_char(parse(fdata['lastModifiedDateTime']))
                    item['grandid']=idx
                    item['parent']=pid
                    item['path']=path
                    mongo.db.items.insert_one(item)
                    pid=fdata.get('id')
    #插入数据
    item={}
    item['type']=GetExt(data.get('name'))
    item['name']=data.get('name')
    item['user']=user
    item['id']=data.get('id')
    item['size']=humanize.naturalsize(data.get('size'), gnu=True)
    item['size_order']=data.get('size')
    item['lastModtime']=date_to_char(parse(data.get('lastModifiedDateTime')))
    item['grandid']=grandid
    item['parent']=parent_id
    if grand_path=='':
        path=user+':/'+convert2unicode(data['name'])
    else:
        if share_path!='/':
            path=user+':/'+grand_path.replace(share_path,'',1)+'/'+convert2unicode(data['name'])
        else:
            path=user+':/'+grand_path+'/'+convert2unicode(data['name'])
    path=path.replace('//','/')
    print('new file path:{}'.format(path))
    item['path']=path
    if GetExt(data['name']) in ['bmp','jpg','jpeg','png','gif']:
        item['order']=3
        # key1='name:{}'.format(data['id'])
        # key2='path:{}'.format(data['id'])
        # redis_client.set(key1,data['name'])
        # redis_client.set(key2,path)
    elif data['name']=='.password':
        item['order']=1
    else:
        item['order']=2
    mongo.db.items.insert_one(item)

def CheckTimeOut(fileid):
    app_url=GetAppUrl()
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    headers.update(default_headers)
    url=app_url+'v1.0/me/drive/mongo.db.items/'+fileid
    r=requests.get(url,headers=headers)
    data=json.loads(r.content)
    if data.get('@microsoft.graph.downloadUrl'):
        downloadUrl=data.get('@microsoft.graph.downloadUrl')
        start_time=time.time()
        for i in range(10000):
            r=requests.head(downloadUrl)
            print '{}\'s gone, status:{}'.format(time.time()-start_time,r.status_code)
            if r.status_code==404:
                break


class GetItemThread(Thread):
    def __init__(self,queue,user):
        super(GetItemThread,self).__init__()
        self.queue=queue
        self.user=user
        self._stop_event = Event()
        share_path=od_users.get(user).get('share_path')
        if share_path=='/':
            self.share_path=share_path
        else:
            sp=share_path
            if not sp.startswith('/'):
                sp='/'+share_path
            if sp.endswith('/') and sp!='/':
                sp=sp[:-1]
            self.share_path=sp

    def run(self):
        while not self.queue.empty():
            time.sleep(0.5) #避免过快
            info=self.queue.get()
            url=info['url']
            grandid=info['grandid']
            parent=info['parent']
            trytime=info['trytime']
            self.GetItem(url,grandid,parent,trytime)
            if self.queue.empty():
                # print('{} queue empty!break'.format(self.user))
                break

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def GetItem(self,url,grandid=0,parent='',trytime=1):
        app_url=GetAppUrl()
        token=GetToken(user=self.user)
        print(u'[start] getting files from url {}'.format(url))
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        try:
            r=requests.get(url,headers=headers,timeout=10)
            data=json.loads(r.content)
            if data.get('error'):
                print('error:{}! waiting 180s'.format(data.get('error').get('message')))
                time.sleep(180)
                self.queue.put(dict(url=url,grandid=grandid,parent=parent,trytime=trytime))
                return
            values=data.get('value')
            if len(values)>0:
                for value in values:
                    item={}
                    if value.get('folder'):
                        folder=mongo.db.items.find_one({'id':value['id']})
                        if folder is not None:
                            if folder['size_order']==value['size']: #文件夹大小未变化，不更新
                                print(u'path:{},origin size:{},current size:{}--------no change'.format(value['name'],folder['size_order'],value['size']))
                            else:
                                mongo.db.items.delete_one({'id':value['id']})
                                item['type']='folder'
                                item['user']=self.user
                                item['order']=0
                                item['name']=convert2unicode(value['name'])
                                item['id']=convert2unicode(value['id'])
                                item['size']=humanize.naturalsize(value['size'], gnu=True)
                                item['size_order']=int(value['size'])
                                item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                                item['grandid']=grandid
                                item['parent']=parent
                                grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                if grand_path=='':
                                    path=convert2unicode(value['name'])
                                else:
                                    path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                                if path.startswith('/') and path!='/':
                                    path=path[1:]
                                if path=='':
                                    path=convert2unicode(value['name'])
                                path=urllib.unquote('{}:/{}'.format(self.user,path))
                                item['path']=path
                                subfodler=mongo.db.items.insert_one(item)
                                if value.get('folder').get('childCount')==0:
                                    continue
                                else:
                                    parent_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                    path=urllib.quote(convert2unicode(parent_path+'/'+value['name']))
                                    url=app_url+'v1.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                    self.queue.put(dict(url=url,grandid=grandid+1,parent=item['id'],trytime=1))
                        else:
                            mongo.db.items.delete_one({'id':value['id']})
                            item['type']='folder'
                            item['user']=self.user
                            item['order']=0
                            item['name']=convert2unicode(value['name'])
                            item['id']=convert2unicode(value['id'])
                            item['size']=humanize.naturalsize(value['size'], gnu=True)
                            item['size_order']=int(value['size'])
                            item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                            item['grandid']=grandid
                            item['parent']=parent
                            grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                            if grand_path=='':
                                path=convert2unicode(value['name'])
                            else:
                                path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                            if path.startswith('/') and path!='/':
                                path=path[1:]
                            if path=='':
                                path=convert2unicode(value['name'])
                            path=urllib.unquote('{}:/{}'.format(self.user,path))
                            item['path']=path
                            subfodler=mongo.db.items.insert_one(item)
                            if value.get('folder').get('childCount')==0:
                                continue
                            else:
                                parent_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                path=urllib.quote(convert2unicode(parent_path+'/'+value['name']))
                                url=app_url+'v1.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                self.queue.put(dict(url=url,grandid=grandid+1,parent=item['id'],trytime=1))
                    else:
                        if mongo.db.items.find_one({'id':value['id']}) is not None: #文件存在
                            continue
                        else:
                            item['type']=GetExt(value['name'])
                            grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                            if grand_path=='':
                                path=convert2unicode(value['name'])
                            else:
                                path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                            if path.startswith('/') and path!='/':
                                path=path[1:]
                            if path=='':
                                path=convert2unicode(value['name'])
                            path=urllib.unquote('{}:/{}'.format(self.user,path))
                            item['path']=path
                            item['user']=self.user
                            item['name']=convert2unicode(value['name'])
                            item['id']=convert2unicode(value['id'])
                            item['size']=humanize.naturalsize(value['size'], gnu=True)
                            item['size_order']=int(value['size'])
                            item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                            item['grandid']=grandid
                            item['parent']=parent
                            if GetExt(value['name']) in ['bmp','jpg','jpeg','png','gif']:
                                item['order']=3
                                key1='name:{}'.format(value['id'])
                                key2='path:{}'.format(value['id'])
                                redis_client.set(key1,value['name'])
                                redis_client.set(key2,path)
                            elif value['name']=='.password':
                                item['order']=1
                            else:
                                item['order']=2
                            mongo.db.items.insert_one(item)
            else:
                print('{}\'s size is zero'.format(url))
            if data.get('@odata.nextLink'):
                self.queue.put(dict(url=data.get('@odata.nextLink'),grandid=grandid,parent=parent,trytime=1))
            print(u'[success] getting files from url {}'.format(url))
        except Exception as e:
            trytime+=1
            print(u'error to opreate GetItem("{}","{}","{}"),try times :{}, reason: {}'.format(url,grandid,parent,trytime,e))
            if trytime<=3:
                self.queue.put(dict(url=url,grandid=grandid,parent=parent,trytime=trytime))


    def GetItemByPath(self,path):
        app_url=GetAppUrl()
        token=GetToken(user=self.user)
        path=urllib.quote(convert2unicode(path))
        if path=='' or path=='/':
            url=app_url+u'v1.0/me/drive/root/'
        else:
            url=app_url+u'v1.0/me/drive/root:{}:/'.format(path)
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=requests.get(url,headers=headers)
        data=json.loads(r.content)
        return data

    def GetItemByUrl(self,url):
        app_url=GetAppUrl()
        token=GetToken(user=self.user)
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=requests.get(url,headers=headers)
        data=json.loads(r.content)
        return data

def clearRedis():
    key_lists=['path:*','name:*','*has_item*','*root*']
    for k in key_lists:
        try:
            redis_client.delete(*redis_client.keys(k))
        except:
            print('empty keys {}'.format(k))

def CheckServer():
    mongo_cmd='lsof -i:27017 | grep LISTEN'
    redis_cmd='lsof -i:6379 | grep LISTEN'
    r1=len(subprocess.Popen(mongo_cmd,shell=True,stdout=subprocess.PIPE).stdout.readlines())
    r2=len(subprocess.Popen(redis_cmd,shell=True,stdout=subprocess.PIPE).stdout.readlines())
    msg='<h1><br>'
    if r1==0:
        msg+='<p>MongoDB未运行</p>'
    if r2==0:
        msg+='<p>Redis未运行</p>'
    msg+='</h1>'
    if r1==0 or r2==0:
        return msg,False
    else:
        return msg,True
