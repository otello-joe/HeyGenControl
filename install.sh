#!/bin/bash
# 1. 将下载的二进制文件移动到用户 bin 目录
mkdir -p ~/bin
cp HeyGenControl_v1.0_Linux ~/bin/

# 2. 修改 .desktop 文件中的路径
DESKTOP_FILE="HeyGenControl.desktop"
sed -i "s|Exec=.*|Exec=$HOME/bin/HeyGenControl_v1.0_Linux|g" $DESKTOP_FILE

# 3. 安装到应用菜单
mkdir -p ~/.local/share/applications
cp $DESKTOP_FILE ~/.local/share/applications/

# 4. 给予执行权限
chmod +x ~/.local/share/applications/$DESKTOP_FILE

echo "✅ 已成功添加到桌面菜单！现在你可以在应用列表中搜索 'HeyGen' 了。"
