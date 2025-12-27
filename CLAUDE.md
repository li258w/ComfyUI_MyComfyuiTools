# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 ComfyUI 自定义节点插件，名为 "ComfyUI Style & Asset Selector"。它通过外部 JSON 文件管理和快速选择各种提示词（Prompt），支持样式、服装、姿势、构图等多种类目的独立选择。

## 架构设计

### 核心架构
- **基类模式**: 使用 `BaseJsonSelector` 基类，所有具体选择器节点都继承自此基类
- **模块化设计**: 每个节点对应一个 JSON 文件，互不干扰
- **热更新**: 修改 JSON 文件后，重启 ComfyUI 即可生效

### 文件结构
```
ComfyUI_MyComfyuiTools/
├── __init__.py              # 节点注册文件
├── selector_nodes.py        # 主要实现文件（当前版本）
├── readme.md               # 项目文档
├── js/                     # 前端JavaScript文件
│   └── widgets.js          # 双下拉菜单联动逻辑
├── backup/                 # 备份文件夹
│   ├── json/              # JSON备份文件
│   ├── classify_clothing.py      # 自动分类脚本
│   └── preview_categories.py     # 分类预览脚本
└── *.json                  # 11个JSON数据文件
```

### 节点注册机制
- 在 `__init__.py` 中注册所有节点类到 `NODE_CLASS_MAPPINGS`
- 节点显示名称在 `NODE_DISPLAY_NAME_MAPPINGS` 中定义
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

**clothing.json 特殊字段**：
```json
{
  "unique_key_name": {
    "描述": "下拉菜单中显示的中文描述",
    "关键词": "实际输出的英文提示词",
    "分类": ["中式", "复古", "街头"]  // 可选字段，支持多分类标签
  }
}
```

## 节点功能特性

### 输入参数
**所有选择器节点的通用参数**：
- `prefix`: 前置文本（如 "masterpiece, best quality"）
- `style_select`: 下拉选择菜单（包含"无"、"随机"、"自定义"和JSON条目）
- `output_mode`: 输出模式（"Key"、"关键词"、"描述+关键词"）
- `random_filter`: 随机模式筛选词（逗号分隔）
- `custom_text`: 自定义模式下的输入文本
- `seed`: 随机种子（支持 Fixed/Randomize/Increment）

**ClothingSelector 特殊参数**：
- `category_select`: 分类选择菜单（包含"无"、"随机"、"自定义"和所有分类）
- `item_select`: 项目选择菜单，根据 `category_select` 动态过滤
  - 包含特殊选项 "*全部* (随机)"：在所选分类内随机选择

### 输出逻辑
**通用输出逻辑**：
1. **无 (None)**: 仅输出前置文本
2. **自定义 (Custom)**: 输出 `custom_text` 内容
3. **随机 (Random)**: 从JSON中随机选择，支持关键词筛选
4. **具体选项**: 输出对应JSON条目的内容

**ClothingSelector 特殊输出逻辑**：
1. **分类选择流程**：
   - `category_select` 和 `item_select` 共同决定最终选择的项目
   - 当 `item_select` 为 "*全部* (随机)" 时，在 `category_select` 指定的分类内随机选择
   - 当 `item_select` 为空或为分类标题时，选择该分类下的第一个项目
2. **分类到项目的映射**：
   - 使用类属性 `_category_items_map` 存储分类到项目的映射
   - 在 `INPUT_TYPES` 中构建映射关系
   - 在 `process_text` 中根据映射进行选择

### 文本处理
- 自动检查并添加末尾标点符号（`check_and_add_comma` 方法）
- 支持前置文本拼接
- 自动处理中英文标点

## 包含的节点

插件包含以下11个选择器节点：
1. **JsonStyleSelector** - 风格 (`styles.json`)
2. **JsonClothingSelector** - 服装 (`clothing.json`)
   - **特殊功能**：支持21个风格主题分类，双级下拉菜单界面
   - **分类系统**：使用 `classify_clothing.py` 脚本自动分类，支持多标签
   - **前端联动**：通过 `js/widgets.js` 实现分类到项目的动态过滤
   - **随机选项**：支持分类内随机选择（"*全部* (随机)"选项）
3. **JsonPoseSelector** - 姿势 (`pose.json`)
4. **JsonHairstylesSelector** - 发型 (`hairstyles.json`)
5. **JsonEyeColorsSelector** - 眼睛颜色 (`eye_colors.json`)
6. **JsonBackgroundSelector** - 背景 (`background.json`)
7. **JsonBodyTypesSelector** - 体型 (`body_types.json`)
8. **JsonPlaceSelector** - 地点 (`place.json`)
9. **JsonHairColorSelector** - 头发颜色 (`hair_color.json`)
10. **JsonPhotoTypeSelector** - 照片类型 (`photo_type.json`)
11. **JsonCompositionSelector** - 构图 (`composition.json`)

### 工具节点
- **StringJoiner**: 多字符串联结工具，支持多种分隔符

## 开发注意事项

### 版本管理
- `selector_nodes.py` 是当前主版本（v1.7+）
- **v1.7 新增功能**：服装分类系统、双级下拉菜单、分类内随机选择、前端JavaScript联动
- **v1.6 新增功能**：随机筛选器、自定义模式、描述+关键词输出模式

### 代码修改
1. **添加新节点**: 创建新的子类继承 `BaseJsonSelector`，设置 `TARGET_JSON_FILE` 和 `NODE_NAME`
2. **修改基类**: 所有节点共享基类逻辑，修改会影响所有节点
3. **JSON文件**: 必须放在插件根目录，使用UTF-8编码

### 错误处理
- JSON文件加载失败时打印错误信息但不中断
- 随机筛选无匹配项时优雅降级，仅输出前置文本
- 所有异常都有适当的错误消息返回

## 测试和调试

### 开发流程
1. 修改代码后需要重启 ComfyUI 才能生效
2. JSON 文件修改后也需要重启 ComfyUI
3. 使用 ComfyUI 的节点面板测试功能

### 常见问题
- 确保 JSON 文件格式正确（UTF-8编码，正确的中文标点）
- 节点名称在 `__init__.py` 中正确注册
- 文件路径使用 `os.path.dirname(os.path.realpath(__file__))` 获取当前目录

## 扩展建议

### 添加新类别：
1. 创建新的 JSON 文件（如 `lighting.json`）
2. 在 `selector_nodes.py` 中添加新的选择器类
3. 在 `__init__.py` 中注册新节点
4. 重启 ComfyUI 测试

### 为现有节点添加分类系统（参考 ClothingSelector）：
1. **JSON数据准备**：
   - 在JSON条目中添加"分类"字段，格式为字符串数组：`"分类": ["标签1", "标签2"]`
   - 可以使用类似 `classify_clothing.py` 的脚本自动分类
2. **Python后端修改**：
   - 参考 `ClothingSelector` 类重写 `INPUT_TYPES` 方法
   - 构建 `_category_items_map` 类属性存储分类到项目的映射
   - 重写 `process_text` 方法处理分类选择逻辑
3. **前端JavaScript修改**：
   - 参考 `js/widgets.js` 实现双下拉菜单联动
   - 注册扩展时指定目标节点名称
   - 注意避免JavaScript无限递归（保存原始callback）
4. **注册前端资源**：
   - 在 `__init__.py` 中设置 `WEB_DIRECTORY = "./js"`
   - 确保JavaScript文件在正确的位置