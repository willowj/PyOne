# PyOne - 基于Python的onedrive文件本地化浏览系统,使用MongoDB缓存文件

## PyOne3.0版本更新！！！支持多网盘绑定

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
    - **防盗链设置**。
    - **后台上传文件**。
    - **后台更新文件**。
    - **后台设置统计代码**
    - **后台管理onedrive文件**。
        - **删除onedrive文件**
        - **直接在后台给文件夹添加`.password`和`README`和`HEAD`**
        - **直接在后台编辑文本文件**。
        - **上传本地文件至onedrive**(2018.10.18更新）
        - **支持创建文件夹**(2018.10.19更新）
        - **支持移动文件（仅限单文件）**(2018.10.19更新）
4. **支持绑定多网盘！！！**（2018.11.15更新）

## 适用环境 ##
1. linux环境（推荐centos7）
2. Python2.7
3. **需要安装redis，MongoDB**

**推荐预先安装宝塔，再进行安装**

## 安装教程 ##
请转移到我的博客查看[安装教程](https://www.abbeyok.com/?p=174)

## 更新源码步骤 ##
- PyOne旧版本升级到3.0：**请重装！！！**
- PyOne3.0内小版本更新：
    1. 拉最新代码
    ```
    git pull
    ```
    5. 重新安装依赖，看是否有新增的依赖包：
    ```
    pip install -r requirements.txt
    ```
    6. 重启网站：
    ```
    supervisorctl -c supervisord.conf restart pyone
    ```
    7. 最好更新一下文件缓存：
    ```
    python function.py UpdateFile
    ```

## 提供安装服务 ##
[点击购买](https://iofaka.com/?gid=4)

