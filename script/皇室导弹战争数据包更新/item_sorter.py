import os
import re
import pandas as pd
import argparse
from pathlib import Path
import shutil
import logging
import json
from collections import defaultdict

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('FileSorter')

class FileSorter:
    def __init__(self, excel_path, config_path=None):
        self.excel_path = excel_path
        self.config_path = config_path
        self.items_df = None
        self.config = []
        self.file_stats = defaultdict(dict)
        
        # 默认配置
        self.default_config = [
            {
                "file_path": "data/missile_royale/function/game/choose/remove_saves.mcfunction",
                "description": "重排清除已选卡组的指令顺序",
                "start_regex": r"#清空玩家保存的卡组",
                "end_regex": r"",
                "item_regex": r"tag @s remove (\w+)",  # 提取道具ID
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/choose/save_cards.mcfunction",
                "description": "重排保存卡组的指令顺序",
                "start_regex": r"#保存玩家卡组",
                "end_regex": r"clear @s",
                "item_regex": r"execute if items entity @s hotbar\.\* minecraft:(\w*) run tag @s add \w*",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/tp.mcfunction",
                "description": "重排游戏开始时清空道具使用记录指令的顺序",
                "start_regex": r"#清空道具使用记录",
                "end_regex": r"#分发初始卡组",
                "item_regex": r"scoreboard players reset @a\[team=!\] use\.(\w*)",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/initiate/initiation.mcfunction",
                "description": "重排初始化道具使用变量的指令顺序",
                "start_regex": r"#设置道具使用变量",
                "end_regex": r"",
                "item_regex": r"scoreboard objectives add use\.(\w*) minecraft\.used:minecraft\.\w*",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/cost/remove.mcfunction",
                "description": "重排重置道具使用变量的指令顺序",
                "start_regex": r"#重置道具使用变量",
                "end_regex": r"",
                "item_regex": r"scoreboard players reset @a\[team=!\] use\.(\w*)",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/cost/remove.mcfunction",
                "description": "重排发牌指令的顺序",
                "start_regex": r"#发牌",
                "end_regex": r"#重置道具使用变量",
                "item_regex": r"execute as @a\[team=!,scores=\{use\.(\w*)=1\.\.\}\] run function missile_royale:game/deal/deal",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/cost/remove.mcfunction",
                "description": "重排扣费指令的顺序",
                "start_regex": r"#扣费",
                "end_regex": r"#发牌",
                "item_regex": r"xp add @a\[team=!,scores=\{use\.(\w*)=1\.\.\}\] -\d+ levels",
                "sort_by": ["类型", "编号"],  # 先按类型排序，再按编号排序
                "sort_order": "asc",  # 升序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/deal/deal.mcfunction",
                "description": "重排发牌指令的顺序",
                "start_regex": r"#分发新卡",
                "end_regex": r"clear @s\[team=!,level=0\] #missile_royale:above/above0",
                "item_regex": r"loot give @s\[team=!,tag=(\w*)\] loot \{[\S]*",
                "sort_by": ["类型", "费用"],  # 先按类型排序，再按费用排序
                "sort_order": "desc",  # 降序排序
                "backup": True
            },
            {
                "file_path": "data/missile_royale/function/game/choose/previous_cards.mcfunction",
                "description": "重排发放保留卡组指令的顺序",
                "start_regex": r"#每位玩家保留上一局游戏所用卡组",
                "end_regex": r"item modify entity @s hotbar\.1 missile_royale:cards",
                "item_regex": r"give @s\[tag=(\w*)\] \w*",
                "sort_by": ["类型", "费用"],  # 先按类型排序，再按费用排序
                "sort_order": "desc",  # 降序排序
                "backup": True
            }
        ]
        
        self.load_excel()
        self.load_config()

    def load_excel(self):
        """加载Excel数据"""
        try:
            # 读取Excel，保留原始数据类型
            self.items_df = pd.read_excel(self.excel_path, keep_default_na=False)
            logger.info(f"✅ 成功读取Excel文件: {self.excel_path}")
            logger.info(f"道具总数: {len(self.items_df)}")
            
            # 打印前5个道具作为示例
            logger.info("\n前5个道具示例:")
            logger.info(self.items_df.head().to_string(index=False))
            
            return True
        except Exception as e:
            logger.error(f"❌ 读取Excel失败: {e}")
            return False

    def load_config(self):
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"✅ 成功加载配置文件: {self.config_path}")
            except Exception as e:
                logger.error(f"❌ 加载配置文件失败: {e}")
                logger.info("⚠️ 使用默认配置")
                self.config = self.default_config
        else:
            logger.info("⚠️ 未提供配置文件，使用默认配置")
            self.config = self.default_config
            
        # 打印配置摘要
        logger.info("\n配置摘要:")
        for i, cfg in enumerate(self.config, 1):
            logger.info(f"  {i}. {cfg['description']}")
            logger.info(f"     文件: {cfg['file_path']}")
            logger.info(f"     排序字段: {', '.join(cfg['sort_by'])} ({cfg['sort_order']})")
            logger.info(f"     备份: {'是' if cfg.get('backup', True) else '否'}")

    def backup_file(self, file_path):
        """创建文件备份"""
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"🔁 创建备份: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 创建备份失败: {e}")
            return False

    def find_item_block(self, content, start_index, end_index, item_id):
        """查找特定道具的条目块"""
        # 构建匹配模式，查找以item_id开头的条目
        pattern = re.compile(fr"^\s*//\s*道具:\s*{re.escape(item_id)}\b.*?(?=^\s*//\s*道具:|\Z)", 
                           re.MULTILINE | re.DOTALL)
        
        match = pattern.search(content, start_index, end_index)
        if match:
            return match.start(), match.end(), match.group(0)
        return None, None, None

    def extract_items_from_region(self, content, start_index, end_index, item_regex):
        """从区域中提取所有条目块"""
        items = []
        pattern = re.compile(item_regex, re.MULTILINE)
        
        # 查找所有匹配
        pos = start_index
        while pos < end_index:
            match = pattern.search(content, pos, end_index)
            if not match:
                break
                
            item_id = match.group(1)
            # 获取完整条目块
            block_start, block_end, block_content = match.start(), match.end(), match.group(0)
            
            if block_content:
                items.append({
                    "id": item_id,
                    "start": block_start,
                    "end": block_end,
                    "content": block_content
                })
                pos = block_end
            else:
                pos = match.end()
        
        return items

    def sort_items(self, items, sort_fields, sort_order):
        """根据Excel数据排序条目"""
        # 创建排序键
        def get_sort_key(item, str_mode = False):
            key = []
            item_row = self.items_df[self.items_df['物品代号'] == item['id']]
            
            if not item_row.empty:
                for field in sort_fields:
                    value = item_row[field].values[0]
                    
                    if str_mode:
                        # 如果需要字符串排序，直接使用字符串
                        key.append(str(value))
                    else:
                        # 尝试转换为数字
                        try:
                            # 检查是否为数字类型
                            if isinstance(value, (int, float)):
                                key.append(value)
                            else:
                                # 尝试转换为数字
                                if '.' in value:
                                    key.append(float(value))
                                else:
                                    key.append(int(value))
                        except (ValueError, TypeError):
                            # 无法转换为数字，使用字符串
                            key.append(str(value))
            else:
                # 未找到的道具使用最大可能值，放在最后
                key.append(float('inf'))
            
            return tuple(key)
        
        # 排序
        try:
            sorted_items = sorted(items, key=get_sort_key, reverse=(sort_order.lower() == "desc"))
        except TypeError as e:
            logger.error(f"❌ 排序失败: {e}")
            logger.info("⚠️ 尝试使用字符串排序...")
            # 使用字符串作为备选方案
            sorted_items = sorted(items, key=lambda x: str(get_sort_key(x,True)), 
                                 reverse=(sort_order.lower() == "desc"))
        
        # 记录排序变化
        order_changes = []
        for new_idx, item in enumerate(sorted_items):
            old_idx = next((i for i, it in enumerate(items) if it['id'] == item['id']), -1)
            if old_idx != new_idx:
                order_changes.append(f"{item['id']}: {old_idx} → {new_idx}")
        
        return sorted_items, order_changes

    def process_file(self, config):
        """处理单个文件"""
        file_path = Path(config['file_path'])
        description = config['description']
        start_regex = config['start_regex']
        end_regex = config.get('end_regex')
        item_regex = config['item_regex']
        sort_fields = config['sort_by']
        sort_order = config.get('sort_order', 'asc')
        backup = config.get('backup', True)
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"处理文件: {file_path}")
        logger.info(f"描述: {description}")
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"❌ 文件不存在: {file_path}")
            self.file_stats[str(file_path)] = {"status": "error", "message": "文件不存在"}
            return False
        
        # 创建备份
        if backup:
            self.backup_file(file_path)
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"❌ 读取文件失败: {e}")
            self.file_stats[str(file_path)] = {"status": "error", "message": str(e)}
            return False
        
        # 查找起始位置
        start_match = re.search(start_regex, content)
        if not start_match:
            logger.error(f"❌ 未找到起始标记: {start_regex}")
            self.file_stats[str(file_path)] = {"status": "error", "message": "未找到起始标记"}
            return False
        
        start_index = start_match.end()
        
        # 查找结束位置
        end_index = len(content)
        if end_regex:
            end_match = re.search(end_regex, content[start_index:])
            if end_match:
                end_index = start_index + end_match.start()
            else:
                logger.warning("⚠️ 未找到结束标记，将使用文件末尾")
        
        # 提取区域内容
        region_content = content[start_index:end_index]
        
        # 提取条目块
        items = self.extract_items_from_region(content, start_index, end_index, item_regex)
        
        if not items:
            logger.warning("⚠️ 未找到任何条目块")
            self.file_stats[str(file_path)] = {"status": "warning", "message": "未找到条目块"}
            return True
        
        logger.info(f"找到 {len(items)} 个条目块")
        
        # 排序条目
        sorted_items, order_changes = self.sort_items(items, sort_fields, sort_order)
        
        if not order_changes:
            logger.info("✅ 条目已按所需顺序排列，无需更改")
            self.file_stats[str(file_path)] = {"status": "unchanged", "items_count": len(items)}
            return True
        
        # 打印顺序变化
        logger.info("\n顺序变化:")
        for change in order_changes:
            logger.info(f"  {change}")
        
        # 构建新的区域内容
        new_region_content = "\n".join(item['content'] for item in sorted_items)
        
        # 保留原始前缀和后缀
        prefix = content[:start_index]
        suffix = content[end_index:]
        
        # 创建新内容
        new_content = prefix + "\n\n" + new_region_content + "\n\n" + suffix
        
        # 写回文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"✅ 文件已更新: {file_path}")
            logger.info(f"修改条目数: {len(order_changes)}/{len(items)}")
            
            self.file_stats[str(file_path)] = {
                "status": "updated",
                "items_count": len(items),
                "changed_count": len(order_changes)
            }
            return True
        except Exception as e:
            logger.error(f"❌ 写入文件失败: {e}")
            self.file_stats[str(file_path)] = {"status": "error", "message": str(e)}
            return False

    def run(self):
        """执行所有文件处理"""
        if self.items_df is None or self.items_df.empty:
            logger.error("❌ Excel数据未加载，无法继续")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("开始处理文件")
        logger.info("=" * 60)
        
        success = True
        for cfg in self.config:
            result = self.process_file(cfg)
            if not result:
                success = False
        
        logger.info("\n" + "=" * 60)
        logger.info("处理完成!")
        logger.info("=" * 60)
        
        # 打印统计信息
        logger.info("\n处理统计:")
        for file, stats in self.file_stats.items():
            status = stats['status']
            if status == "updated":
                logger.info(f"  ✅ {file}: 更新了 {stats['changed_count']}/{stats['items_count']} 个条目")
            elif status == "unchanged":
                logger.info(f"  ⏩ {file}: {stats['items_count']} 个条目，无需更改")
            elif status == "warning":
                logger.info(f"  ⚠ {file}: {stats['message']}")
            else:
                logger.info(f"  ❌ {file}: 错误 - {stats['message']}")
        
        return success

def main():
    # parser = argparse.ArgumentParser(description='文件条目排序工具')
    # parser.add_argument('excel', type=str, help='Excel文件路径')
    # parser.add_argument('--config', type=str, default=None, help='配置文件路径')
    # parser.add_argument('--log', type=str, default='INFO', 
    #                     choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
    #                     help='日志级别')
    
    # args = parser.parse_args()
    
    # # 设置日志级别
    # logger.setLevel(args.log.upper())
    
    # 创建处理器
    sorter = FileSorter("../../doc/道具信息.xlsx", None)
    sorter.run()

if __name__ == "__main__":
    main()