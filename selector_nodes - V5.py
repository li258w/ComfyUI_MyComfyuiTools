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
        
        options = ["无 (None)", "随机 (Random)"]
        
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
                "output_mode": (["Key", "关键词"], {"default": "Key"}),
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
    CATEGORY = "MyCustomNodes" # 统一的分类

    def check_and_add_comma(self, text):
        if not text:
            return ""
        
        ending_punctuation = ['.', ',', ';', '!', '?', ':', '。', '，', '；', '！', '？', '：']
        stripped_text = text.strip()
        
        if stripped_text and stripped_text[-1] not in ending_punctuation:
            return f"{stripped_text}, "
        
        return stripped_text

    def process_text(self, prefix, style_select, output_mode, seed): 
        target_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.TARGET_JSON_FILE)

        selected_content = ""
        data = {}

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return (f"Error loading JSON file at {self.TARGET_JSON_FILE}: {e}",)

        # ... (随机/选择逻辑与 V5 相同) ...
        selected_key = ""
        
        if style_select == "无 (None)":
            final_output = self.check_and_add_comma(prefix)
            return (final_output,)

        elif style_select == "随机 (Random)":
            if data:
                selected_key = random.choice(list(data.keys()))
            else:
                return (f"Error: JSON data in {self.TARGET_JSON_FILE} is empty for random selection.",)
        
        else:
            for key, content in data.items():
                if content.get("描述") == style_select:
                    selected_key = key
                    break
        
        if selected_key:
            if output_mode == "Key":
                selected_content = selected_key
            else: 
                selected_content = data.get(selected_key, {}).get("关键词", selected_key)
        
        clean_prefix = prefix.strip()
        
        if clean_prefix and selected_content:
            result = f"{clean_prefix} {selected_content}"
        elif selected_content:
            result = selected_content
        else:
            result = clean_prefix

        final_output = self.check_and_add_comma(result)

        return (final_output,)

# --- 现有子类 1: 风格选择器 (使用 styles.json) ---
class StyleSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/styles.json"
    NODE_NAME = "Style Selector"

# --- 现有子类 2: 服装选择器 (使用 clothing.json) ---
class ClothingSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/clothing.json"
    NODE_NAME = "Clothing Selector"

# --- 现有子类 3: 姿势选择器 (使用 pose.json) ---
class PoseSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/pose.json"
    NODE_NAME = "Pose Selector"

# --- 新增子类 4: 发型选择器 (使用 hairstyles.json) ---
class HairstylesSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/hairstyles.json"
    NODE_NAME = "Hairstyles Selector"

# --- 新增子类 5: 眼睛颜色选择器 (使用 eye_colors.json) ---
class EyeColorsSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/eye_colors.json"
    NODE_NAME = "Eye Colors Selector"

# --- 新增子类 6: 背景选择器 (使用 background.json) ---
class BackgroundSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/background.json"
    NODE_NAME = "Background Selector"

# --- 新增子类 7: 体型选择器 (使用 body_types.json) ---
class BodyTypesSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/body_types.json"
    NODE_NAME = "Body Types Selector"

# --- 新增子类 8: 地点选择器 (使用 place.json) ---
class PlaceSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/place.json"
    NODE_NAME = "Place Selector"

# --- 新增子类 9: 头发颜色选择器 (使用 hair_color.json) ---
class HairColorSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/hair_color.json"
    NODE_NAME = "Hair Color Selector"

# --- 新增子类 10: 照片类型选择器 (使用 photo_type.json) ---
class PhotoTypeSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/photo_type.json"
    NODE_NAME = "Photo Type Selector"
    
# --- 新增子类 11: 构图选择器 (使用 composition.json) ---
class CompositionSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/composition.json"
    NODE_NAME = "Composition Selector"