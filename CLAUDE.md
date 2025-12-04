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
├── selector_nodes - V5.py   # 旧版本实现
├── readme.md               # 项目文档
└── *.json                  # 11个JSON数据文件
```

### 节点注册机制
- 在 `__init__.py` 中注册所有节点类到 `NODE_CLASS_MAPPINGS`
- 节点显示名称在 `NODE_DISPLAY_NAME_MAPPINGS` 中定义
- 所有节点分类为 "MyCustomNodes"

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

## 节点功能特性

### 输入参数
- `prefix`: 前置文本（如 "masterpiece, best quality"）
- `style_select`: 下拉选择菜单（包含"无"、"随机"、"自定义"和JSON条目）
- `output_mode`: 输出模式（"Key"、"关键词"、"描述+关键词"）
- `random_filter`: 随机模式筛选词（逗号分隔）
- `custom_text`: 自定义模式下的输入文本
- `seed`: 随机种子（支持 Fixed/Randomize/Increment）

### 输出逻辑
1. **无 (None)**: 仅输出前置文本
2. **自定义 (Custom)**: 输出 `custom_text` 内容
3. **随机 (Random)**: 从JSON中随机选择，支持关键词筛选
4. **具体选项**: 输出对应JSON条目的内容

### 文本处理
- 自动检查并添加末尾标点符号（`check_and_add_comma` 方法）
- 支持前置文本拼接
- 自动处理中英文标点

## 包含的节点

插件包含以下11个选择器节点：
1. **JsonStyleSelector** - 风格 (`styles.json`)
2. **JsonClothingSelector** - 服装 (`clothing.json`)
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
- `selector_nodes.py` 是当前主版本（v1.6+）
- `selector_nodes - V5.py` 是旧版本（v5），功能较少
- 当前版本新增功能：随机筛选器、自定义模式、描述+关键词输出模式

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

如需添加新类别：
1. 创建新的 JSON 文件（如 `lighting.json`）
2. 在 `selector_nodes.py` 中添加新的选择器类
3. 在 `__init__.py` 中注册新节点
4. 重启 ComfyUI 测试