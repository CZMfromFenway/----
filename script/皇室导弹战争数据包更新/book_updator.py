import pandas as pd
import json
import os
import copy
from pathlib import Path
import re

class BookModifierUpdater:
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
        print("开始更新书本修饰器数据")
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
            print("✅ 书本修饰器更新完成！")
        else:
            print("⚠️ 更新过程中出现错误")
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
                # 创建包含基本结构的空书本文件
                base_structure = {
                    "function": "set_written_book_pages",
                    "mode": "append",
                    "pages": []
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(base_structure, f, indent=2, ensure_ascii=False)
            else:
                print(f"❌ 文件不存在: {file_path}")
                return False
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        
        # 确保文件包含pages数组
        if 'pages' not in data or not isinstance(data['pages'], list):
            print(f"❌ 文件缺少有效的pages数组: {file_path}")
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
            
            # 处理每个符合条件的道具
            for item in filtered_items:
                # 获取匹配值（名称）
                match_value = self.replace_placeholders(rule['match_value'], item)
                found = False
                
                # 遍历所有页面
                for page_index, page in enumerate(data['pages']):
                    if not isinstance(page, list):
                        continue
                    
                    # 在页面中查找道具代号
                    code_index = -1
                    for i, element in enumerate(page):
                        if isinstance(element, dict) and element.get('text') == match_value:
                            code_index = i
                            break
                    
                    if code_index == -1:
                        continue
                    
                    # 找到道具代号位置，更新整个页面
                    print(f"    🔍 在页面 {page_index} 找到道具: {match_value}")
                    
                    # 生成新页面内容
                    new_page = []
                    for element in rule['page_template']:
                        if isinstance(element, str):
                            # 处理字符串元素
                            new_page.append(self.replace_placeholders(element, item))
                        elif isinstance(element, dict):
                            # 处理文本对象元素
                            new_element = copy.deepcopy(element)
                            self.update_text_object(new_element, item)
                            new_page.append(new_element)
                        else:
                            # 其他类型直接复制
                            new_page.append(copy.deepcopy(element))
                    
                    # 替换原页面
                    data['pages'][page_index] = new_page
                    print(f"    ✅ 更新页面内容")
                    modified = True
                    found = True
                    break
                
                # 未找到时的插入逻辑
                if not found and rule.get('insert_on_missing', True):
                    # 生成新页面
                    new_page = []
                    for element in rule['page_template']:
                        if isinstance(element, str):
                            new_page.append(self.replace_placeholders(element, item))
                        elif isinstance(element, dict):
                            new_element = copy.deepcopy(element)
                            self.update_text_object(new_element, item)
                            new_page.append(new_element)
                        else:
                            new_page.append(copy.deepcopy(element))
                    
                    # 设置插入位置
                    insert_position = rule.get('insert_position', 'end')
                    insert_index = len(data['pages'])  # 默认插入末尾
                    
                    if insert_position == 'start':
                        insert_index = 0
                    elif isinstance(insert_position, int):
                        insert_index = min(max(insert_position, 0), len(data['pages']))
                    elif rule.get('insert_after') or rule.get('insert_before'):
                        # 查找参考道具页面
                        ref_value = rule.get('insert_after') or rule.get('insert_before')
                        ref_index = -1
                        for j, page in enumerate(data['pages']):
                            if not isinstance(page, list):
                                continue
                            for element in page:
                                if isinstance(element, dict) and element.get('text') == ref_value:
                                    ref_index = j
                                    break
                            if ref_index >= 0:
                                break
                        
                        if ref_index >= 0:
                            if rule.get('insert_after'):
                                insert_index = ref_index + 1
                            else:
                                insert_index = ref_index
                    
                    # 插入新页面
                    data['pages'].insert(insert_index, new_page)
                    print(f"    ➕ 在位置 {insert_index} 添加新页面: {item.get('名称', '?')}")
                    modified = True
        
        # 如果有修改则写回文件
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ 书本修饰器文件已更新: {file_path}")
                return True
            except Exception as e:
                print(f"❌ 写入文件失败: {e}")
                return False
        else:
            print(f"⏩ 文件无需修改: {file_path}")
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
    
    def update_text_object(self, obj, item):
        """更新文本对象中的占位符"""
        if not isinstance(obj, dict):
            return
        
        for key, value in obj.items():
            if isinstance(value, str):
                # 替换字符串值中的占位符
                obj[key] = self.replace_placeholders(value, item)
            elif isinstance(value, dict):
                # 递归处理嵌套对象
                self.update_text_object(value, item)
            elif isinstance(value, list):
                # 处理列表中的每个元素
                for i, element in enumerate(value):
                    if isinstance(element, str):
                        value[i] = self.replace_placeholders(element, item)
                    elif isinstance(element, dict):
                        self.update_text_object(element, item)

# 书本修饰器专用配置
BOOK_MODIFIER_CONFIG = [
    # data/missile_wars/item_modifier/text/help_missiles.json
    {
        "file_path": "data/missile_wars/item_modifier/text/help_missiles.json",
        "create_if_missing": True,
        "rules": [
            {
                "description": "更新帮助中导弹的名称和描述",
                "condition": {"类型": "进攻"},
                "match_value": "{名称}",
                "page_template": [
                    "",
                    {"text": "{名称}", "color": "{稀有度}"},
                    {"text": "\n", "color": "black"},
                    {"text": "{代号}", "color": "{稀有度}"},
                    {"text": "\n", "color": "black"},
                    {"text": "编号：", "color": "gray"},
                    {"text": "{编号}", "color": "gray"},
                    "\n",
                    {"text": "怪物蛋：", "color": "black"},
                    {"text": "{怪物蛋/物品}", "color": "dark_green"},
                    {"text": "\n长：", "color": "black"},
                    {"text": "{长}", "color": "dark_green"},
                    {"text": "  宽：", "color": "black"},
                    {"text": "{宽}", "color": "dark_green"},
                    {"text": "  高：", "color": "black"},
                    {"text": "{高}", "color": "dark_green"},
                    {"text": "\n移速：", "color": "black"},
                    {"text": "{移速（m/s）} m/s", "color": "dark_green"},
                    {"text": "\n弹药量：", "color": "black"},
                    {"text": "{弹药量（TNT）}", "color": "dark_green"},
                    {"text": "+", "color": "black"},
                    {"text": "{弹药量（TNT矿车）}", "color": "dark_red"},
                    {"text": "\n皇室模式费用：", "color": "black"},
                    {"text": "{费用}", "color": "dark_green"},
                    {"text": "\n非皇室模式合成配方：\n", "color": "black"},
                    {"text": "{配方}", "color": "dark_purple"},
                    "\n\n",
                    {"text": "{详细介绍}", "color": "black"}
                ],
                "insert_on_missing": True,
                "insert_position": "end"
            }
        ]
    },
    # data/missile_wars/item_modifier/text/help_defensive_items.json
    {
        "file_path": "data/missile_wars/item_modifier/text/help_defensive_items.json",
        "create_if_missing": True,
        "rules": [
            {
                "description": "更新帮助中防御性道具的名称和描述",
                "condition": {"类型": "防御"},
                "match_value": "{名称}",
                "page_template": [
                    "",
                    {"text": "{名称}", "color": "{稀有度}"},
                    {"text": "\n", "color": "black"},
                    {"text": "\n", "color": "black"},
                    {"text": "编号：", "color": "gray"},
                    {"text": "{编号}", "color": "gray"},
                    "\n",
                    {"text": "怪物蛋/物品：", "color": "black"},
                    {"text": "{怪物蛋/物品}", "color": "dark_green"},
                    {"text": "\n皇室模式费用：", "color": "black"},
                    {"text": "{费用}", "color": "dark_green"},
                    {"text": "\n非皇室模式合成配方：\n", "color": "black"},
                    {"text": "{配方}", "color": "dark_purple"},
                    "\n\n",
                    {"text": "{详细介绍}", "color": "black"}
                ],
                "insert_on_missing": True,
                "insert_position": "end"
            }
        ]
    }
]

if __name__ == "__main__":
    # 初始化书本修饰器更新器
    updater = BookModifierUpdater(
        excel_path= "../../doc/道具信息.xlsx",
        config=BOOK_MODIFIER_CONFIG
    )
    
    # 执行更新
    updater.run()