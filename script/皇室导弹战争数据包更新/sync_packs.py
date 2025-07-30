import os
import shutil
import argparse
from pathlib import Path
import sys

def sync_data_packs(new_data_dir, old_data_dir, dry_run=False):
    """
    同步数据包文件
    
    参数:
    new_data_dir -- 修改后的数据包data目录
    old_data_dir -- 原始数据包的data目录
    dry_run      -- 模拟运行，不实际复制文件
    """
    # 确保目录存在
    new_path = Path(new_data_dir)
    old_path = Path(old_data_dir)
    
    if not new_path.exists():
        print(f"❌ 新数据包目录不存在: {new_path}")
        return False
    
    if not old_path.exists():
        print(f"❌ 原始数据包目录不存在: {old_path}")
        return False
    
    print(f"开始同步数据包:")
    print(f"  来源: {new_path}")
    print(f"  目标: {old_path}")
    print(f"  模式: {'模拟运行' if dry_run else '实际复制'}")
    
    # 收集所有需要同步的文件
    files_to_sync = []
    for root, dirs, files in os.walk(new_path):
        for file in files:
            # 跳过备份文件
            if file.endswith('.bak'):
                continue
                
            rel_path = Path(root).relative_to(new_path)
            src_file = new_path / rel_path / file
            dest_file = old_path / rel_path / file
            
            files_to_sync.append((src_file, dest_file, rel_path / file))
    
    print(f"找到 {len(files_to_sync)} 个需要同步的文件")
    
    # 同步文件
    synced_count = 0
    skipped_count = 0
    created_dirs = set()
    
    for src, dest, rel_path in files_to_sync:
        # 检查源文件是否存在
        if not src.exists():
            print(f"⚠️ 源文件不存在: {src} (跳过)")
            skipped_count += 1
            continue
        
        # 检查目标目录是否存在
        dest_dir = dest.parent
        if not dest_dir.exists():
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.add(str(dest_dir))
            print(f"📁 创建目录: {dest_dir.relative_to(old_path)}")
        
        # 检查文件是否需要复制
        if dest.exists():
            # 比较文件内容
            if filecmp.cmp(src, dest, shallow=False):
                print(f"⏩ 文件相同: {rel_path} (跳过)")
                skipped_count += 1
                continue
            else:
                action = "更新"
        else:
            action = "新增"
        
        # 执行复制操作
        if not dry_run:
            try:
                shutil.copy2(src, dest)
                print(f"✅ {action}文件: {rel_path}")
                synced_count += 1
            except Exception as e:
                print(f"❌ 复制失败: {rel_path} - {e}")
                skipped_count += 1
        else:
            print(f"📝 [模拟] {action}文件: {rel_path}")
            synced_count += 1
    
    # 输出摘要
    print("\n同步结果摘要:")
    print(f"  总文件数: {len(files_to_sync)}")
    print(f"  同步文件: {synced_count}")
    print(f"  跳过文件: {skipped_count}")
    
    if created_dirs:
        print("\n创建的目录:")
        for dir_path in created_dirs:
            print(f"  - {Path(dir_path).relative_to(old_path)}")
    
    return True

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='同步数据包文件')
    parser.add_argument('new_data', help='修改后的数据包data目录路径')
    parser.add_argument('old_data', help='原始数据包的data目录路径')
    parser.add_argument('-d', '--dry-run', action='store_true', help='模拟运行，不实际复制文件')
    
    args = parser.parse_args()
    
    # 导入所需模块
    try:
        import filecmp
    except ImportError:
        print("❌ 需要filecmp模块，请确保使用标准Python环境")
        sys.exit(1)
    
    # 执行同步
    success = sync_data_packs(args.new_data, args.old_data, args.dry_run)
    
    if success:
        print("\n✅ 同步操作完成")
    else:
        print("\n⚠️ 同步操作未完成")