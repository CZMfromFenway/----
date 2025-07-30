#!/bin/bash
# 双版本数据包发布脚本

# ===== 配置区域 =====
# 版本信息
VERSION="1.2 pre-2"
LOW_VERSION="1.21"
HIGH_VERSION="1.21.5-1.21.8"

# 数据包名称
PACK_NAME="Missile Wars-Royale Fusion"

# 仓库目录
LOW_REPO_DIR="D:/czm我的世界/.minecraft/versions/1.21-Fabric 0.15.11/saves/Missile Wars/datapacks/Missile Wars Fusion for 1.21"
HIGH_REPO_DIR="D:/czm我的世界/.minecraft/versions/1.21.8-Fabric 0.16.14/saves/Missile Wars 1_21_8/datapacks/Missile Wars Fusion for 1.21.8"

# 输出目录
OUTPUT_DIR="D:/czm我的世界/数据包/Missile Wars/release"

# 压缩格式
ARCHIVE_FORMAT="zip"  # 可选 zip 或 tar

# ===== 脚本主体 =====
# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 函数：安全打包仓库
package_repo() {
    local repo_dir="$1"
    local version_name="$2"
    local output_file="$3"
    
    echo "=== 正在打包 $version_name 版本 ==="
    echo "仓库目录: $repo_dir"
    echo "输出文件: $output_file"
    
    # 检查仓库目录是否存在
    if [ ! -d "$repo_dir" ]; then
        echo "❌ 错误：仓库目录不存在: $repo_dir"
        return 1
    fi
    
    # 进入仓库目录
    pushd "$repo_dir" > /dev/null || return 1
    
    # 检查是否是Git仓库
    if [ ! -d ".git" ]; then
        echo "❌ 错误：目录不是Git仓库: $repo_dir"
        popd > /dev/null || return 1
        return 1
    fi
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️ 警告：仓库中有未提交的更改！"
        git status --short
        read -p "是否继续打包？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 打包已取消"
            popd > /dev/null || return 1
            return 1
        fi
    fi
    
    # 执行打包
    echo "🛠️ 正在创建 $ARCHIVE_FORMAT 压缩包..."
    if [ "$ARCHIVE_FORMAT" = "zip" ]; then
        git archive --format zip -o "$output_file" HEAD
    else
        git archive --format tar -o "${output_file%.*}.tar" HEAD
        gzip "${output_file%.*}.tar"
    fi
    
    # 验证压缩包
    if [ $? -eq 0 ] && [ -f "$output_file" ]; then
        file_size=$(du -h "$output_file" | cut -f1)
        echo "✅ 成功创建 $version_name 版本压缩包 ($file_size)"
    else
        echo "❌ 创建压缩包失败"
        popd > /dev/null || return 1
        return 1
    fi
    
    popd > /dev/null || return 1
    return 0
}

# 主打包流程
echo "🚀 开始发布 $PACK_NAME v$VERSION"
echo "========================================"

# 打包1.21版本
low_output_file="${OUTPUT_DIR}/${PACK_NAME} for ${LOW_VERSION} v${VERSION}.${ARCHIVE_FORMAT}"
package_repo "$LOW_REPO_DIR" "$LOW_VERSION" "$low_output_file"

echo "----------------------------------------"

# 打包1.21.5-1.21.8版本
high_output_file="${OUTPUT_DIR}/${PACK_NAME} for ${HIGH_VERSION} v${VERSION}.${ARCHIVE_FORMAT}"
package_repo "$HIGH_REPO_DIR" "$HIGH_VERSION" "$high_output_file"

echo "========================================"
echo "🏁 发布流程完成"
echo "输出目录: $OUTPUT_DIR"
echo "生成的文件:"
ls -lh "$OUTPUT_DIR" | grep "$PACK_NAME"