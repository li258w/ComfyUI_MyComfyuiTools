import os
import json
import random 

# random_filter 输入框的提示文案（多处复用，避免不一致）
FILTER_PLACEHOLDER = "随机筛选词 (逗号分隔, 匹配描述/关键词/分类, 例如: 裙子, film)"

# --- 基础类：所有选择器节点的基类 ---
class BaseJsonSelector:
    # 子类必须覆盖这两个属性
    TARGET_JSON_FILE = "" 
    NODE_NAME = ""

    # JSON数据缓存，避免频繁的文件IO
    # 结构: {file_path: {"signature": (mtime, size), "data": {...}}}
    # 缓存以"修改时间 + 文件大小"作为指纹，文件一改就自动重载，无需重启 ComfyUI
    _JSON_CACHE = {}
    # 缓存指纹检查的开销极小（一次 os.stat），仅在命中缓存时才付出
    _JSON_CACHE_ENABLED = True

    @classmethod
    def _file_signature(cls, file_path):
        """生成文件指纹（mtime + size）。文件不存在时返回 None。"""
        try:
            st = os.stat(file_path)
            return (st.st_mtime, st.st_size)
        except OSError:
            return None

    @classmethod
    def _json_file_path(cls):
        """本节点对应的 JSON 文件绝对路径。"""
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.TARGET_JSON_FILE)

    @classmethod
    def get_desc_index(cls, file_path):
        """返回 {描述: Key} 索引，避免每次输出都全表扫描。

        重复描述时保留"首次出现"的 Key，与原先线性查找（命中即 break）的行为一致。
        索引存在 JSON 缓存条目里，随文件指纹变化自动重建，无需额外维护。
        """
        data = cls.get_json_data(file_path)
        if not data:
            return {}

        cached = cls._JSON_CACHE.get(file_path) if cls._JSON_CACHE_ENABLED else None
        if cached is not None and cached.get("data") is data and "desc_index" in cached:
            return cached["desc_index"]

        index = {}
        for key, content in data.items():
            if isinstance(content, dict):
                desc = content.get("描述")
                if isinstance(desc, str) and desc not in index:
                    index[desc] = key

        if cached is not None:
            cached["desc_index"] = index
        return index

    @classmethod
    def _collect_search_text(cls, key, content):
        """收集一个条目中可被 random_filter 命中的文本。

        范围：JSON 的 key + 描述 + 关键词 + 分类标签。
        把 key 也纳入搜索很关键——本插件的数据约定是「英文写在 key 上、
        关键词字段写中文」，不搜 key 的话英文筛选几乎筛不到东西。

        之前只匹配"描述"，导致输入英文关键词或分类名筛选不到任何结果。
        """
        parts = []
        if isinstance(key, str):
            parts.append(key)
        if isinstance(content, dict):
            for field in ("描述", "关键词"):
                text = cls._as_text(content.get(field))
                if text:
                    parts.append(text)
            cats = content.get("分类")
            if isinstance(cats, (list, tuple)):
                parts.extend(c for c in cats if isinstance(c, str))
        return parts

    @staticmethod
    def _as_text(value):
        """把字段值规整为字符串。

        兼容个别条目把 "关键词" 写成数组的情况（json/styles.json 的
        ForestCinematicSoftLight 就是这样）——原先会把 Python 列表直接送进
        check_and_add_comma，导致节点抛 AttributeError 崩溃。
        """
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return ", ".join(v.strip() for v in value if isinstance(v, str) and v.strip())
        return ""

    @classmethod
    def _match_filter(cls, key, content, lower_terms):
        """判断条目是否命中筛选词（任一命中即可，OR 语义；英文大小写不敏感）。"""
        for text in cls._collect_search_text(key, content):
            lowered = text.lower()
            for term in lower_terms:
                if term in lowered:
                    return True
        return False

    @classmethod
    def get_json_data(cls, file_path):
        """获取JSON数据，使用缓存避免重复读取文件

        缓存会自动失效：每次调用都会比对文件指纹（mtime + size），
        一旦外部修改了 JSON 文件，下一次访问就会重新加载，
        因此"改完 JSON 需要重启 ComfyUI"的问题不再存在。
        """
        if not file_path:
            return None

        if not cls._JSON_CACHE_ENABLED:
            signature = cls._file_signature(file_path)
            cached = None
        else:
            signature = cls._file_signature(file_path)
            cached = cls._JSON_CACHE.get(file_path)

        # 文件已被删除/改名：丢弃可能残留的旧缓存
        if signature is None:
            cls._JSON_CACHE.pop(file_path, None)
            return None

        if cached is not None and cached.get("signature") == signature:
            return cached.get("data")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[Node: {cls.NODE_NAME}] Error loading JSON file '{file_path}': {e}")
            return None

        if cls._JSON_CACHE_ENABLED:
            cls._JSON_CACHE[file_path] = {"signature": signature, "data": data}
        return data

    @classmethod
    def clear_json_cache(cls, file_path=None):
        """清除JSON缓存

        Args:
            file_path: 要清除的特定文件路径，如果为None则清除所有缓存
        """
        if file_path:
            if file_path in cls._JSON_CACHE:
                del cls._JSON_CACHE[file_path]
                print(f"[Node: {cls.NODE_NAME}] Cleared cache for: {file_path}")
        else:
            cls._JSON_CACHE.clear()
            print(f"[Node: {cls.NODE_NAME}] Cleared all JSON cache")
    
    @classmethod
    def INPUT_TYPES(s):
        default_json_path = s._json_file_path()

        options = ["无 (None)", "随机 (Random)", "自定义 (Custom)"]

        # 使用缓存获取JSON数据
        data = s.get_json_data(default_json_path)

        if data:
            for key, content in data.items():
                if isinstance(content, dict) and "描述" in content:
                    options.append(content["描述"])

        return {
            "required": {
                "prefix": ("STRING", {"multiline": False, "default": "", "placeholder": "前置文本 (例如: style: )"}),
                "style_select": (options,),
                # 【修改点 1】新增“描述+关键词”选项
                "output_mode": (["Key", "关键词", "描述+关键词"], {"default": "Key"}),

                "random_filter": ("STRING", {"multiline": False, "default": "", "placeholder": FILTER_PLACEHOLDER}),
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
    CATEGORY = "MyCustomNodes/prompt"

    def check_and_add_comma(self, text):
        if not text:
            return ""

        # 兜底：字段值可能是数组（见 _as_text 说明），统一规整为字符串再处理
        if not isinstance(text, str):
            text = self._as_text(text)
            if not text:
                return ""

        # 使用字符串存储标点符号，提高in操作的效率
        ending_punctuation = ".,;!?:。，；！？："
        stripped_text = text.strip()

        if stripped_text and stripped_text[-1] not in ending_punctuation:
            return f"{stripped_text}, "

        return stripped_text

    def process_text(self, prefix, style_select, output_mode, random_filter, custom_text, seed):
        # 跳过分类标题行（以"--- "开头）
        if style_select.startswith("--- "):
            # 当作"无"处理
            final_output = self.check_and_add_comma(prefix)
            return (final_output,)

        target_path = self._json_file_path()

        selected_content = ""
        data = {}

        # 使用缓存获取JSON数据
        data = self.get_json_data(target_path)
        if data is None:
            return (f"Error loading JSON file at {self.TARGET_JSON_FILE}: File not found or invalid",)

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
                # 匹配范围：描述 + 关键词 + 分类标签（英文大小写不敏感）
                lower_terms = [t.lower() for t in filter_terms]
                candidates = [
                    key for key, content in data.items()
                    if self._match_filter(key, content, lower_terms)
                ]

            if candidates:
                # 使用局部随机实例避免全局种子污染
                if seed != 0:
                    local_random = random.Random(seed)
                    selected_key = local_random.choice(candidates)
                else:
                    selected_key = random.choice(candidates)
            else:
                print(f"[{self.NODE_NAME}] Warning: No items matched the filter keywords: {random_filter}")
                final_output = self.check_and_add_comma(prefix)
                return (final_output,)

        # 4. 选择 具体选项 —— 走 {描述: Key} 索引，避免全表扫描
        else:
            selected_key = self.get_desc_index(target_path).get(style_select, "")
        
        # --- 内容提取 【修改点 2】新增描述+关键词逻辑 ---
        if selected_key:
            item_data = data.get(selected_key, {})

            if output_mode == "Key":
                selected_content = selected_key
            elif output_mode == "关键词":
                # 用 _as_text 兜底数组型字段（见 _as_text 说明）
                selected_content = self._as_text(item_data.get("关键词")) or selected_key
            elif output_mode == "描述+关键词":
                description = self._as_text(item_data.get("描述"))
                keyword = self._as_text(item_data.get("关键词"))

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

# --- 分类选择器基类 ---
class BaseCategorizedJsonSelector(BaseJsonSelector):
    """
    所有支持分类的选择器节点的基类。
    子类只需设置 TARGET_JSON_FILE 和 NODE_NAME。
    本类提供双级下拉菜单（分类+项目）的通用逻辑。
    """

    # 分类 -> 项目列表 的映射。
    # 必须声明为类属性：原先只在 INPUT_TYPES 里动态赋值，一旦 JSON 加载失败
    # 或 INPUT_TYPES 从未被调用，process_text 访问它就会抛 AttributeError。
    _category_items_map = {}
    # 映射的来源指纹 (json 路径, 数据对象 id)，用于判断映射是否需要重建
    _category_map_source = None

    @classmethod
    def _build_category_items_map(cls, data):
        """从 JSON 数据构建 "分类 -> 项目描述列表" 映射（各分类内按名称排序）。"""
        categories = {}
        uncategorized = []

        for _key, content in (data or {}).items():
            if isinstance(content, dict) and "描述" in content:
                description = content["描述"]
                item_categories = content.get("分类", [])
                if item_categories:
                    for category in item_categories:
                        categories.setdefault(category, []).append(description)
                else:
                    uncategorized.append(description)

        # 分类名排序；"其他"（未分类）始终排在最后
        result = {c: sorted(items) for c, items in sorted(categories.items())}
        if uncategorized:
            result["其他"] = sorted(uncategorized)
        return result

    @staticmethod
    def _category_options_and_items(category_map):
        """由映射派生出两级下拉菜单的选项列表，保证与映射永远一致。"""
        category_options = ["无 (None)", "随机 (Random)", "自定义 (Custom)"]
        # "[隐藏]" 用于 category_select 为 无/随机/自定义 时占位，避免验证失败
        all_items = ["[隐藏]"]
        for category, items in category_map.items():
            category_options.append(category)
            # 标题行与 "*全部* (随机)" 必须出现在后端选项里，
            # 否则前端动态添加后提交时会报 "Value not in list"
            all_items.append(f"--- {category} ---")
            all_items.append("*全部* (随机)")
            all_items.extend(items)
        return category_options, all_items

    @classmethod
    def _ensure_category_items_map(cls):
        """返回最新的分类映射；JSON 内容变化后自动重建。

        以 (文件路径, 数据对象 id) 作为来源指纹：get_json_data 在文件未变时
        返回同一个缓存对象，重新加载后则是新对象，据此判断是否需要重建。
        这样即使只改了 JSON 而没点刷新按钮，分类内随机也不会用到过期列表。
        """
        if not cls.TARGET_JSON_FILE:
            return {}

        path = cls._json_file_path()
        data = cls.get_json_data(path)
        source = (path, id(data))

        if cls._category_map_source != source:
            try:
                cls._category_items_map = cls._build_category_items_map(data)
            except Exception as e:
                print(f"[Node: {cls.NODE_NAME}] Error processing JSON file '{cls.TARGET_JSON_FILE}': {e}")
                cls._category_items_map = {}
            cls._category_map_source = source

        return cls._category_items_map

    @classmethod
    def INPUT_TYPES(s):
        # 检查TARGET_JSON_FILE是否有效
        if not s.TARGET_JSON_FILE:
            print(f"[Node: {s.NODE_NAME}] Error: TARGET_JSON_FILE is empty")
            return {
                "required": {
                    "prefix": ("STRING", {"multiline": False, "default": "", "placeholder": "前置文本 (例如: style: )"}),
                    "category_select": (["无 (None)"], {"default": "无 (None)"}),
                    "item_select": (["[隐藏]"], {"default": "[隐藏]"}),
                    "output_mode": (["Key", "关键词", "描述+关键词"], {"default": "Key"}),
                    "random_filter": ("STRING", {"multiline": False, "default": "", "placeholder": FILTER_PLACEHOLDER}),
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

        category_map = s._ensure_category_items_map()
        category_options, all_items = s._category_options_and_items(category_map)

        return {
            "required": {
                "prefix": ("STRING", {"multiline": False, "default": "", "placeholder": "前置文本 (例如: style: )"}),
                "category_select": (category_options, {"default": "无 (None)"}),
                "item_select": (all_items, {"default": "[隐藏]"}),
                "output_mode": (["Key", "关键词", "描述+关键词"], {"default": "Key"}),
                "random_filter": ("STRING", {"multiline": False, "default": "", "placeholder": FILTER_PLACEHOLDER}),
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

    def process_text(self, prefix, category_select, item_select, output_mode, random_filter, custom_text, seed):
        """
        重写process_text方法，处理分类和项目选择
        支持在特定分类内随机选择（当item_select为"*全部* (随机)"时）
        """
        # 根据category_select和item_select确定style_select的值
        if category_select == "无 (None)":
            style_select = "无 (None)"
        elif category_select == "随机 (Random)":
            style_select = "随机 (Random)"
        elif category_select == "自定义 (Custom)":
            style_select = "自定义 (Custom)"
        else:
            # 具体分类选择
            # 用 _ensure_category_items_map() 而非直接读类属性：
            # 保证拿到的是与当前 JSON 同步的映射，且映射一定存在
            category_items = self._ensure_category_items_map().get(category_select, [])
            if not item_select or item_select == "[隐藏]" or item_select.startswith("--- "):
                # 如果item_select为空或为分类标题，使用该分类下的第一个项目
                if category_items:
                    style_select = category_items[0]
                else:
                    # 没有项目，当作"无"处理
                    style_select = "无 (None)"
            elif item_select == "*全部* (随机)":
                # 在该分类内随机选择一个项目，使用局部随机实例避免全局种子污染
                pool = category_items
                # 分类内随机同样遵循 random_filter（此前会被静默忽略）
                terms = [t.strip().lower() for t in random_filter.split(",") if t.strip()]
                if terms and pool:
                    data = self.get_json_data(self._json_file_path()) or {}
                    desc_index = self.get_desc_index(self._json_file_path())
                    pool = [
                        desc for desc in pool
                        if self._match_filter(desc_index.get(desc, ""),
                                              data.get(desc_index.get(desc, "")), terms)
                    ]
                    if not pool:
                        print(f"[{self.NODE_NAME}] Warning: No items in category "
                              f"'{category_select}' matched the filter keywords: {random_filter}")
                if pool:
                    if seed != 0:
                        local_random = random.Random(seed)
                        style_select = local_random.choice(pool)
                    else:
                        style_select = random.choice(pool)
                else:
                    # 没有项目，当作"无"处理
                    style_select = "无 (None)"
            else:
                # 具体项目选择
                style_select = item_select

        # 调用基类的process_text方法
        return super().process_text(prefix, style_select, output_mode, random_filter, custom_text, seed)


# --- 子类列表 (JSON Selector Nodes) ---

class StyleSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/styles.json"
    NODE_NAME = "Style Selector"

# ... (其余的 Selector 节点保持不变) ...

class ClothingSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/clothing.json"
    NODE_NAME = "Clothing Selector"

class PoseSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/pose.json"
    NODE_NAME = "Pose Selector"

class HairstylesSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/hairstyles.json"
    NODE_NAME = "Hairstyles Selector"

class EyeColorsSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/eye_colors.json"
    NODE_NAME = "Eye Colors Selector"

class BackgroundSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/background.json"
    NODE_NAME = "Background Selector"

class BodyTypesSelector(BaseCategorizedJsonSelector):
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

class CompositionSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/composition.json"
    NODE_NAME = "Composition Selector"


class ShoesSelector(BaseCategorizedJsonSelector):
    TARGET_JSON_FILE = "json/shoes.json"
    NODE_NAME = "Shoes Selector"


class ExpressionSelector(BaseJsonSelector):
    TARGET_JSON_FILE = "json/expressions.json"
    NODE_NAME = "Expression Selector"


def serialize_input_types(node_class):
    """把某个节点的 INPUT_TYPES() 转成可 JSON 序列化的结构，供前端热更新下拉菜单。

    ComfyUI 的 INPUT_TYPES 里每个字段形如 ``(选项列表 or 类型名, 配置字典)``，
    其中的元组无法直接 JSON 化，这里统一转成 ``[值, 配置]`` 数组。

    Returns:
        dict: {"required": {字段名: [值, 配置]}, "optional": {...}}
    """
    spec = node_class.INPUT_TYPES()
    result = {}
    for section, fields in spec.items():
        if not isinstance(fields, dict):
            continue
        serialized = {}
        for name, value in fields.items():
            if isinstance(value, tuple):
                first = value[0] if len(value) > 0 else []
                extra = value[1] if len(value) > 1 and isinstance(value[1], dict) else {}
                serialized[name] = [first, extra]
            else:
                serialized[name] = value
        result[section] = serialized
    return result


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
        # 使用字典查表提高可维护性
        SEPARATOR_MAP = {
            ", (逗号+空格)": ", ",
            ". (句号+空格)": ". ",
            "| (竖线+空格)": " | ",
            "\\n (回车/换行)": "\n",
        }
        separator = SEPARATOR_MAP.get(separator_select, "")
        if separator_select == "Custom (自定义)":
            separator = custom_separator.replace("\\n", "\n") 

        # 3. 收集并过滤掉 None/空值
        all_strings = [string_1, string_2, string_3, string_4, string_5,
                       string_6, string_7, string_8]
        cleaned_list = [s.strip() for s in all_strings if s and s.strip()]
        
        # 4. 联结字符串
        result = separator.join(cleaned_list)
        
        return (result,)