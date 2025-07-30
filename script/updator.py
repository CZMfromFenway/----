import os
import re
import json
import shutil
import argparse
from pathlib import Path

class MinecraftUpgrader:
    def __init__(self, config_path=None):
        self.config = []
        self.total_replacements = 0
        self.total_files_processed = 0
        self.total_files_modified = 0
        
        # 根据您提供的规则生成的默认配置
        self.default_config = [
            {
                "name": "规则1 - 引号处理",
                "description": "处理特殊引号格式",
                "path": "data/missile_wars/function/platform/*.mcfunction",
                "recursive": True,
                "patterns": [
                    {
                        "search": "'\"|\"'",
                        "replace": "'"
                    }
                ]
            },
            {
                "name": "规则2 - 简化物品格式",
                "description": "简化物品对象格式",
                "path": "**/recipe/*.json",
                "recursive": True,
                "patterns": [
                    {
                        "search": r'\{\s*"item": (.*?)\s*\}',
                        "replace": r'\1'
                    }
                ]
            },
            {
                "name": "规则3 - 数组格式更新",
                "description": "更新数组表示格式",
                "path": "**/over.mcfunction",
                "recursive": True,
                "patterns": [
                    {
                        "search": r'\[I;(\d+),(\d+)\]',
                        "replace": r'[\1,\2]'
                    }
                ]
            },
            {
                "name": "规则4 - 弓物品属性更新",
                "description": "更新弓物品的属性和显示",
                "path": "data/**/*.mcfunction",
                "recursive": True,
                "patterns": [
                    {
                        "search": r'bow\[custom_name="\{\\"text\\":\\"弓\\",\\"color\\":\\"light_purple\\",\\"italic\\":false\}",lore=\["\{\\"text\\":\\"请发射箭矢以摧毁敌方导弹\\",\\"color\\":\\"gray\\",\\"italic\\":false\}"\],enchantments=\{flame:1,"missile_wars:explosive_arrow":1(.*?)\},unbreakable=\{show_in_tooltip:false\}\]',
                        "replace": r'bow[custom_name={"text":"弓","color":"light_purple","italic":false},lore=[{"text":"请发射箭矢以摧毁敌方导弹","color":"gray","italic":false}],enchantments={flame:1,"missile_wars:explosive_arrow":1\1},unbreakable={},tooltip_display={hidden_components:["unbreakable"]}]'
                    }
                ]
            },
            {
                "name": "规则5 - can_place_on属性更新",
                "description": "更新can_place_on属性格式",
                "path": "data/missile_wars/item_modifier/item/*.json",
                "recursive": True,
                "patterns": [
                    {
                        "search": r'"can_place_on": \{\s*"predicates": \[\s*\{\s*"blocks": "#missile_wars:game_block"\s*\}\s*\],\s*"show_in_tooltip": false\s*\}',
                        "replace": r'"can_place_on": {\n          "blocks": "#missile_wars:game_block"\n        },\n        "tooltip_display": {\n          "hidden_components": [\n            "can_place_on"\n          ]\n        }'
                    }
                ]
            },
            {
                "name": "规则6 - 文本组件重命名",
                "description": "更新事件属性命名规范",
                "path": "**/*.mcfunction",
                "recursive": True,
                "patterns": [
                    {
                        "search": r'"clickEvent":\{"action":"run_command","value"',
                        "replace": r'"click_event":{"action":"run_command","command"'
                    },
                    {
                        "search": r'"hoverEvent":\{"action":"show_text","contents"',
                        "replace": r'"hover_event":{"action":"show_text","value"'
                    }
                ]
            },
            {
                "name": "规则7 - 版本号更新",
                "description": "更新数据包版本号",
                "path": "pack.mcmeta",
                "recursive": False,
                "patterns": [
                    {
                        "search": r'"pack_format": \d+',
                        "replace": r'"pack_format": 81,\n        "supported_formats": [71,81]'
                    }
                ]
            }
        ]
        
        if config_path:
            self.load_config(config_path)
        else:
            self.config = self.default_config
    
    def load_config(self, config_path):
        """加载自定义配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ 成功加载配置文件: {config_path}")
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            print("⚠️ 使用默认配置")
            self.config = self.default_config
    
    def save_config(self, config_path):
        """保存当前配置到文件"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到: {config_path}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def copy_directory(self, source_dir, target_dir):
        """复制整个目录结构到目标目录，排除.git文件夹"""
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        
        if not source_path.exists():
            print(f"❌ 源目录不存在: {source_path}")
            return False
        
        print(f"📂 正在复制目录: {source_path} -> {target_path}")
        
        try:
            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 复制所有文件和子目录，排除.git文件夹
            file_count = 0
            dir_count = 0
            skipped_git = 0
            
            for item in source_path.glob('**/*'):
                # 排除.git目录及其内容
                if '.git' in item.parts:
                    skipped_git += 1
                    continue
                    
                relative_path = item.relative_to(source_path)
                dest_path = target_path / relative_path
                
                if item.is_file():
                    # 确保目标目录存在
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(item, dest_path)
                    file_count += 1
                    if file_count % 50 == 0:  # 每50个文件打印一次进度
                        print(f"  ↳ 已复制 {file_count} 个文件...")
                elif item.is_dir():
                    # 只创建目录，不复制内容（内容会通过文件复制处理）
                    dest_path.mkdir(parents=True, exist_ok=True)
                    dir_count += 1
            
            print(f"✅ 目录复制完成! "
                  f"文件: {file_count}, 目录: {dir_count}, 跳过.git项目: {skipped_git}")
            return True
        except Exception as e:
            print(f"❌ 复制目录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def find_files(self, base_path, pattern, recursive=True):
        """根据模式查找文件"""
        files = []
        base_path = Path(base_path)
        
        if pattern == "**/*.json":
            # 递归查找所有JSON文件
            for file in base_path.rglob("*.json"):
                files.append(file)
        else:
            # 简单模式匹配
            if recursive:
                for file in base_path.rglob(pattern):
                    if file.is_file():
                        files.append(file)
            else:
                for file in base_path.glob(pattern):
                    if file.is_file():
                        files.append(file)
        
        return files
    
    def apply_replacements(self, content, patterns):
        """应用所有替换规则到内容"""
        total_replacements = 0
        
        for pattern in patterns:
            try:
                # 处理多行匹配
                flags = re.DOTALL if '\n' in pattern.get("search", "") else 0
                search_regex = re.compile(pattern["search"], flags)
                
                # 执行替换
                new_content, count = search_regex.subn(pattern["replace"], content)
                
                if count > 0:
                    content = new_content
                    total_replacements += count
            except Exception as e:
                print(f"⚠️ 正则表达式错误: {pattern.get('search', '')} - {e}")
        
        return content, total_replacements
    
    def upgrade_datapack(self, datapack_path):
        """升级整个数据包"""
        datapack_path = Path(datapack_path)
        if not datapack_path.exists():
            print(f"❌ 数据包路径不存在: {datapack_path}")
            return False
        
        print(f"\n开始升级数据包: {datapack_path.name}")
        print("=" * 60)
        
        # 重置统计
        self.total_replacements = 0
        self.total_files_processed = 0
        self.total_files_modified = 0
        
        # 处理每个升级操作
        for operation in self.config:
            print(f"\n▶ 执行操作: {operation['name']}")
            print(f"  {operation['description']}")
            
            # 查找匹配的文件
            files = self.find_files(datapack_path, operation.get("path", "**/*.json"), 
                                  operation.get("recursive", True))
            
            if not files:
                print("  ⚠ 没有找到匹配的文件")
                continue
            
            op_replacements = 0
            op_files_modified = 0
            
            for file_path in files:
                self.total_files_processed += 1
                
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 应用替换规则
                    new_content, replacements = self.apply_replacements(
                        content, operation["patterns"]
                    )
                    
                    if replacements > 0:
                        # 写回修改后的内容
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ {file_path.relative_to(datapack_path)} - 修改了 {replacements} 处")
                        self.total_replacements += replacements
                        op_replacements += replacements
                        self.total_files_modified += 1
                        op_files_modified += 1
                    else:
                        print(f"  ⏩ {file_path.relative_to(datapack_path)} - 无修改")
                
                except Exception as e:
                    print(f"  ❌ 处理文件失败: {file_path} - {str(e)}")
            
            print(f"  {op_files_modified} 个文件被修改，共 {op_replacements} 处更改")
        
        # 打印总统计
        print("\n" + "=" * 60)
        print("升级完成!")
        print(f"处理文件总数: {self.total_files_processed}")
        print(f"修改文件数: {self.total_files_modified}")
        print(f"总修改处数: {self.total_replacements}")
        print("=" * 60)
        
        return True
    
    def preview_upgrade(self, datapack_path):
        """预览升级将做的更改（不实际修改文件）"""
        datapack_path = Path(datapack_path)
        if not datapack_path.exists():
            print(f"❌ 数据包路径不存在: {datapack_path}")
            return False
        
        print(f"\n预览数据包升级: {datapack_path.name}")
        print("=" * 60)
        print("注意: 此操作不会实际修改文件\n")
        
        # 重置统计
        total_replacements = 0
        total_files_processed = 0
        total_files_modified = 0
        
        # 处理每个升级操作
        for operation in self.config:
            print(f"\n▶ 操作预览: {operation['name']}")
            print(f"  {operation['description']}")
            
            # 查找匹配的文件
            files = self.find_files(datapack_path, operation.get("path", "**/*.json"), 
                                  operation.get("recursive", True))
            
            if not files:
                print("  ⚠ 没有找到匹配的文件")
                continue
            
            op_replacements = 0
            op_files_modified = 0
            
            for file_path in files:
                total_files_processed += 1
                
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 应用替换规则（但不保存）
                    _, replacements = self.apply_replacements(
                        content, operation["patterns"]
                    )
                    
                    if replacements > 0:
                        print(f"  🔍 {file_path.relative_to(datapack_path)} - 将修改 {replacements} 处")
                        total_replacements += replacements
                        op_replacements += replacements
                        total_files_modified += 1
                        op_files_modified += 1
                    else:
                        print(f"  ⏩ {file_path.relative_to(datapack_path)} - 无修改")
                
                except Exception as e:
                    print(f"  ❌ 处理文件失败: {file_path} - {str(e)}")
            
            print(f"  {op_files_modified} 个文件将被修改，共 {op_replacements} 处更改")
        
        # 打印总统计
        print("\n" + "=" * 60)
        print("升级预览完成!")
        print(f"将处理文件总数: {total_files_processed}")
        print(f"将修改文件数: {total_files_modified}")
        print(f"将修改处数: {total_replacements}")
        print("=" * 60)
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Minecraft 数据包升级助手')
    parser.add_argument('datapack', type=str, help='数据包路径')
    parser.add_argument('--config', type=str, default=None, help='自定义配置文件路径')
    parser.add_argument('--preview', action='store_true', help='预览升级将做的更改（不实际修改文件）')
    parser.add_argument('--save-config', type=str, default=None, help='保存当前配置到文件')
    parser.add_argument('--copy-from', type=str, default=None, help='复制源目录路径')
    
    args = parser.parse_args()
    
    # 创建升级器
    upgrader = MinecraftUpgrader(args.config)
    
    # 保存配置（如果需要）
    if args.save_config:
        upgrader.save_config(args.save_config)
        return
    
    # 执行目录复制（如果需要）
    if args.copy_from:
        if not upgrader.copy_directory(args.copy_from, args.datapack):
            print("❌ 目录复制失败，升级中止")
            return
    
    # 执行升级或预览
    if args.preview:
        upgrader.preview_upgrade(args.datapack)
    else:
        upgrader.upgrade_datapack(args.datapack)

if __name__ == "__main__":
    main()