# ComfyUI Style & Asset Selector

这是一个为 ComfyUI 开发的自定义节点集合，旨在通过外部 JSON 文件管理和快速选择各种提示词（Prompt）。它支持样式、服装、姿势、构图等多种类目的独立选择，并具备强大的随机筛选和自定义功能。

## ✨ 核心功能 (Features)

* **模块化管理**：拥有 11 个独立节点（Style, Clothing, Pose, Composition 等），互不干扰。
* **双输出模式**：支持输出 JSON 的 `Key`（索引键）或详细的 `关键词`。
* **智能随机**：
    * 内置 `Seed` 控件，支持固定或随机生成。
    * **随机筛选器**：支持在随机模式下输入关键词（如"复古, 红色"），只在符合描述的条目中进行随机。
* **自定义模式**：可以直接在节点内输入自定义文本，跳过 JSON 选择。
* **文本拼接**：支持前置文本（Prefix）拼接，并自动处理末尾的标点符号（自动补全逗号）。
* **热更新**：修改 JSON 文件后，重启 ComfyUI 即可生效。

## 📂 包含的节点 (Nodes)

该插件包含以下 11 个选择器节点，分别读取对应的 JSON 文件：

1.  **Style Selector** (`styles.json`) - 风格
2.  **Clothing Selector** (`clothing.json`) - 服装
3.  **Pose Selector** (`pose.json`) - 姿势
4.  **Hairstyles Selector** (`hairstyles.json`) - 发型
5.  **Eye Colors Selector** (`eye_colors.json`) - 眼睛颜色
6.  **Background Selector** (`background.json`) - 背景
7.  **Body Types Selector** (`body_types.json`) - 体型
8.  **Place Selector** (`place.json`) - 地点
9.  **Hair Color Selector** (`hair_color.json`) - 头发颜色
10. **Photo Type Selector** (`photo_type.json`) - 照片类型/胶片
11. **Composition Selector** (`composition.json`) - 构图

## 📝 JSON 数据格式 (JSON Format)

所有 JSON 文件需存放在插件根目录下，格式统一如下：

```json
{
  "unique_key_name": {
    "描述": "下拉菜单中显示的中文描述",
    "关键词": "实际输出的英文提示词"
  },
  "example_item": {
    "描述": "示例条目",
    "关键词": "example, prompt, text"
  }
}


🎮 使用指南 (Usage)
输入参数说明
prefix: 前置文本。例如输入 masterpiece, best quality。

style_select: 下拉选择菜单。

具体选项: 选择 JSON 中的特定条目。

无 (None): 不选择任何条目，仅输出 prefix。

随机 (Random): 在 JSON 中随机选择一个条目。

自定义 (Custom): 使用下方 custom_text 的内容。

output_mode: 输出模式。

Key: 输出 JSON 字典的键名（例如 unique_key_name）。

关键词: 输出 JSON 中的 关键词 字段内容。

random_filter: (仅在随机模式下生效) 输入筛选词（逗号分隔）。例如输入 裙子，则只会在描述中包含“裙子”的条目里随机。

custom_text: (仅在自定义模式下生效) 也就是手动输入框。

seed: 随机种子。控制随机选择的结果，支持“生成后控制（Fixed/Randomize/Increment）”。

📅 更新日志 (Changelog)
[2025-11-21] v1.6 - Random Filter Update
新增功能：增加了 random_filter 输入框。

允许用户在启用“随机 (Random)”模式时，输入关键词（如 "outdoor, nature"）。

节点会自动筛选 JSON 中“描述”字段包含这些关键词的条目，并限制随机范围。

优化：如果筛选后没有匹配项，节点将优雅降级，仅输出前置文本并打印警告，不会报错中断。

[2025-11-21] v1.5 - Custom Input & Composition Node
新增节点：增加了 Composition Selector (构图选择器)。

功能增强：在下拉菜单中增加了 自定义 (Custom) 选项。

新增输入：增加了 custom_text 输入框。当下拉菜单选择“自定义”时，直接输出此输入框的内容，忽略 JSON 数据。

[2025-11-21] v1.4 - Category Expansion
大规模重构：代码重构为模块化结构，引入 BaseJsonSelector 基类。

新增节点：一次性扩展了 7 个新类目：

Hairstyles, Eye Colors, Background, Body Types, Place, Hair Color, Photo Type。

优化：所有节点类代码统一管理，便于维护。

[2025-11-21] v1.3 - Architecture Refactor
结构调整：将单一节点拆分为多个独立节点（Style, Clothing, Pose）。

文件分离：核心逻辑移至 selector_nodes.py，__init__.py 仅负责注册。

命名优化：简化了节点显示名称（去掉 "My" 前缀）。

[2025-11-21] v1.2 - UX & Stability Improvements
体验升级：将 seed 输入改为内置 Widget，并开启 control_after_generate 属性。现在可以直接在节点面板上选择 Fixed 或 Randomize，无需连接外部 Seed 节点。

Bug修复：解决了随机模式下缓存导致结果不更新的问题。

[2025-11-21] v1.1 - Output Logic Enhancements
新增功能：增加了 output_mode 选项，允许用户选择输出 Key 或 关键词。

格式优化：增加了 check_and_add_comma 逻辑，确保输出文本末尾自动添加逗号（如果缺少）。

Bug修复：修复了前置文本拼接时多余逗号的问题。

[2025-11-21] v1.0 - Initial Release
基础功能：创建了首个 MyJsonStyleSelector 节点。

核心逻辑：实现了读取本地 styles.json 文件并显示在下拉菜单中。

拼接功能：实现了 Prefix + Selection 的文本拼接输出。