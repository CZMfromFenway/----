import os
import filecmp
import difflib
import json
from pathlib import Path
import argparse

def compare_data_packs(new_data_dir, old_data_dir, output_file=None):
    """
    比较两个数据包目录中的文件差异
    
    参数:
    new_data_dir -- 修改后的数据包data目录
    old_data_dir -- 原始数据包的data目录
    output_file  -- 差异输出文件路径（可选）
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
    
    print(f"开始比较数据包:")
    print(f"  新数据包: {new_path}")
    print(f"  原始数据包: {old_path}")
    
    # 收集所有修改过的文件
    modified_files = []
    for root, dirs, files in os.walk(new_path):
        for file in files:
            # 跳过非文本文件（如图片、声音等）
            if file.split('.')[-1].lower() in ['png', 'jpg', 'ogg', 'wav', 'mp3']:
                continue
                
            rel_path = Path(root).relative_to(new_path)
            new_file = new_path / rel_path / file
            old_file = old_path / rel_path / file
            
            # 只比较在原始数据包中存在的文件
            if old_file.exists():
                modified_files.append((new_file, old_file, rel_path / file))
    
    print(f"找到 {len(modified_files)} 个需要比对的文件")
    
    # 比较结果
    diff_count = 0
    identical_count = 0
    output_lines = []
    
    # 添加标题
    title = f"数据包差异报告\n新旧目录对比:\n  新: {new_path}\n  旧: {old_path}\n\n"
    output_lines.append(title)
    
    for new_file, old_file, rel_path in modified_files:
        # 比较文件内容
        if filecmp.cmp(new_file, old_file, shallow=False):
            # 文件内容完全相同
            identical_count += 1
            result_line = f"✅ 文件相同: {rel_path}\n"
            output_lines.append(result_line)
        else:
            # 文件内容不同
            diff_count += 1
            result_line = f"❌ 文件不同: {rel_path}\n"
            output_lines.append(result_line)
            
            # 获取文件差异
            diff = get_file_diff(old_file, new_file)
            if diff:
                output_lines.append(diff)
    
    # 添加摘要
    summary = f"\n比较结果摘要:\n"
    summary += f"  总文件数: {len(modified_files)}\n"
    summary += f"  相同文件: {identical_count}\n"
    summary += f"  不同文件: {diff_count}\n"
    output_lines.append(summary)
    
    # 输出结果
    report = ''.join(output_lines)
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 差异报告已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
    
    # 控制台输出
    print(report)
    
    return True

def get_file_diff(old_file, new_file):
    """获取两个文件的差异对比"""
    try:
        # 读取文件内容
        with open(old_file, 'r', encoding='utf-8') as f:
            old_lines = f.readlines()
        
        with open(new_file, 'r', encoding='utf-8') as f:
            new_lines = f.readlines()
        
        # 生成差异
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=str(old_file),
            tofile=str(new_file),
            lineterm=''
        )
        
        # 格式化差异
        diff_text = ''.join(diff)
        return f"差异详情:\n{diff_text}\n{'='*80}\n"
    
    except UnicodeDecodeError:
        # 尝试二进制比较
        try:
            with open(old_file, 'rb') as f:
                old_data = f.read()
            
            with open(new_file, 'rb') as f:
                new_data = f.read()
            
            if old_data == new_data:
                return "⚠️ 文件内容相同（但文本比较失败）\n"
            else:
                return "⚠️ 文件内容不同（二进制文件，无法显示差异）\n"
        
        except Exception as e:
            return f"⚠️ 无法比较文件: {e}\n"
    
    except Exception as e:
        return f"⚠️ 比较文件时出错: {e}\n"

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='比较两个数据包目录中的文件差异')
    parser.add_argument('new_data', help='修改后的数据包data目录路径')
    parser.add_argument('old_data', help='原始数据包的data目录路径')
    parser.add_argument('-o', '--output', help='差异报告输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 执行比较
    compare_data_packs(args.new_data, args.old_data, args.output)