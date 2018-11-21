#!/etc/bash
#安装aria2
function install_aria2(){
    echo "7. 安装aria2";
    which aria2c > /dev/null 2>&1
    if [ $? == 0 ]; then
        echo "检测到已安装aria2"
        echo "请到后台配置aria2信息"
        echo "如果您配置了aria2授权信息，请确保是rpc-secret模式！如果不是，则不能正常工作。"
        echo "开启rpc-secret模式方法："
        echo "  >1. 编辑aria2的配置文件，将rpc-secret这一行反注释，然后'rpc-secret='后面填写密码"
        echo "  >2. 将rpc-user和rpc-passwd注释掉"
        echo "  >3. 重启aria2"
    else
        git clone https://github.com/abbeyokgo/aria2_installer.git
        cd aria2_installer
        sh install_aria2.sh
        echo "安装aria2完成"
        echo "如果已经成功安装，请到后台配置aria2信息"
        cd ..
        rm -rf aria2_installer
    fi
}


function update_config(){
    num=`cat config.py | grep "ARIA2_HOST" | wc -l`
    if [ $num == 0 ]; then
        echo 'ARIA2_HOST="localhost"' >> config.py
    fi
    num=`cat config.py | grep "ARIA2_PORT" | wc -l`
    if [ $num == 0 ]; then
        echo 'ARIA2_PORT=6800' >> config.py
    fi
    num=`cat config.py | grep "ARIA2_SECRET" | wc -l`
    if [ $num == 0 ]; then
        echo 'ARIA2_SECRET=""' >> config.py
    fi
    num=`cat config.py | grep "ARIA2_SCHEME" | wc -l`
    if [ $num == 0 ]; then
        echo 'ARIA2_SCHEME="http"' >> config.py
    fi
}
#11.20
function del_rubbish(){
    python -c "from function import *;down_db.delete_many({});"
}

#执行
echo "2018.11.20更新版本，修复了磁力链接下载的bug&上传、展示有特殊字符的文件出问题的bug。"
echo "2018.11.21更新版本，优化磁力下载功能-可选下载文件。"
echo "本次更新会删除离线下载历史数据"
del_rubbish
#之前的更新操作
install_aria2
update_config
supervisorctl -c supervisord.conf restart pyone
echo "---------------------------------------------------------------"
echo "更新完成！"
echo "  > 1. 检查/data/aria2是否存在。"
echo "  > 2. 检查aria2是否运行：pgrep 'aria2c'"
echo "    如果aria2没有运行，运行：sh /data/aria2/aria2.sh start"
echo "如果重启网站失败，请手动重启！"
echo "---------------------------------------------------------------"
echo
echo "PyOne交流群：864996565"

