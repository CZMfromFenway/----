import pandas as pd
import os
import re
import json
from pathlib import Path
import shutil
import copy

def update_datapack(excel_path, config, column_mapping = None):
    """
    根据Excel表格更新Minecraft数据包文件，支持修改现有道具和添加新道具
    
    参数:
    excel_path -- Excel文件路径
    config -- 配置字典，包含文件处理规则
    """
    # 读取Excel数据
    try:
        df = pd.read_excel(excel_path)
        
        # 应用列名映射
        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
            print(f"已应用列名映射: {column_mapping}")
        
        # 创建道具名称到数据的映射
        # 使用道具代号作为主键（小写处理）
        items = {str(row['id']).lower(): row.to_dict() for _, row in df.iterrows()}
        
        # 添加原始道具名称到字典
        for key, item in items.items():
            item['道具名称'] = item.get('name', '')  # 保留中文名称
            
        print(f"成功读取 {len(items)} 个道具信息")
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return

    # 处理所有目标文件
    if 'item_loot_table' in config:
        process_item_loot_table(items, config['item_loot_table'])

    for file_path, file_config in config.items():

        # 处理 cost_group 类型（Xcost.json 文件组）
        if file_config.get('type') == 'cost_group':
            process_cost_group_files(items, file_config)
            continue
        file_path = Path(file_path)
        if not file_path.exists():
            # 如果文件不存在但需要自动创建
            if file_config.get('create_if_missing', False):
                print(f"创建新文件: {file_path}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if file_config['type'] == 'text':
                    file_path.touch()
                elif file_config['type'] == 'json':
                    with open(file_path, 'w') as f:
                        json.dump([], f, indent=2)
            else:
                print(f"文件不存在且未配置自动创建: {file_path}")
                continue
        
        try:
            # 文本文件处理
            if file_config['type'] == 'text':
                process_text_file(file_path, items, file_config)
            # JSON文件处理
            elif file_config['type'] == 'json':
                process_json_file(file_path, items, file_config)
                
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            import traceback
            traceback.print_exc()

def process_text_file(file_path, items, config):
    """处理文本文件"""
    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        original_content = content
        modified = False
        appended_items = set()
        
        # 处理每个道具
        for item_key, item_data in items.items():
            item_id = item_data['id']  # 道具代号
            item_cost = item_data['cost']  # 费用
            
            found = False
            
            # 应用所有规则
            for rule in config['rules']:
                # 准备正则表达式 - 使用道具代号替换<ID>占位符
                # 对道具代号进行正则转义（处理特殊字符）
                escaped_code = re.escape(item_id)
                pattern = rule['pattern'].replace('<ID>', escaped_code)
                
                # 编译正则表达式
                regex = re.compile(pattern, re.IGNORECASE)
                
                # 准备替换内容
                replacement = rule['replacement'].format(
                    id=item_id,
                    cost=item_cost
                )
                
                # 执行替换
                new_content, count = regex.subn(replacement, content)
                if count > 0:
                    print(f"在 {file_path.name} 中更新了 {item_data['id']} ({count} 处)")
                    content = new_content
                    modified = True
                    found = True
            
                # 如果没有找到匹配项且配置了追加规则
                if not found and 'append_template' in rule:
                    append_content = rule['append_template'].format(
                        id=item_id,
                        cost=item_cost
                    )
                    
                    # 检查是否已存在类似内容（避免重复追加）
                    if not re.search(re.escape(append_content), content, re.IGNORECASE):
                        # 确定追加位置
                        if 'append_after' in rule:
                            append_after_regex = re.compile(rule['append_after'])
                            match = append_after_regex.search(content)
                            if match:
                                pos = match.end()
                                content = content[:pos] + '\n' + append_content + content[pos:]
                            else:
                                content += '\n' + append_content
                        else:
                            content += '\n' + append_content
                        
                        print(f"在 {file_path.name} 中添加了新道具: {item_data['id']}")
                        modified = True
                        appended_items.add(item_id)
        
        # 如果有修改则写回文件
        if modified:
            f.seek(0)
            f.write(content)
            f.truncate()
            print(f"✅ 已更新文件: {file_path}")
        else:
            print(f"⏩ 未找到需要修改的内容: {file_path}")

def process_json_file(file_path, items, config):
    """处理JSON文件"""
    with open(file_path, 'r+', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"JSON解析错误，创建新结构: {file_path}")
            data = []
        
        # 定位目标列表
        target_list = data
        if 'json_path' in config:
            path_parts = config['json_path'].split('.')
            for part in path_parts:
                if part:  # 跳过空部分
                    if part not in target_list:
                        target_list[part] = []
                    target_list = target_list[part]
        
        if not isinstance(target_list, list):
            print(f"目标路径不是列表，创建新列表: {config['json_path']}")
            target_list = []
            if 'json_path' in config:
                # 重建路径
                current = data
                parts = config['json_path'].split('.')
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = target_list
        
        modified = False
        new_items_added = 0
        
        # 处理每个道具
        for item_key, item_data in items.items():
            item_name = item_data['name']
            found = False
            
            # 在列表中查找道具
            for obj in target_list:
                # 检查匹配条件
                if config['match_key'] in obj and str(obj[config['match_key']]).lower() == item_key:
                    # 更新现有道具
                    for field, template in config['update_fields'].items():
                        # 处理特殊字段（如NBT路径）
                        if field.startswith('nbt:'):
                            nbt_path = field[4:]
                            current = obj
                            parts = nbt_path.split('.')
                            for part in parts[:-1]:
                                if part not in current:
                                    current[part] = {}
                                current = current[part]
                            current[parts[-1]] = template.format(**item_data)
                        else:
                            # 更新普通字段
                            obj[field] = template.format(**item_data)
                    
                    print(f"在 {file_path.name} 中更新了 {item_name}")
                    modified = True
                    found = True
                    break
            
            # 如果没找到且需要添加新道具
            if not found and config.get('add_new_items', True):
                # 创建新道具对象
                new_obj = {}
                
                # 添加匹配键
                new_obj[config['match_key']] = item_name
                
                # 添加其他字段
                for field, template in config['update_fields'].items():
                    # 处理特殊字段
                    if field.startswith('nbt:'):
                        nbt_path = field[4:]
                        current = new_obj
                        parts = nbt_path.split('.')
                        for part in parts[:-1]:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                        current[parts[-1]] = template.format(**item_data)
                    else:
                        # 添加普通字段
                        new_obj[field] = template.format(**item_data)
                
                # 添加到列表
                target_list.append(new_obj)
                print(f"在 {file_path.name} 中添加了新道具: {item_name}")
                modified = True
                new_items_added += 1
        
        # 如果有修改则写回文件
        if modified:
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
            print(f"✅ 已更新JSON文件: {file_path} (添加了 {new_items_added} 个新道具)")
        else:
            print(f"⏩ JSON文件无需修改: {file_path}")

def process_cost_group_files(items, config):
    """
    处理 Xcost.json 文件组（费用分组文件）
    
    参数:
    items -- 道具字典 {道具代号: 道具数据}
    config -- 配置字典
        file_template: 文件路径模板 (如 "data/missile_royale/costs/{cost}cost.json")
        min_cost: 最小费用 (默认1)
        max_cost: 最大费用 (默认10)
    """
    # 获取配置参数
    file_template = config['file_template']
    min_cost = config.get('min_cost', 1)
    max_cost = config.get('max_cost', 10)
    
    print(f"\n处理费用分组文件: {file_template} (费用范围: {min_cost}-{max_cost})")
    
    # 按费用分组道具
    cost_groups = {}
    for item_code, item_data in items.items():
        try:
            cost = int(item_data['cost'])
            if min_cost <= cost <= max_cost:
                if cost not in cost_groups:
                    cost_groups[cost] = []
                cost_groups[cost].append(item_code)
        except (KeyError, ValueError, TypeError):
            print(f"⚠️ 道具 {item_code} 的费用无效: {item_data.get('cost')}")
    
    print(f"道具按费用分组: {cost_groups}")
    
    # 处理每个费用文件
    for cost in range(min_cost, max_cost + 1):
        file_path = file_template.format(cost=cost)
        path = Path(file_path)
        
        # 跳过不存在的文件
        if not path.exists():
            print(f"⏩ 文件不存在: {path} (跳过)")
            continue
        
        # 读取文件内容
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取文件失败: {path} - {e}")
            continue
        
        # 更新 values 数组
        if "values" in data:
            # 获取当前费用的道具列表
            current_items = cost_groups.get(cost, [])
            
            # 保留原始格式（字符串数组）
            data["values"] = current_items
            print(f"更新文件 {path.name}: 设置 {len(current_items)} 个道具")
            
            # 写回文件
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ 已更新: {path}")
            except Exception as e:
                print(f"写入文件失败: {path} - {e}")
        else:
            print(f"⚠️ 文件 {path} 缺少 'values' 键")

def process_item_loot_table(items, config):
    """
    处理道具专属战利品表文件（每个道具一个文件）
    
    参数:
    items -- 道具字典 {道具代号: 道具数据}
    config -- 配置字典
        directory: 目录路径
        template: 模板字典
    """
    directory = Path(config['directory'])
    template = config['template']
    
    # 确保目录存在
    directory.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    skipped_count = 0
    
    for item_code, item_data in items.items():
        # 文件路径
        file_path = directory / f"{item_code}.json"
        
        # 如果文件已存在，则跳过（根据需求，只创建不更新）
        if file_path.exists():
            # 可选：验证文件内容是否正确
            if config.get('verify_content', False):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    # 检查道具ID是否正确
                    if existing_data['pools'][0]['entries'][0]['name'] != item_code:
                        print(f"⚠️ 文件 {file_path.name} 中的道具ID不匹配，但跳过更新")
                except Exception as e:
                    print(f"⚠️ 验证文件 {file_path.name} 失败: {e}")
            skipped_count += 1
            continue
        
        # 创建新的战利品表文件
        try:
            # 深拷贝模板，避免修改原始模板
            loot_table = copy.deepcopy(template)
            
            # 替换道具ID
            loot_table['pools'][0]['entries'][0]['name'] = item_code
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(loot_table, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 创建战利品表文件: {file_path.name}")
            created_count += 1
        except Exception as e:
            print(f"创建文件 {file_path.name} 失败: {e}")
    
    print(f"战利品表处理完成: 创建了 {created_count} 个新文件, 跳过了 {skipped_count} 个已存在文件")

def backup_file(file_path):
    """创建文件备份"""
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    shutil.copyfile(file_path, backup_path)
    print(f"创建备份: {backup_path}")

if __name__ == "__main__":
    # =============== 配置区域 ===============
    # Excel文件路径（包含道具名称和费用）
    EXCEL_PATH = "../../doc/道具信息.xlsx"

    #列名映射
    COLUMN_MAPPING = {
    '道具名称': 'name',
    '物品代号': 'id',
    '费用': 'cost'
    }
    
    # 文件处理配置
    CONFIG = {
        # 扣费
        "data/missile_royale/function/game/cost/remove.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'xp add @a\[team=!,scores=\{use\.<ID>=1\.\.\}\] -\d+ levels',
                    "replacement": 'xp add @a[team=!,scores={{use.{id}=1..}}] -{cost} levels',
                    "append_template": '\nxp add @a[team=!,scores={{use.{id}=1..}}] -{cost} levels',
                    "append_after": r'#扣费'
                },
                {
                    "pattern": r'execute as @a\[team=!,scores=\{use\.<ID>=1\.\.\}\] run function missile_royale:game/deal/deal',
                    "replacement": 'execute as @a[team=!,scores={{use.{id}=1..}}] run function missile_royale:game/deal/deal',
                    "append_template": '\nexecute as @a[team=!,scores={{use.{id}=1..}}] run function missile_royale:game/deal/deal',
                    "append_after": r'#发牌'
                },
                {
                    "pattern": r'scoreboard players reset @a\[team=!\] use\.<ID>',
                    "replacement": 'scoreboard players reset @a[team=!] use.{id}',
                    "append_template": '\nscoreboard players reset @a[team=!] use.{id}',
                    "append_after": r'#重置道具使用变量'
                }
            ],
            "create_if_missing": True
        },
        
        # 初始化计分板
        "data/missile_royale/function/initiate/initiation.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'scoreboard objectives add use\.<ID> minecraft\.used:minecraft\.<ID>',
                    "replacement": 'scoreboard objectives add use.{id} minecraft.used:minecraft.{id}',
                    "append_template": '\nscoreboard objectives add use.{id} minecraft.used:minecraft.{id}',
                    "append_after": r'#设置道具使用变量'
                }
            ]
        },

        # 清除卡牌存储
        "data/missile_royale/function/game/choose/remove_saves.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'tag @s remove <ID>',
                    "replacement": 'tag @s remove {id}',
                    "append_template": 'tag @s remove {id}\n'
                }
            ]
        },

        # 保存新卡组
        "data/missile_royale/function/game/choose/save_cards.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'execute if items entity @s hotbar\.\* minecraft:<ID> run tag @s add <ID>',
                    "replacement": 'execute if items entity @s hotbar.* minecraft:{id} run tag @s add {id}',
                    "append_template": '\nexecute if items entity @s hotbar.* minecraft:{id} run tag @s add {id}',
                    "append_after": r'#保存玩家卡组'
                }
            ]
        },

        # 载入玩家保存的卡组
        "data/missile_royale/function/game/choose/previous_cards.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'give @s\[tag=<ID>\] <ID>',
                    "replacement": 'give @s[tag={id}] {id}',
                    "append_template": '\ngive @s[tag={id}] {id}',
                    "append_after": r'#每位玩家保留上一局游戏所用卡组'
                }
            ]
        },

        # 开场清除道具使用记录
        "data/missile_royale/function/game/tp.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'scoreboard players reset @a\[team=!\] use\.<ID>',
                    "replacement": 'scoreboard players reset @a[team=!] use.{id}',
                    "append_template": '\nscoreboard players reset @a[team=!] use.{id}',
                    "append_after": r'#清空道具使用记录'
                }
            ]
        },

        #发牌
        "data/missile_royale/function/game/deal/deal.mcfunction": {
            "type": "text",
            "rules": [
                {
                    "pattern": r'loot give @s\[team=!,tag=<ID>\].*',
                    "replacement": 'loot give @s[team=!,tag={id}] loot {{pools:[{{rolls:1,entries:[{{type:"minecraft:loot_table",value:"missile_wars:items/{id}",functions:[{{function:"reference",name:"missile_royale:cost_display"}}]}}]}}]}}',
                    "append_template": '\nloot give @s[team=!,tag={id}] loot {{pools:[{{rolls:1,entries:[{{type:"minecraft:loot_table",value:"missile_wars:items/{id}",functions:[{{function:"reference",name:"missile_royale:cost_display"}}]}}]}}]}}',
                    "append_after": r'#分发新卡'
                },
                {
                    "pattern": r'value:"missile_wars:items/trident",functions:\[(.*?)\]',
                    "replacement": 'value:"missile_wars:items/trident"'
                }
            ]
        },

        # Xcost.json 文件组配置
        "cost_group_files": {
            "type": "cost_group",
            "file_template": "data/missile_royale/tags/item/cost/{cost}cost.json",
            "min_cost": 1,
            "max_cost": 10
        },

        # 道具专属战利品表配置
        "item_loot_table": {
            "type": "item_loot_table",
            "directory": "data/missile_wars/loot_table/items",
            "template": {
                "pools": [
                    {
                        "entries": [
                            {
                                "type": "item",
                                "name": "PLACEHOLDER",  # 占位符，将在处理时替换
                            }
                        ],
                        "rolls": 1
                    }
                ],
                "functions": [
                    {
                        "function": "minecraft:reference",
                        "name": "missile_wars:item/green_items",
                        "conditions": [
                            {
                                "condition": "entity_properties",
                                "entity": "this",
                                "predicate": {
                                    "team": "green"
                                }
                            }
                        ]
                    },
                    {
                        "function": "minecraft:reference",
                        "name": "missile_wars:item/orange_items",
                        "conditions": [
                            {
                                "condition": "entity_properties",
                                "entity": "this",
                                "predicate": {
                                    "team": "orange"
                                }
                            }
                        ]
                    }
                ]
            },
            # 可选：验证已存在文件的内容
            "verify_content": True
        },

    }
    
    # 创建备份（可选）
    CREATE_BACKUPS = True
    
    # =============== 执行更新 ===============
    # 备份文件
    if CREATE_BACKUPS:
        for file_path in CONFIG:
            if not CONFIG[file_path].get('is_per_item_file', False):
                path = Path(file_path)
                if path.exists():
                    backup_file(path)
    
    # 处理专属JSON文件（需要特殊处理）
    per_item_configs = {}
    for file_path, file_config in list(CONFIG.items()):
        if file_config.get('is_per_item_file', False):
            per_item_configs[file_path] = file_config
            del CONFIG[file_path]  # 从主配置中移除
    
    # 执行主要更新
    update_datapack(EXCEL_PATH, CONFIG, column_mapping=COLUMN_MAPPING)
    
    # 处理每个道具的专属文件
    if per_item_configs:
        # 读取Excel数据
        df = pd.read_excel(EXCEL_PATH)
        items = {str(row['name']).lower(): row.to_dict() for _, row in df.iterrows()}
        
        for template_path, file_config in per_item_configs.items():
            for item_key, item_data in items.items():
                item_name = item_data['name']
                # 动态生成文件路径
                actual_path = template_path.format(name=item_name)
                # 创建单文件配置
                item_config = {actual_path: dict(file_config)}
                # 更新专属文件
                update_datapack(EXCEL_PATH, item_config)
    
    print("=" * 50)
    print("数据包更新完成！")
    print("=" * 50)