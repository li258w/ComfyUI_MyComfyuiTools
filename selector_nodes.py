import os
import json
import random 
import folder_paths

# --- 基础类：所有选择器节点的基类 ---
class BaseJsonSelector:
    # 子类必须覆盖这两个属性
    TARGET_JSON_FILE = "" 
    NODE_NAME = ""

    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        default_json_path = os.path.join(current_dir, s.TARGET_JSON_FILE)
        
        options = ["无 (None)", "随机 (Random)", "自定义 (Custom)"]
        
        if os.path.exists(default_json_path):
            try:
                with open(default_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, content in data.items():
                        if isinstance(content, dict) and "描述" in content:
                            options.append(content["描述"])
            except Exception as e:
                print(f"[Node: {s.NODE_NAME}] Error loading JSON file '{s.TARGET_JSON_FILE}': {e}")
        
        return {
            "required": {
                "prefix": ("STRING", {"multiline": False, "default": "", "placeholder": "前置文本 (例如: style: )"}),
                "style_select": (options,),
                # 【修改点 1】新增“描述+关键词”选项
                "output_mode": (["Key", "关键词", "描述+关键词"], {"default": "Key"}),
                
                "random_filter": ("STRING", {"multiline": False, "default": "", "placeholder": "随机模式筛选词 (逗号分隔, 例如: 裙子, 红色)"}),
                "custom_text": ("STRING", {"multiline": False, "default": "", "placeholder": "当上方选择'自定义'时，使用此文本"}),
                "seed": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 0xffffffffffffffff, 
                    "control_after_generate": True
                }),
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "process_text"
    CATEGORY = "MyCustomNodes"

    def check_and_add_comma(self, text):
        if not text:
            return ""
        
        ending_punctuation = ['.', ',', ';', '!', '?', ':', '。', '，', '；', '！', '？', '：']
        stripped_text = text.strip()
        
        if stripped_text and stripped_text[-1] not in ending_punctuation:
            return f"{stripped_text}, "
        
        return stripped_text

    def process_text(self, prefix, style_select, output_mode, random_filter, custom_text, seed): 
        target_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.TARGET_JSON_FILE)

        selected_content = ""
        data = {}

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return (f"Error loading JSON file at {self.TARGET_JSON_FILE}: {e}",)

        selected_key = ""
        
        # --- 逻辑分支 (省略) ---
        
        # 1. 选择 "无"
        if style_select == "无 (None)":
            final_output = self.check_and_add_comma(prefix)
            return (final_output,)

        # 2. 选择 "自定义"
        elif style_select == "自定义 (Custom)":
            selected_content = custom_text
            
        # 3. 选择 "随机" (包含筛选逻辑)
        elif style_select == "随机 (Random)":
            if not data:
                return (f"Error: JSON data in {self.TARGET_JSON_FILE} is empty.",)
            
            filter_terms = [t.strip() for t in random_filter.split(",") if t.strip()] 
            
            if not filter_terms:
                candidates = list(data.keys())
            else:
                candidates = []
                for key, content in data.items():
                    description = content.get("描述", "")
                    for term in filter_terms:
                        if term in description:
                            candidates.append(key)
                            break 
            
            if candidates:
                selected_key = random.choice(candidates)
            else:
                print(f"[{self.NODE_NAME}] Warning: No items matched the filter keywords: {random_filter}")
                final_output = self.check_and_add_comma(prefix)
                return (final_output,)
        
        # 4. 选择 具体选项
        else:
            for key, content in data.items():
                if content.get("描述") == style_select:
                    selected_key = key
                    break
        
        # --- 内容提取 【修改点 2】新增描述+关键词逻辑 ---
        if selected_key:
            item_data = data.get(selected_key, {})
            
            if output_mode == "Key":
                selected_content = selected_key
            elif output_mode == "关键词": 
                selected_content = item_data.get("关键词", selected_key)
            elif output_mode == "描述+关键词":
                description = item_data.get("描述", "")
                keyword = item_data.get("关键词", "")
                
                # 按照 "描述(关键词)" 格式输出
                if description and keyword:
                    selected_content = f"{description}({keyword})"
                elif description:
                    selected_content = description
                elif keyword:
                    selected_content = keyword
                else:
                    selected_content = selected_key # 最终的fallback，输出Key
        
        # --- 拼接输出 (保持不变) ---
        clean_prefix = prefix.strip()
        
        if clean_prefix and selected_content:
            result = f"{clean_prefix} {selected_content}"
        elif selected_content:
            result = selected_content
        else:
            result = clean_prefix

        final_output = self.check_and_add_comma(result)

        return (final_output,)

# --- 子类列表 (JSON Selector Nodes) ---

class StyleSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/styles.json"
    NODE_NAME = "Style Selector"

# ... (其余的 Selector 节点保持不变) ...

class ClothingSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/clothing.json"
    NODE_NAME = "Clothing Selector"

class PoseSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/pose.json"
    NODE_NAME = "Pose Selector"

class HairstylesSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/hairstyles.json"
    NODE_NAME = "Hairstyles Selector"

class EyeColorsSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/eye_colors.json"
    NODE_NAME = "Eye Colors Selector"

class BackgroundSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/background.json"
    NODE_NAME = "Background Selector"

class BodyTypesSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/body_types.json"
    NODE_NAME = "Body Types Selector"

class PlaceSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/place.json"
    NODE_NAME = "Place Selector"

class HairColorSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/hair_color.json"
    NODE_NAME = "Hair Color Selector"

class PhotoTypeSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/photo_type.json"
    NODE_NAME = "Photo Type Selector"

class CompositionSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/composition.json"
    NODE_NAME = "Composition Selector"


# --- 工具节点：多字符串联结 ---
class StringJoiner:
    # 保持 StringJoiner 稳定不变
    
    @classmethod
    def INPUT_TYPES(s):
        separator_options = [
            ", (逗号+空格)", 
            ". (句号+空格)", 
            "| (竖线+空格)", 
            "\\n (回车/换行)",
            "Custom (自定义)"
        ]
        
        return {
            "required": {
                "string_1": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "separator_select": (separator_options, {"default": ", (逗号+空格)"}),
            },
            "optional": {
                "string_2": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_3": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_4": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_5": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_6": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_7": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "string_8": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                
                "custom_separator": ("STRING", {"multiline": False, "default": "", "placeholder": "仅在选择Custom时生效"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("concatenated_text",)
    FUNCTION = "join_strings"
    CATEGORY = "MyCustomNodes/Utils"

    def join_strings(self, string_1, string_2="", string_3="", string_4="", string_5="", string_6="", string_7="", string_8="", separator_select="", custom_separator=""):
        # 1. 确定最终联结符
        separator = ""
        if separator_select == ", (逗号+空格)":
            separator = ", "
        elif separator_select == ". (句号+空格)":
            separator = ". "
        elif separator_select == "| (竖线+空格)":
            separator = " | "
        elif separator_select == "\\n (回车/换行)":
            separator = "\n"
        elif separator_select == "Custom (自定义)":
            separator = custom_separator.replace("\\n", "\n") 

        # 2. 收集所有输入
        input_strings = [
            string_1, string_2, string_3, string_4, string_5, 
            string_6, string_7, string_8
        ]

        # 3. 过滤掉 None/空值
        cleaned_list = []
        for s in input_strings:
            if s is None:
                continue 
            
            stripped_s = s.strip()
            
            if stripped_s:
                cleaned_list.append(stripped_s)
        
        # 4. 联结字符串
        result = separator.join(cleaned_list)
        
        return (result,)