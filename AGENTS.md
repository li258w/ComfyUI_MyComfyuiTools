# AGENTS.md

This file provides guidance to Codex (codex.ai) when working with code in this repository.

## 项目概述

这是一个 ComfyUI 自定义节点插件，名为 "ComfyUI Style & Asset Selector"。它通过外部 JSON 文件管理和快速选择各种提示词（Prompt），支持样式、服装、姿势、构图等多种类目的独立选择。

## 架构设计

### 核心架构
- **基类模式**: 使用 `BaseJsonSelector` 基类，所有具体选择器节点都继承自此基类
- **分类基类**: `BaseCategorizedJsonSelector` 继承 `BaseJsonSelector`，提供双级下拉菜单（分类+项目）通用逻辑
- **模块化设计**: 每个节点对应一个 JSON 文件，互不干扰
- **热更新**: 修改 JSON 文件后，重启 ComfyUI 即可生效

### 文件结构
```text
ComfyUI_MyComfyuiTools/        # 插件根目录
├── __init__.py                 # 节点注册文件（含 WEB_DIRECTORY）
├── selector_nodes.py           # 主要实现文件（423行）
├── readme.md                   # 项目文档
├── AGENTS.md                   # 本文件
├── UPDATE_LOG.md               # 更新日志
├── json/                       # JSON数据文件目录（13个文件）
│   ├── styles.json
│   ├── clothing.json
│   ├── pose.json
│   ├── composition.json
│   ├── shoes.json
│   ├── hairstyles.json
│   ├── body_types.json
│   ├── background.json
│   ├── place.json
│   ├── eye_colors.json
│   ├── hair_color.json
│   ├── photo_type.json
│   └── expressions.json
├── js/                         # 前端JavaScript文件
│   └── widgets.js              # 双下拉菜单联动逻辑
├── backup/                     # 备份文件夹
│   ├── json/                   # JSON备份文件
│   ├── classify_clothing.py      # 自动分类脚本
│   └── preview_categories.py     # 分类预览脚本
└── .gitignore
```

### 节点注册机制
- 在 `__init__.py` 中注册所有节点类到 `NODE_CLASS_MAPPINGS`
- 节点显示名称在 `NODE_DISPLAY_NAME_MAPPINGS` 中定义
- 前端资源目录通过 `WEB_DIRECTORY = "./js"` 注册
- **节点分类结构**：
  - 提示词选择器节点分类为 "MyCustomNodes/prompt"（所有继承 `BaseJsonSelector` 的节点）
  - 工具节点分类为 "MyCustomNodes/Utils"（`StringJoiner` 节点）

## JSON 数据格式

所有 JSON 文件使用统一格式：
```json
{
  "unique_key_name": {
    "描述": "下拉菜单中显示的中文描述",
    "关键词": "实际输出的英文提示词"
  }
}
```

**支持分类的JSON文件特殊字段**（clothing.json、pose.json、composition.json、shoes.json、hairstyles.json、body_types.json、background.json）：
```json
{
  "unique_key_name": {
    "描述": "下拉菜单中显示的中文描述",
    "关键词": "实际输出的英文提示词",
    "分类": ["上装（日常）", "街头", "运动休闲"]  // 可选字段，支持多分类标签
  }
}
```

## 节点功能特性

### 输入参数
**所有选择器节点的通用参数**：
- `prefix`: 前置文本（如 "masterpiece, best quality"）
- `style_select`（非分类节点）或 `category_select` + `item_select`（分类节点）: 选择菜单
- `output_mode`: 输出模式（"Key"、"关键词"、"描述+关键词"）
- `random_filter`: 随机模式筛选词（逗号分隔）
- `custom_text`: 自定义模式下的输入文本
- `seed`: 随机种子（支持 Fixed/Randomize/Increment）

**支持分类系统的选择器特殊参数**（ClothingSelector、PoseSelector、CompositionSelector、ShoesSelector、HairstylesSelector、BodyTypesSelector、BackgroundSelector）：
- `category_select`: 分类选择菜单（包含"无"、"随机"、"自定义"和所有分类）
- `item_select`: 项目选择菜单，根据 `category_select` 动态过滤
  - 包含特殊选项 `*全部* (随机)`：在所选分类内随机选择

### 输出逻辑
**通用输出逻辑**：
1. **无 (None)**: 仅输出前置文本
2. **自定义 (Custom)**: 输出 `custom_text` 内容
3. **随机 (Random)**: 从JSON中随机选择，支持关键词筛选
4. **具体选项**: 输出对应JSON条目的内容

**支持分类系统的选择器特殊输出逻辑**（所有 `BaseCategorizedJsonSelector` 子类）：
1. **分类选择流程**：
   - `category_select` 和 `item_select` 共同决定最终选择的项目
   - 当 `item_select` 为 `*全部* (随机)` 时，在 `category_select` 指定的分类内随机选择
   - 当 `item_select` 为空或为分类标题时，选择该分类下的第一个项目
2. **分类到项目的映射**：
   - 使用类属性 `_category_items_map` 存储分类到项目的映射
   - 在 `INPUT_TYPES` 中构建映射关系
   - 在 `process_text` 中根据映射进行选择

### 文本处理
- `check_and_add_comma` 方法自动检查并添加末尾标点符号
- 自动处理中英文标点集合：`.,;!?:。，；！？：`
- 支持前置文本拼接

## 包含的节点

插件包含以下 13 个选择器节点 + 1 个工具节点：

1. **JsonStyleSelector** - 风格 (`json/styles.json`) | 基类: `BaseJsonSelector`
2. **JsonClothingSelector** - 服装 (`json/clothing.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多分类，双级下拉菜单界面
   - **分类系统**：使用 `classify_clothing.py` 脚本自动分类，支持多标签
   - **前端联动**：通过 `js/widgets.js` 实现分类到项目的动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
3. **JsonPoseSelector** - 姿势 (`json/pose.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多姿势类型分类，双级下拉菜单界面
   - **分类系统**：为所有姿势条目添加分类标签，支持多标签
   - **前端联动**：通过 `js/widgets.js` 实现分类到项目的动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
4. **JsonCompositionSelector** - 构图 (`json/composition.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多构图风格分类，双级下拉菜单界面
   - **分类系统**：使用 `classify_composition.py` 脚本自动分类，支持多标签
   - **前端联动**：通过 `js/widgets.js` 实现分类到项目的动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
5. **JsonShoesSelector** - 鞋子 (`json/shoes.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多鞋子类型分类，双级下拉菜单界面
   - **前端联动**：通过 `js/widgets.js` 实现动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
6. **JsonHairstylesSelector** - 发型 (`json/hairstyles.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多发型分类，双级下拉菜单界面
   - **前端联动**：通过 `js/widgets.js` 实现动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
7. **JsonBodyTypesSelector** - 体型 (`json/body_types.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持多体型分类，双级下拉菜单界面
   - **前端联动**：通过 `js/widgets.js` 实现动态过滤
   - **随机选项**：支持分类内随机选择（`*全部* (随机)` 选项）
8. **JsonBackgroundSelector** - 背景 (`json/background.json`) | 基类: `BaseCategorizedJsonSelector`
   - **特殊功能**：支持2层简化分类系统（环境基调 + 场景类型），双级下拉菜单界面
   - **分类系统**：环境基调（室内/室外）+ 场景类型（科幻/奇幻/日常·生活/娱乐·活动/运动/人群/自然景观）
   - **设计理念**：极度简化、聚焦核心、高效率分组
9. **JsonExpressionSelector** - 表情 (`json/expressions.json`) | 基类: `BaseJsonSelector`
10. **JsonEyeColorsSelector** - 眼睛颜色 (`json/eye_colors.json`) | 基类: `BaseJsonSelector`
11. **JsonPlaceSelector** - 地点 (`json/place.json`) | 基类: `BaseJsonSelector`
12. **JsonHairColorSelector** - 头发颜色 (`json/hair_color.json`) | 基类: `BaseJsonSelector`
13. **JsonPhotoTypeSelector** - 照片类型 (`json/photo_type.json`) | 基类: `BaseJsonSelector`

### 工具节点
- **StringJoiner**: 多字符串联结工具，支持多种分隔符（逗号、句号、竖线、换行、自定义），最多8个输入

## 开发注意事项

### 版本管理
- `selector_nodes.py` 是当前主版本（v2.2+）
- **v2.2 新增功能**：
  - 新增 `ShoesSelector` 节点（鞋子选择器，BaseCategorizedJsonSelector）
  - 新增 `ExpressionSelector` 节点（表情选择器，BaseJsonSelector）
  - `HairstylesSelector` 升级为分类选择器（BaseCategorizedJsonSelector）
  - JSON 数据文件迁移至 `json/` 子目录
  - BaseCategorizedJsonSelector 内置 `*全部* (随机)` 选项，消除前后端验证不一致
  - 新增 `clear_json_cache()` 缓存清除方法
- **v2.1 新增功能**：背景分类系统、双级下拉菜单、分类内随机选择
  - 简化分类系统：2层标签（环境基调 + 场景类型）
- **v2.0 新增功能**：BodyTypes Selector 分类系统
- **v1.9 新增功能**：Pose Selector 分类系统
- **v1.8 新增功能**：Composition Selector 分类系统
- **v1.7 新增功能**：Clothing 分类系统、双级下拉菜单联动
- **v1.6 新增功能**：随机筛选器、自定义模式、描述+关键词输出模式

### 代码修改
1. **添加新节点**: 创建新的子类继承 `BaseJsonSelector`，设置 `TARGET_JSON_FILE` 和 `NODE_NAME`
2. **分类选择器**: 子类继承 `BaseCategorizedJsonSelector` 而非 `BaseJsonSelector`，自动获得双级下拉菜单
3. **修改基类**: 所有节点共享基类逻辑，修改会影响所有节点
4. **JSON文件**: 放在 `json/` 子目录（相对于 `selector_nodes.py`），使用UTF-8编码
5. **前端JS扩展**: 在 `js/widgets.js` 的节点名检查数组中添加新节点名来启用前端联动

### 错误处理
- JSON文件加载失败时打印错误信息但不中断
- 随机筛选无匹配项时优雅降级，仅输出前置文本
- 所有异常都有适当的错误消息返回

## 测试和调试

### 开发流程
1. 修改代码后需要重启 ComfyUI 才能生效
2. JSON 文件修改后也需要重启 ComfyUI
3. 使用 ComfyUI 的节点面板测试功能
4. 如需清除 JSON 缓存，调用 `BaseJsonSelector.clear_json_cache()`

### 常见问题
- 确保 JSON 文件格式正确（UTF-8编码，正确的中文标点）
- 节点名称在 `__init__.py` 中正确注册
- 文件路径使用 `os.path.dirname(os.path.realpath(__file__))` 获取当前目录
- 分类节点 name 需添加到 `js/widgets.js` 的节点列表中

## 扩展建议

### 添加新类别：
1. 创建新的 JSON 文件放入 `json/` 目录（如 `lighting.json`）
2. 在 `selector_nodes.py` 中添加新的选择器类（继承 `BaseJsonSelector` 或 `BaseCategorizedJsonSelector`）
3. 在 `__init__.py` 中注册新节点和显示名称
4. 如使用分类系统，在 `js/widgets.js` 的节点名数组中加入新节点名
5. 重启 ComfyUI 测试

### 为现有节点添加分类系统：
1. **JSON数据准备**：
   - 在JSON条目中添加 `"分类"` 字段，格式为字符串数组：`"分类": ["标签1", "标签2"]`
   - 可以使用类似 `classify_clothing.py` 的脚本自动分类
2. **Python后端修改**：将基类改为 `BaseCategorizedJsonSelector`（无需重写 `INPUT_TYPES` 或 `process_text`）
3. **前端JavaScript修改**：
   - 在 `js/widgets.js` 的节点名检查数组中添加新节点名
   - 注意保存原始 callback 避免无限递归
4. **注册前端资源**：确认 `__init__.py` 中已设置 `WEB_DIRECTORY = "./js"`
