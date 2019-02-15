#-*- coding=utf-8 -*-
from header import *

########################删除文件
def DeleteLocalFile(fileid):
    items.remove({'id':fileid})

def DeleteRemoteFile(fileid,user='A'):
    app_url=GetAppUrl()
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token)}
    url=app_url+'v1.0/me/drive/items/'+fileid
    r=requests.delete(url,headers=headers)
    if r.status_code==204:
        DeleteLocalFile(fileid)
        return True
    else:
        DeleteLocalFile(fileid)
        return False

########################
def CreateFolder(folder_name,grand_path,user='A'):
    app_url=GetAppUrl()
    token=GetToken(user=user)
    if grand_path=='' or grand_path is None or grand_path=='/':
        url=app_url+'v1.0/me/drive/root/children'
        parent_id=''
        grandid=0
    else:
        path='{}:/{}'.format(user,grand_path)
        parent=items.find_one({'path':path})
        parent_id=parent['id']
        grandid=parent['grandid']+1
        url=app_url+'v1.0/me/drive/items/{}/children'.format(parent['id'])
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    payload={
      "name": folder_name,
      "folder": {},
      "@microsoft.graph.conflictBehavior": "rename"
    }
    r=requests.post(url,headers=headers,data=json.dumps(payload))
    data=json.loads(r.content)
    if data.get('id'):
        #插入数据
        share_path=od_users.get(user).get('share_path')
        item={}
        item['type']='folder'
        item['user']=user
        item['name']=data.get('name')
        item['id']=data.get('id')
        item['size']=humanize.naturalsize(data.get('size'), gnu=True)
        item['size_order']=data.get('size')
        item['lastModtime']=date_to_char(parse(data.get('lastModifiedDateTime')))
        item['grandid']=grandid
        item['parent']=parent_id
        if grand_path=='' or grand_path is None or grand_path=='/':
            path=convert2unicode(data['name'])
        else:
            path=grand_path.replace(share_path,'',1)+'/'+convert2unicode(data['name'])
        if not path.startswith('/'):
            path='/'+path
        path='{}:{}'.format(user,path)
        item['path']=path
        item['order']=0
        items.insert_one(item)
        return True
    else:
        print(data.get('error').get('msg'))
        return False

def MoveFile(fileid,new_folder_path,user='A'):
    app_url=GetAppUrl()
    token=GetToken(user=user)
    #GetRootid
    if new_folder_path=='' or new_folder_path is None or new_folder_path=='/':
        folder_id=GetRootid(user)
        parent=''
        grandid=0
        path='{}:/{}'.format(user,GetName(fileid))
    else:
        path='{}:/{}'.format(user,new_folder_path)
        print path
        parent_item=items.find_one({'path':path})
        folder_id=parent_item['id']
        parent=parent_item['id']
        grandid=parent_item['grandid']+1
        path=parent_item['path']+'/'+GetName(fileid)
    url=app_url+'v1.0/me/drive/items/{}'.format(fileid)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    payload={
      "parentReference": {
        "id": folder_id
      },
      "name": GetName(fileid)
    }
    r=requests.patch(url,headers=headers,data=json.dumps(payload))
    data=json.loads(r.content)
    if data.get('id'):
        new_value={'parent':parent,'grandid':grandid,'path':path}
        items.find_one_and_update({'id':fileid},{'$set':new_value})
        file=items.find_one({'id':fileid})
        filename=file['name']
        if file['parent']=='':
            path='/'
        else:
            path=items.find_one({'id':file['parent']})['path']
        key='has_item$#$#$#$#{}$#$#$#$#{}'.format(path,filename)
        rd.delete(key)
        return True
    else:
        print(data.get('error').get('msg'))
        return False

def ReName(fileid,new_name,user='A'):
    app_url=GetAppUrl()
    token=GetToken(user=user)
    url=app_url+'v1.0/me/drive/items/{}'.format(fileid)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    payload={
      "name": new_name
    }
    r=requests.patch(url,headers=headers,data=json.dumps(payload))
    data=json.loads(r.content)
    if data.get('id'):
        it=items.find_one({'id':fileid})
        old_name=it['name']
        path=it['path'].replace(old_name,new_name,1)
        new_value={'path':path,'name':new_name}
        items.find_one_and_update({'id':fileid},{'$set':new_value})
        key='path:{}'.format(fileid)
        rd.delete(key)
        key='name:{}'.format(fileid)
        rd.delete(key)
        if it['type']=='folder':
            files=items.find({'parent':it['id']})
            for file in files:
                new_path=file['path'].replace(old_name,new_name,1)
                new_value={'path':new_path}
                items.find_one_and_update({'id':file['id']},{'$set':new_value})
        return True
    else:
        print(data.get('error').get('msg'))
        return False
