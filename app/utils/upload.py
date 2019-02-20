#-*- coding=utf-8 -*-
from header import *
import header

def _upload(filepath,remote_path,user='A'): #remote_path like 'share/share.mp4'
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token)}
    headers.update(default_headers)
    url=app_url+'v1.0/me/drive/root:{}:/content'.format(urllib.quote(convert2unicode(remote_path)))
    r=requests.put(url,headers=headers,data=open(filepath,'rb'))
    try:
        data=json.loads(r.content)
        trytime=1
        while 1:
            try:
                if data.get('error'):
                    print(data.get('error').get('message'))
                    yield {'status':'upload fail!'}
                    break
                elif r.status_code==201 or r.status_code==200:
                    print('upload {} success!'.format(filepath))
                    AddResource(data,user)
                    yield {'status':'upload success!'}
                    break
                else:
                    print(data)
                    yield {'status':'upload fail!'}
                    break
            except Exception as e:
                trytime+=1
                print('error to opreate _upload("{}","{}"), try times {},error:{}'.format(filepath,remote_path,trytime,e))
                yield {'status':'upload fail! retry!'}
            if trytime>3:
                yield {'status':'upload fail! touch max retry time(3)'}
                break
    except:
        print(u'upload fail!content')
        print(r.content)

def _upload_part(uploadUrl, filepath, offset, length,trytime=1):
    size=header._filesize(filepath)
    offset,length=map(int,(offset,length))
    if offset>size:
        print('offset must smaller than file size')
        return {'status':'fail','msg':'params mistake','code':1}
    length=length if offset+length<size else size-offset
    endpos=offset+length-1 if offset+length<size else size-1
    print('upload file {} {}%'.format(filepath,round(float(endpos)/size*100,1)))
    filebin=header._file_content(filepath,offset,length)
    headers={}
    # headers['Authorization']='bearer {}'.format(token)
    headers['Content-Length']=str(length)
    headers['Content-Range']='bytes {}-{}/{}'.format(offset,endpos,size)
    headers.update(default_headers)
    try:
        r=requests.put(uploadUrl,headers=headers,data=filebin)
        data=json.loads(r.content)
        if r.status_code==201 or r.status_code==200:
            print(u'{} upload success!'.format(filepath))
            return {'status':'success','msg':'all upload success','code':0,'info':data}
        elif r.status_code==202:
            offset=data.get('nextExpectedRanges')[0].split('-')[0]
            return {'status':'success','msg':'partition upload success','code':1,'offset':offset}
        else:
            trytime+=1
            if trytime<=3:
                return {'status':'fail'
                        ,'msg':'please retry'
                        ,'sys_msg':data.get('error').get('message')
                        ,'code':2,'trytime':trytime}
            else:
                return {'status':'fail'
                        ,'msg':'retry times limit'
                        ,'sys_msg':data.get('error').get('message')
                        ,'code':3}
    except Exception as e:
        print('error to opreate _upload_part("{}","{}","{}","{}"), try times {},reason:{}'.format(uploadUrl, filepath, offset, length,trytime,e))
        trytime+=1
        if trytime<=3:
            return {'status':'fail','msg':'please retry','code':2,'trytime':trytime,'sys_msg':''}
        else:
            return {'status':'fail','msg':'retry times limit','code':3,'sys_msg':''}

def CreateUploadSession(path,user='A'):
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    headers.update(default_headers)
    url=app_url+u'v1.0/me/drive/root:{}:/createUploadSession'.format(urllib.quote(convert2unicode(path)))
    data={
          "item": {
            "@microsoft.graph.conflictBehavior": "fail",
          }
        }
    try:
        r=requests.post(url,headers=headers,data=json.dumps(data))
        retdata=json.loads(r.content)
        if r.status_code==409:
            print('file exists')
            return False
        else:
            return retdata
    except Exception as e:
        print('error to opreate CreateUploadSession("{}"),reason {}'.format(path,e))
        return False

def UploadSession(uploadUrl, filepath,user):
    length=327680*10
    offset=0
    trytime=1
    filesize=header._filesize(filepath)
    while 1:
        result=_upload_part(uploadUrl, filepath, offset, length,trytime=trytime)
        code=result['code']
        #上传完成
        if code==0:
            AddResource(result['info'],user)
            yield {'status':'upload success!','uploadUrl':uploadUrl}
            break
        #分片上传成功
        elif code==1:
            trytime=1
            offset=result['offset']
            per=round((float(offset)/filesize)*100,1)
            yield {'status':'partition upload success! {}%'.format(per),'uploadUrl':uploadUrl}
        #错误，重试
        elif code==2:
            if result['sys_msg']=='The request has been throttled':
                print(result['sys_msg']+' ; wait for 1800s')
                yield {'status':'The request has been throttled! wait for 1800s','uploadUrl':uploadUrl}
                time.sleep(1800)
            offset=offset
            trytime=result['trytime']
            yield {'status':'partition upload fail! retry!','uploadUrl':uploadUrl}
        #重试超过3次，放弃
        elif code==3:
            yield {'status':'partition upload fail! touch max retry times!','uploadUrl':uploadUrl}
            break

def Upload_for_server(filepath,remote_path=None,user='A'):
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    if remote_path is None:
        remote_path=os.path.basename(filepath)
    if remote_path.endswith('/'):
        remote_path=os.path.join(remote_path,os.path.basename(filepath))
    if not remote_path.startswith('/'):
        remote_path='/'+remote_path
    filepath=convert2unicode(filepath)
    remote_path=convert2unicode(remote_path)
    print('local file path:{}, remote file path:{}'.format(filepath,remote_path))
    if header._filesize(filepath)<1024*1024*3.25:
        for msg in _upload(filepath,remote_path,user):
            yield msg
    else:
        session_data=CreateUploadSession(remote_path,user)
        if session_data==False:
            yield {'status':'file exists!'}
        else:
            if session_data.get('uploadUrl'):
                uploadUrl=session_data.get('uploadUrl')
                for msg in UploadSession(uploadUrl,filepath,user):
                    yield msg
            else:
                print('user:{} create upload session fail! {},{}'.format(user,remote_path,session_data.get('error').get('message')))
                yield {'status':'user:{};create upload session fail!{}'.format(user,session_data.get('error').get('message'))}

def ContinueUpload(filepath,uploadUrl,user):
    headers={'Content-Type':'application/json'}
    headers.update(default_headers)
    r=requests.get(uploadUrl,headers=headers)
    data=json.loads(r.text)
    offset=data.get('nextExpectedRanges')[0].split('-')[0]
    expires_on=time.mktime(parse(data.get('expirationDateTime')).timetuple())
    if time.time()>expires_on:
        yield 'alright expired!'
    else:
        length=327680*10
        trytime=1
        filesize=header._filesize(filepath)
        while 1:
            result=_upload_part(uploadUrl, filepath, offset, length,trytime=trytime)
            code=result['code']
            #上传完成
            if code==0:
                AddResource(result['info'],user)
                yield {'status':'upload success!'}
                break
            #分片上传成功
            elif code==1:
                trytime=1
                offset=result['offset']
                per=round((float(offset)/filesize)*100,1)
                yield {'status':'partition upload success! {}%'.format(per)}
            #错误，重试
            elif code==2:
                if result['sys_msg']=='The request has been throttled':
                    print(result['sys_msg']+' ; wait for 1800s')
                    yield {'status':'The request has been throttled! wait for 1800s'}
                    time.sleep(1800)
                offset=offset
                trytime=result['trytime']
                yield {'status':'partition upload fail! retry!'}
            #重试超过3次，放弃
            elif code==3:
                yield {'status':'partition upload fail! touch max retry times!'}
                break

def Upload(filepath,remote_path=None,user='A'):
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    if remote_path is None:
        remote_path=os.path.basename(filepath)
    if remote_path.endswith('/'):
        remote_path=os.path.join(remote_path,os.path.basename(filepath))
    if not remote_path.startswith('/'):
        remote_path='/'+remote_path
    if header._filesize(filepath)<1024*1024*3.25:
        for msg in _upload(filepath,remote_path,user):
            1
    else:
        session_data=CreateUploadSession(remote_path,user)
        if session_data==False:
            return {'status':'file exists!'}
        else:
            if session_data.get('uploadUrl'):
                uploadUrl=session_data.get('uploadUrl')
                for msg in UploadSession(uploadUrl,filepath,user):
                    1
            else:
                print(session_data.get('error').get('msg'))
                print('create upload session fail! {}'.format(remote_path))
                return {'status':'create upload session fail!'}


class MultiUpload(Thread):
    def __init__(self,waiting_queue,user):
        super(MultiUpload,self).__init__()
        self.queue=waiting_queue
        self.user=user

    def run(self):
        while not self.queue.empty():
            localpath,remote_dir=self.queue.get()
            cp='{}:/{}'.format(self.user,remote_dir)
            if mon_db.items.find_one({'path':cp}):
                print(u'{} exists!'.format(cp))
            else:
                Upload(localpath,remote_dir,self.user)


def UploadDir(local_dir,remote_dir,user,threads=5):
    print(u'geting file from dir {}'.format(local_dir))
    localfiles=list_all_files(local_dir)
    print(u'get {} files from dir {}'.format(len(localfiles),local_dir))
    print(u'check filename')
    for f in localfiles:
        dir_,fname=os.path.dirname(f),os.path.basename(f)
        if len(re.findall('[:/#\|]+',fname))>0:
            newf=os.path.join(dir_,re.sub('[:/#\|]+','',fname))
            shutil.move(f,newf)
    localfiles=list_all_files(local_dir)
    check_file_list=[]
    if local_dir.endswith('/'):
        local_dir=local_dir[:-1]
    for file in localfiles:
        dir_,fname=os.path.dirname(file),os.path.basename(file)
        remote_path=remote_dir+'/'+dir_.replace(local_dir,'')+'/'+fname
        remote_path=remote_path.replace('//','/')
        check_file_list.append((remote_path,file))
    queue=Queue()
    tasks=[]
    for remote_path,file in check_file_list:
        queue.put((file,remote_path))
    print "start upload files 5s later"
    time.sleep(5)
    for i in range(min(threads,queue.qsize())):
        t=MultiUpload(queue,user)
        t.start()
        tasks.append(t)
    for t in tasks:
        t.join()
    #删除错误数据
    RemoveRepeatFile()
