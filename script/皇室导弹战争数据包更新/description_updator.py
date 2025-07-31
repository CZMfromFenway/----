import pandas as pd
import json
import re
import os
import copy
from pathlib import Path
from functools import reduce

class DataPackUpdater:
    def __init__(self, excel_path, config):
        self.excel_path = excel_path
        self.config = config
        self.items = []
    
    def load_excel(self):
        """加载Excel数据，所有值作为字符串处理"""
        try:
            # 读取Excel，不转换数据类型
            df = pd.read_excel(self.excel_path, dtype=str, keep_default_na=False)
            print(f"✅ 成功读取Excel文件: {self.excel_path}")
            
            # 替换可能的NaN值为空字符串
            df = df.fillna('')
            
            # 转换为道具字典列表，所有值保持字符串格式
            self.items = df.to_dict('records')
            print(f"共读取 {len(self.items)} 个道具信息")
            
            # 打印前5个道具作为示例
            print("\n前5个道具示例:")
            for i, item in enumerate(self.items[:5], 1):
                print(f"  道具{i}: {item}")
            
            return True
        except Exception as e:
            print(f"❌ 读取Excel失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """执行更新"""
        if not self.load_excel():
            return False
        
        print("\n" + "=" * 50)
        print("开始更新数据包")
        print("=" * 50)
        
        success = True
        for file_config in self.config:
            try:
                result = self.process_file(file_config)
                if not result:
                    success = False
            except Exception as e:
                print(f"❌ 处理文件配置时出错: {e}")
                import traceback
                traceback.print_exc()
                success = False
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 数据包更新完成！")
        else:
            print("⚠️ 数据包更新过程中出现错误")
        print("=" * 50)
        
        return success
    
    def process_file(self, config):
        """处理单个文件配置"""
        file_path = Path(config['file_path'])
        print(f"\n处理文件: {file_path}")
        
        # 检查文件是否存在
        if not file_path.exists():
            if config.get('create_if_missing', False):
                print(f"创建新文件: {file_path}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
            else:
                print(f"❌ 文件不存在: {file_path}")
                return False
        
        # 根据文件类型处理
        file_type = config.get('type', 'text')
        if file_type == 'text':
            return self.process_text_file(file_path, config)
        elif file_type == 'json':
            return self.process_json_file(file_path, config)
        else:
            print(f"❌ 未知文件类型: {file_type}")
            return False
    
    def process_text_file(self, file_path, config):
        """处理文本文件"""
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return False
        
        modified = False
        new_content = content
        
        # 处理每个规则
        for rule in config['rules']:
            # 筛选符合条件的道具
            condition = rule.get('condition', {})
            filtered_items = self.filter_items(condition)
            
            if not filtered_items:
                print(f"  ⏩ 没有符合条件的道具，跳过规则: {rule.get('description', '')}")
                continue
            
            print(f"  应用规则: {rule.get('description', '')}")
            print(f"  符合条件道具数: {len(filtered_items)}")
            
            # 处理每个符合条件的道具
            for item in filtered_items:
                # 替换占位符
                search_pattern = self.replace_placeholders(rule['search_pattern'], item)
                replace_template = self.replace_placeholders(rule['replace_template'], item)
                
                # 尝试替换
                regex = re.compile(re.escape(search_pattern))
                if regex.search(new_content):
                    new_content = regex.sub(replace_template, new_content)
                    print(f"    ✅ 更新道具: {item.get('名称', '?')}")
                    modified = True
                else:
                    # 未找到，需要插入
                    insert_location = rule.get('insert_location', 'end')
                    insert_after = rule.get('insert_after')
                    insert_before = rule.get('insert_before')
                    
                    if insert_after:
                        # 在指定内容后插入
                        after_pattern = re.compile(re.escape(insert_after))
                        new_content = after_pattern.sub(
                            lambda m: m.group(0) + '\n' + replace_template, 
                            new_content
                        )
                        print(f"    ➕ 在 '{insert_after}' 后新增道具: {item.get('名称', '?')}")
                        modified = True
                    elif insert_before:
                        # 在指定内容前插入
                        before_pattern = re.compile(re.escape(insert_before))
                        new_content = before_pattern.sub(
                            lambda m: replace_template + '\n' + m.group(0), 
                            new_content
                        )
                        print(f"    ➕ 在 '{insert_before}' 前新增道具: {item.get('名称', '?')}")
                        modified = True
                    elif insert_location == 'start':
                        # 在文件开头插入
                        new_content = replace_template + '\n' + new_content
                        print(f"    ➕ 在文件开头新增道具: {item.get('名称', '?')}")
                        modified = True
                    else:
                        # 默认在文件末尾插入
                        new_content += '\n' + replace_template
                        print(f"    ➕ 在文件末尾新增道具: {item.get('名称', '?')}")
                        modified = True
        
        # 如果有修改则写回文件
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ 文件已更新: {file_path}")
                return True
            except Exception as e:
                print(f"❌ 写入文件失败: {e}")
                return False
        else:
            print(f"⏩ 未找到需要修改的内容: {file_path}")
            return True
    
    def process_json_file(self, file_path, config):
        """处理JSON文件（通用路径匹配）"""
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        
        modified = False
        
        # 处理每个规则
        for rule in config['rules']:
            # 筛选符合条件的道具
            condition = rule.get('condition', {})
            filtered_items = self.filter_items(condition)
            
            if not filtered_items:
                print(f"  ⏩ 没有符合条件的道具，跳过规则: {rule.get('description', '')}")
                continue
            
            print(f"  应用规则: {rule.get('description', '')}")
            print(f"  符合条件道具数: {len(filtered_items)}")
            
            # 新增：处理嵌套数组索引路径 (如 "pages.0")
            array_index = rule.get('array_index')
            if array_index is not None:
                # 获取父数组和索引
                parent_path, index_str = array_index.rsplit('.', 1)
                parent_array = self.get_by_path(data, parent_path)
                
                if not isinstance(parent_array, list):
                    print(f"  ❌ 父路径不是数组: {parent_path}")
                    continue
                
                try:
                    index = int(index_str)
                    if 0 <= index < len(parent_array):
                        target_array = parent_array[index]
                    else:
                        print(f"  ❌ 索引超出范围: {array_index}")
                        continue
                except ValueError:
                    print(f"  ❌ 无效的索引格式: {array_index}")
                    continue
            
            # 处理嵌套数组的特殊情况
            if rule.get('is_nested_array', False):
                if not isinstance(target_array, list):
                    print(f"  ❌ 目标路径不是数组: {target_path}")
                    continue
                
                modified_in_rule = False
                for item in filtered_items:
                    # 获取匹配值
                    match_value = self.replace_placeholders(rule['match_value'], item)
                    
                    # 在嵌套数组中查找匹配项
                    found = False
                    for array_element in target_array:
                        if not isinstance(array_element, list):
                            continue
                            
                        for i, element in enumerate(array_element):
                            if isinstance(element, dict):
                                # 使用指定路径获取值并匹配
                                current_value = self.get_by_path(element, rule['match_path'])
                                if current_value == match_value:
                                    # 更新匹配的元素
                                    update_template = {
                                        'search_key': rule['match_path'],
                                        'search_value': match_value,
                                        'update_template': rule['update_template']
                                    }
                                    self.update_object(array_element, update_template, item)
                                    print(f"    ✅ 更新道具: {item.get('名称', '?')} ({match_value})")
                                    modified = True
                                    modified_in_rule = True
                                    found = True
                                    break
                        if found:
                            break
                    # 未找到时的插入逻辑（如果需要）
                    if not found and rule.get('insert_on_missing', True):
                        # 创建新对象
                        new_obj = copy.deepcopy(rule['insert_template'])
                        
                        # 替换占位符
                        self.update_object(new_obj, rule['insert_template'], item)
                        
                        # 插入到嵌套数组中
                        insert_position = rule.get('insert_position', 'end')
                        if insert_position == 'start':
                            target_array.insert(0, new_obj)
                            print(f"    ➕ 在位置 0 添加道具: {item.get('名称', '?')} ({match_value})")
                        else:
                            target_array.append(new_obj)
                            print(f"    ➕ 在末尾添加道具: {item.get('名称', '?')} ({match_value})")
                        modified = True
                    
                    if modified_in_rule:
                        modified = True

            else:
                # 定位目标数组
                target_path = rule.get('target_path', '')
                target_array = self.get_by_path(data, target_path)
                
                if not isinstance(target_array, list):
                    print(f"  ❌ 目标路径不是数组: {target_path}")
                    continue
                
                # 处理每个符合条件的道具
                for item in filtered_items:
                    # 获取匹配值
                    match_value = self.replace_placeholders(rule['match_value'], item)
                    
                    # 在数组中查找道具
                    found = False
                    for i, obj in enumerate(target_array):
                        # 使用指定路径获取值并匹配
                        current_value = self.get_by_path(obj, rule['match_path'])
                        if current_value == match_value:
                            # 更新现有对象
                            self.update_object(obj, rule['update_template'], item)
                            print(f"    ✅ 更新道具: {item.get('name', '?')} ({match_value})")
                            modified = True
                            found = True
                            break
                    
                    if not found and rule.get('insert_on_missing', True):
                        # 创建新对象
                        new_obj = copy.deepcopy(rule['insert_template'])
                        
                        # 替换占位符
                        self.update_object(new_obj, rule['insert_template'], item)
                        
                        # 设置插入位置
                        insert_position = rule.get('insert_position', 'end')
                        insert_index = len(target_array)  # 默认插入末尾
                        
                        if insert_position == 'start':
                            insert_index = 0
                        elif isinstance(insert_position, int):
                            insert_index = min(max(insert_position, 0), len(target_array))
                        elif rule.get('insert_after') or rule.get('insert_before'):
                            # 查找参考对象
                            ref_value = rule.get('insert_after') or rule.get('insert_before')
                            ref_index = -1
                            for j, obj in enumerate(target_array):
                                ref_obj_value = self.get_by_path(obj, rule['match_path'])
                                if ref_obj_value == ref_value:
                                    ref_index = j
                                    break
                            
                            if ref_index >= 0:
                                if rule.get('insert_after'):
                                    insert_index = ref_index + 1
                                else:
                                    insert_index = ref_index
                        
                        # 插入新对象
                        target_array.insert(insert_index, new_obj)
                        print(f"    ➕ 在位置 {insert_index} 添加道具: {item.get('name', '?')} ({match_value})")
                        modified = True
        
        # 如果有修改则写回文件
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ JSON文件已更新: {file_path}")
                return True
            except Exception as e:
                print(f"❌ 写入JSON文件失败: {e}")
                return False
        else:
            print(f"⏩ JSON文件无需修改: {file_path}")
            return True
    
    def filter_items(self, condition):
        """根据条件筛选道具"""
        if not condition:
            return self.items
        
        filtered = []
        for item in self.items:
            match = True
            for key, value in condition.items():
                item_value = item.get(key)
                
                # 支持正则表达式条件
                if isinstance(value, re.Pattern):
                    if not value.match(str(item_value)):
                        match = False
                        break
                # 支持列表条件
                elif isinstance(value, list):
                    if item_value not in value:
                        match = False
                        break
                # 支持函数条件
                elif callable(value):
                    if not value(item_value):
                        match = False
                        break
                # 直接值匹配
                else:
                    if item_value != value:
                        match = False
                        break
            if match:
                filtered.append(item)
        return filtered
    
    def replace_placeholders(self, text, item):
        """替换文本中的占位符"""
        if not isinstance(text, str):
            return text
        
        # 支持嵌套占位符 {item.字段}
        result = text
        for key, value in item.items():
            # 所有值都作为字符串处理
            str_value = str(value) if not isinstance(value, str) else value
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, str_value)
        return result
    
    def get_by_path(self, data, path):
        """根据点分隔路径获取JSON中的值"""
        if not path:
            return data
        
        try:
            return reduce(lambda d, key: d[key] if isinstance(d, dict) else d[int(key)] if isinstance(d, list) and key.isdigit() else None, 
                         path.split('.'), 
                         data)
        except (KeyError, IndexError, TypeError):
            return None
    
    def update_object(self, obj, template, item):
        """使用模板递归更新对象，处理列表中多个位置"""
        if isinstance(obj, dict) and isinstance(template, dict):
            # 处理字典
            for key, template_value in template.items():
                if key in obj:
                    current_value = obj[key]
                    
                    # 递归处理嵌套结构
                    if isinstance(current_value, (dict, list)):
                        self.update_object(current_value, template_value, item)
                    # 更新字符串值
                    elif isinstance(current_value, str) and isinstance(template_value, str):
                        obj[key] = self.replace_placeholders(template_value, item)
                    # 其他类型保持不变
                else:
                    # 添加新字段
                    if isinstance(template_value, str):
                        obj[key] = self.replace_placeholders(template_value, item)
                    else:
                        obj[key] = copy.deepcopy(template_value)
        
        elif isinstance(obj, list) and isinstance(template, list):
            # 处理列表 - 更新所有匹配位置
            for i, item_value in enumerate(obj):
                # 确保索引在模板范围内
                if i < len(template):
                    template_value = template[i]
                    
                    # 递归处理嵌套结构
                    if isinstance(item_value, (dict, list)):
                        self.update_object(item_value, template_value, item)
                    # 更新字符串值
                    elif isinstance(item_value, str) and isinstance(template_value, str):
                        obj[i] = self.replace_placeholders(template_value, item)
                    # 其他类型保持不变
            
            # 添加额外的元素（如果模板更长）
            if len(template) > len(obj):
                for i in range(len(obj), len(template)):
                    template_value = template[i]
                    if isinstance(template_value, str):
                        obj.append(self.replace_placeholders(template_value, item))
                    else:
                        obj.append(copy.deepcopy(template_value))
        
        elif isinstance(obj, str) and isinstance(template, str):
            # 直接替换字符串
            return self.replace_placeholders(template, item)

# 示例配置
CONFIG = [
    # data/missile_royale/item_modifier/cards.json
    {
        "file_path": "data/missile_royale/item_modifier/cards.json",
        "type": "json",
        "rules": [
            {
                "description": "更新选卡名称和描述",
                "condition": {},  # 所有道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {
                            "name": [{"text": "{名称}","color":"{稀有度}"}]  # 只更新文本
                        },
                        {
                            "lore": [{"text": "{选卡介绍}"}],
                            "mode": "replace_section",  # 替换所有现有描述
                            "offset": 1
                        }
                    ]
                },
                "insert_template": {
                    "function": "filtered",
                    "item_filter": {
                        "items": "{物品代号}"  # 道具ID占位符
                    },
                    "modifier": [
                        {
                            "function": "minecraft:set_name",
                            "name": [
                                {
                                    "text": "{名称}",
                                    "italic": False,
                                    "color": "{稀有度}"
                                }
                            ]
                        },
                        {
                            "function": "minecraft:set_lore",
                            "mode": "replace_section",
                            "offset": 1,  # 从第二行开始替换
                            "lore": [
                                {
                                    "text": "{选卡介绍}",
                                    "color": "white"
                                }
                            ]
                        }
                    ]
                },
                "insert_on_missing": True,
                "insert_position": "end"  # 插入到数组末尾
            }
        ]
    },
    
    # data/missile_wars/item_modifier/item/green_items.json
    {
        "file_path": "data/missile_wars/item_modifier/item/green_items.json",
        "type": "json",
        "rules": [
            {
                "description": "更新绿色导弹名称和描述",
                "condition": {"类型": "进攻"},  # 只处理飞行器道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {
                            "name": [{"text": "部署绿队{名称}", "color": "green", "italic": False}]
                        },
                        {
                            "lore": [
                                {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ],
                            "mode": "replace_all"
                        }
                    ]
                },
                "insert_on_missing": True,
                "insert_template": {
                    "function": "minecraft:filtered",
                    "item_filter": {
                    "items": "{物品代号}"  # 道具ID占位符
                    },
                    "modifier": [
                    {
                        "function": "set_name",
                        "name": [{"text": "部署绿队{名称}", "color": "green", "italic": False}]
                    },
                    {
                        "function": "set_lore",
                        "mode": "replace_all",
                        "lore": [
                        {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                        {"text": "{卡牌介绍}", "color": "white", "italic": False}
                        ]
                    },
                    {
                        "function": "set_components",
                        "components": {
                        "can_place_on": {
                            "predicates": [
                            {
                                "blocks": "#missile_wars:game_block"
                            }
                            ],
                            "show_in_tooltip": False
                        }
                        }
                    }
                    ]
                },
            },
            {
                "description": "更新绿色防御性道具的名称和描述",
                "condition": {"类型": "防御"},  # 只处理防御性道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {
                            "name": [{"text": "{名称}", "color": "light_purple", "italic": False}]
                        },
                        {
                            "lore": [
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ],
                            "mode": "replace_all"
                        }
                    ]
                },
                "insert_on_missing": True,
                "insert_template": {
                    "function": "minecraft:filtered",
                    "item_filter": {
                        "items": "{物品代号}"  # 道具ID占位符
                    },
                    "modifier": [
                        {
                            "function": "set_name",
                            "name": [{"text": "{名称}", "color": "light_purple", "italic": False}]
                        },
                        {
                            "function": "set_lore",
                            "mode": "replace_all",
                            "lore": [
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ]
                        }
                    ]
                }
            },
            {
                "description": "特殊处理火球道具",
                "condition": {"物品代号": "blaze_spawn_egg"},  # 只处理火球道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                            {
                                "name": [{"text": "部署火球", "color": "light_purple", "italic": False}]
                            },
                            {
                                "lore": [
                                    {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                                    {"text": "{卡牌介绍}", "color": "white", "italic": False}
                                ],
                                "mode": "replace_all"
                            },
                            {
                                "function": "set_components",
                                "components": {
                                    "can_place_on": {
                                        "predicates": [
                                            {
                                                "blocks": "#missile_wars:game_block"
                                            }
                                        ],
                                        "show_in_tooltip": False
                                }
                                }
                            }
                    ]
                },
                "insert_on_missing": False  # 不插入新道具
            },
            {
                "description": "特殊处理三叉戟",
                "condition": {"物品代号": "trident"},  # 只处理三叉戟道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {},
                        {},
                        {
                            "function": "minecraft:set_components",
                            "components": {
                                "enchantments": {
                                    "missile_wars:platform_trident": 1
                                }
                            }
                        }
                    ]
                },
                "insert_on_missing": False  # 不插入新道具
            }
        ]
    },

    # data/missile_wars/item_modifier/item/orange_items.json
    {
        "file_path": "data/missile_wars/item_modifier/item/orange_items.json",
        "type": "json",
        "rules": [
            {
                "description": "更新黄色导弹名称和描述",
                "condition": {"类型": "进攻"},  # 只处理飞行器道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {
                            "name": [{"text": "部署黄队{名称}", "color": "gold", "italic": False}]
                        },
                        {
                            "lore": [
                                {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ],
                            "mode": "replace_all"
                        }
                    ]
                },
                "insert_on_missing": True,
                "insert_template": {
                    "function": "minecraft:filtered",
                    "item_filter": {
                    "items": "{物品代号}"  # 道具ID占位符
                    },
                    "modifier": [
                    {
                        "function": "set_name",
                        "name": [{"text": "部署黄队{名称}", "color": "gold", "italic": False}]
                    },
                    {
                        "function": "set_lore",
                        "mode": "replace_all",
                        "lore": [
                        {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                        {"text": "{卡牌介绍}", "color": "white", "italic": False}
                        ]
                    },
                    {
                        "function": "set_components",
                        "components": {
                        "can_place_on": {
                            "predicates": [
                            {
                                "blocks": "#missile_wars:game_block"
                            }
                            ],
                            "show_in_tooltip": False
                        }
                        }
                    }
                    ]
                },
            },
            {
                "description": "更新黄色防御性道具的名称和描述",
                "condition": {"类型": "防御"},  # 只处理防御性道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {
                            "name": [{"text": "{名称}", "color": "light_purple", "italic": False}]
                        },
                        {
                            "lore": [
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ],
                            "mode": "replace_all"
                        }
                    ]
                },
                "insert_on_missing": True,
                "insert_template": {
                    "function": "minecraft:filtered",
                    "item_filter": {
                        "items": "{物品代号}"  # 道具ID占位符
                    },
                    "modifier": [
                        {
                            "function": "set_name",
                            "name": [{"text": "{名称}", "color": "light_purple", "italic": False}]
                        },
                        {
                            "function": "set_lore",
                            "mode": "replace_all",
                            "lore": [
                                {"text": "{卡牌介绍}", "color": "white", "italic": False}
                            ]
                        }
                    ]
                }
            },
            {
                "description": "特殊处理火球道具",
                "condition": {"物品代号": "blaze_spawn_egg"},  # 只处理火球道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                            {
                                "name": [{"text": "部署火球", "color": "light_purple", "italic": False}]
                            },
                            {
                                "lore": [
                                    {"text": "右键地面以在前方部署", "color": "gray", "italic": False},
                                    {"text": "{卡牌介绍}", "color": "white", "italic": False}
                                ],
                                "mode": "replace_all"
                            },
                            {
                                "function": "set_components",
                                "components": {
                                    "can_place_on": {
                                        "predicates": [
                                            {
                                                "blocks": "#missile_wars:game_block"
                                            }
                                        ],
                                        "show_in_tooltip": False
                                }
                                }
                            }
                    ]
                },
                "insert_on_missing": False  # 不插入新道具
            },
            {
                "description": "特殊处理三叉戟",
                "condition": {"物品代号": "trident"},  # 只处理三叉戟道具
                "target_path": "",  # 根数组
                "match_path": "item_filter.items",  # 匹配路径
                "match_value": "{物品代号}",  # 匹配值
                "update_template": {
                    "modifier": [
                        {},
                        {},
                        {
                            "function": "minecraft:set_components",
                            "components": {
                                "enchantments": {
                                    "missile_wars:platform_trident": 1
                                }
                            }
                        }
                    ]
                },
                "insert_on_missing": False  # 不插入新道具
            }
        ]
    },
]

if __name__ == "__main__":
    # 初始化更新器
    updater = DataPackUpdater(
        excel_path="../../doc/道具信息.xlsx",
        config=CONFIG
    )
    
    # 执行更新
    updater.run()