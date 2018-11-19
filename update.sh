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
        rm -rf aria2_installer
    fi
}




#执行
install_aria2
supervisorctl -c supervisord.conf restart pyone
echo "---------------------------------------------------------------"
echo "更新完成！"
echo "---------------------------------------------------------------"
echo
echo "PyOne交流群：864996565"

