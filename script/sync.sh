#!/bin/bash

# 配置
MAIN_REPO="D:\czm我的世界\.minecraft\versions\1.21-Fabric 0.15.11\saves\Missile Wars\datapacks\Missile Wars Fusion for 1.21"
HIGH_REPO="D:\czm我的世界\.minecraft\versions\1.21.8-Fabric 0.16.14\saves\Missile Wars 1_21_8\datapacks\Missile Wars Fusion for 1.21.8"
CONVERT_SCRIPT="D:\czm我的世界\数据包\Missile Wars\script\updator.py"

cd "$MAIN_REPO"

# 1. 确保主仓库干净
if [ -n "$(git status --porcelain)" ]; then
  echo "错误：主仓库有未提交更改！"
  exit 1
fi

# 2. 获取当前版本
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "当前版本: $COMMIT_HASH"

# 3. 清空并准备高版本仓库
cd "$HIGH_REPO"
git checkout version-1.21.8
git clean -fd
git rm -rf .  # 删除所有文件

# 4. 复制并转换文件
python "$CONVERT_SCRIPT" "$HIGH_REPO" --copy-from "$MAIN_REPO"

# 6. 提交到高版本仓库
git add .
git commit -m "同步自1.21($COMMIT_HASH) $(date +%F)"