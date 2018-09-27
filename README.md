# PyOne - 基于Python的onedrive文件本地化浏览系统,使用MongoDB缓存文件


## 说明 ##
1. 写PyOne更多的是为了自己的个性化需求，不具有通用性，这个版本基本完全照抄了oneindex的功能
2. 因为是为了自己的个性化需求，因此PyOne不会经常更新
3. PyOne适合Python程序猿进行二开

## 适用onedrive版本 ##
1. 个人版
2. onedrive商业版
3. onedrive教育版（需要学校管理员开启权限）

## 特性 ##
1. 简单易用。只需简单设置，即可做一个onedrive文件列表分享程序
2. 功能丰富。
    - 可设置文件夹密码。只需在文件夹添加`.password`文件，内容为密码内容，即可在该文件夹设置密码
    - 可设置README。
3. 后台强大。
    - 防盗链设置。
    - 后台上传文件。
    - 后台更新文件。
    - 后台管理onedrive文件。
        - 删除onedrive文件
        - 直接在后台给文件夹添加`.password`和`README`
        - 直接在后台编辑文本文件。

## 适用环境 ##
1. linux环境（推荐centos7）
2. Python2.7
3. **需要安装redis，MongoDB**

**推荐预先安装宝塔，再进行安装**

## 安装教程 ##
请转移到我的博客查看[安装教程](https://abbeyok.com/2018/09/23/pyone2-0/)

## 更新源码步骤 ##
1. 先将data目录和config.py复制出去
2. 删除原来的PyOne源码
3. 重新git clone一份PyOne源码
4. 将原来的data目录替换新源码的data目录，原来的config.py替换新源码的config.py

## 提供安装服务 ##
[点击购买](https://iofaka.com/?gid=4)
