# ComfyUI Style & Asset Selector

这是一个为 ComfyUI 开发的自定义节点集合，旨在通过外部 JSON 文件管理和快速选择各种提示词（Prompt）。它支持样式、服装、姿势、构图等多种类目的独立选择，并具备强大的随机筛选和自定义功能。

## ✨ 核心功能 (Features)

* **模块化管理**：拥有 11 个独立节点（Style, Clothing, Pose, Composition 等），互不干扰。
* **双输出模式**：支持输出 JSON 的 `Key`（索引键）或详细的 `关键词`。
* **智能随机**：
    * 内置 `Seed` 控件，支持固定或随机生成。
    * **随机筛选器**：支持在随机模式下输入关键词（如"复古, 红色"），只在符合描述的条目中进行随机。
    * **分类内随机**：Clothing Selector 支持在特定分类内随机选择（通过"*全部* (随机)"选项）。
* **分类系统**：
    * **Clothing Selector**：21个服装风格主题分类（中式、哥特、复古等）
    * **Pose Selector**：10个姿势类型分类（站姿、坐姿、动态等）
    * **Composition Selector**：10个构图风格分类（经典人像、商业摄影等）
    * **双级下拉菜单**：先选分类，再选具体项目，界面更清晰
    * **动态过滤**：第二级菜单根据第一级选择动态更新
* **自定义模式**：可以直接在节点内输入自定义文本，跳过 JSON 选择。
* **文本拼接**：支持前置文本（Prefix）拼接，并自动处理末尾的标点符号（自动补全逗号）。
* **热更新**：修改 JSON 文件后，重启 ComfyUI 即可生效。

## 📂 包含的节点 (Nodes)

该插件包含以下 11 个选择器节点，分别读取对应的 JSON 文件：

1.  **Style Selector** (`styles.json`) - 风格
2.  **Clothing Selector** (`clothing.json`) - 服装
    * **特别功能**：支持21个风格主题分类，双级下拉菜单界面
    * **分类内随机**：可选择"*全部* (随机)"在特定分类内随机选择
    * **分类列表**：中式、哥特、复古、波西米亚、未来感、朋克、街头、极简、浪漫、性感、学院风、军装、嬉皮、海滩度假、运动休闲、正式商务、晚宴红毯、居家休闲、民族风情、戏剧舞台、其他
3.  **Pose Selector** (`pose.json`) - 姿势
    * **特别功能**：支持10个姿势类型分类，双级下拉菜单界面
    * **分类内随机**：可选择"*全部* (随机)"在特定分类内随机选择
    * **分类列表**：站姿、坐姿、动态、手势动作、表情情绪、正面朝向、侧面朝向、其他
4.  **Hairstyles Selector** (`hairstyles.json`) - 发型
5.  **Eye Colors Selector** (`eye_colors.json`) - 眼睛颜色
6.  **Background Selector** (`background.json`) - 背景
7.  **Body Types Selector** (`body_types.json`) - 体型
8.  **Place Selector** (`place.json`) - 地点
9.  **Hair Color Selector** (`hair_color.json`) - 头发颜色
10. **Photo Type Selector** (`photo_type.json`) - 照片类型/胶片
11. **Composition Selector** (`composition.json`) - 构图
    * **特别功能**：支持10个构图风格分类，双级下拉菜单界面
    * **分类内随机**：可选择"*全部* (随机)"在特定分类内随机选择
    * **分类列表**：经典人像、商业摄影、风景建筑、夜景摄影、电影感构图、时尚大片、街头纪实、艺术创作、自拍生活、其他

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
[2026-01-12] v1.9 - Pose Category System
新增功能：为 Pose Selector 节点添加姿势分类系统和双级下拉菜单。

**自动分类系统**：
- 为所有姿势条目添加分类标签，支持10个姿势类型分类
- 分类包括：站姿、坐姿、动态、手势动作、表情情绪、正面朝向、侧面朝向、其他

**双级下拉菜单**：
- 第一级：选择姿势类型分类（category_select）
- 第二级：选择具体姿势项目（item_select），根据第一级选择动态过滤
- 支持分类内随机选择：在 item_select 中添加 "*全部* (随机)" 选项，可在所选分类内随机选择项目

**技术实现**：
- 前端：扩展现有 JavaScript 联动逻辑（js/widgets.js），支持 Clothing、Composition 和 Pose 节点
- 后端：Python 处理分类映射和随机逻辑，与服装和构图选择器共享架构
- 自动隐藏/显示：当选择"无"、"随机"、"自定义"时隐藏项目选择框

[2025-12-28] v1.8 - Composition Category System
新增功能：为 Composition Selector 节点添加构图分类系统和双级下拉菜单。

**自动分类系统**：
- 使用 AI 辅助脚本将 94 个构图条目自动分类到 10 个风格主题
- 分类包括：经典人像、商业摄影、风景建筑、夜景摄影、电影感构图、时尚大片、街头纪实、艺术创作、自拍生活、其他

**双级下拉菜单**：
- 第一级：选择构图风格分类（category_select）
- 第二级：选择具体构图项目（item_select），根据第一级选择动态过滤
- 支持分类内随机选择：在 item_select 中添加 "*全部* (随机)" 选项，可在所选分类内随机选择项目

**技术实现**：
- 前端：复用现有 JavaScript 联动逻辑（js/widgets.js），同时支持 Clothing 和 Composition 节点
- 后端：Python 处理分类映射和随机逻辑，与服装选择器共享架构
- 自动隐藏/显示：当选择"无"、"随机"、"自定义"时隐藏项目选择框

[2025-12-27] v1.7 - Clothing Category & Two-level Dropdown
新增功能：为 Clothing Selector 节点添加服装分类系统和双级下拉菜单。

**自动分类系统**：
- 使用 AI 辅助脚本将 430 个服装条目自动分类到 21 个风格主题
- 分类包括：中式、哥特、复古、波西米亚、未来感、朋克、街头、极简、浪漫、性感、学院风、军装、嬉皮、海滩度假、运动休闲、正式商务、晚宴红毯、居家休闲、民族风情、戏剧舞台、其他

**双级下拉菜单**：
- 第一级：选择分类（category_select）
- 第二级：选择具体项目（item_select），根据第一级选择动态过滤
- 支持分类内随机选择：在 item_select 中添加 "*全部* (随机)" 选项，可在所选分类内随机选择项目

**技术实现**：
- 前端：JavaScript 动态联动下拉菜单（js/widgets.js）
- 后端：Python 处理分类映射和随机逻辑
- 自动隐藏/显示：当选择"无"、"随机"、"自定义"时隐藏项目选择框

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