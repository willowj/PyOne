#!/etc/bash

#11.20
function del_rubbish(){
    python -c "from function import *;down_db.delete_many({});"
}

#执行
echo "2018.11.20更新版本，修复了磁力链接下载的bug&上传、展示有特殊字符的文件出问题的bug。"
echo "2018.11.21更新版本，优化磁力下载功能-可选下载文件。"
echo "2018.12.04更新版本，优化磁力下载界面"
echo "2018.12.10更新版本，修复特定分享目录后，二级目录设置密码出错的bug"
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

