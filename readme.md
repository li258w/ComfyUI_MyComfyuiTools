# ComfyUI Style & Asset Selector

这是一个为 ComfyUI 开发的自定义节点集合，旨在通过外部 JSON 文件管理和快速选择各种提示词（Prompt）。它支持样式、服装、姿势、构图等多种类目的独立选择，并具备强大的随机筛选和自定义功能。

## ✨ 核心功能 (Features)

* **模块化管理**：共 **14 个节点**（13 个选择器 + 1 个工具节点），各类目互不干扰。
* **双输出模式**：支持输出 JSON 的 `Key`（索引键）、`关键词`，或 `描述+关键词`。
* **智能随机**：
    * 内置 `Seed` 控件，支持固定（Fixed）或随机生成（Randomize / Increment）。
    * **随机筛选器**：支持在随机模式下输入关键词，只在符合的条目中进行随机。
      匹配范围涵盖 **JSON 的 key、描述、关键词、分类标签** 四个位置，英文大小写不敏感，
      多个筛选词之间是「任一命中」的关系。
    * **分类内随机**：支持在特定分类内随机选择（通过 `*全部* (随机)` 选项），同样遵循筛选器。
* **分类系统**（7 个节点支持）：
    * **双级下拉菜单**：先选分类，再选具体项目，界面更清晰。
    * **动态过滤**：第二级菜单根据第一级选择动态更新。
    * 支持一个条目挂多个分类标签，因此每个类目下的实际条目数会多于 JSON 条目数。
* **自定义模式**：可以直接在节点内输入自定义文本，跳过 JSON 选择。
* **文本拼接**：支持前置文本（Prefix）拼接，并自动处理末尾的标点符号（自动补全逗号）。
* **🔥 JSON 热更新**：修改 `json/` 下的数据文件后，点击节点上的 **「🔄 刷新 JSON」** 按钮即可生效，**无需重启 ComfyUI**，也无需刷新浏览器。

## 📂 包含的节点 (Nodes)

### 单级选择器（6 个）

读取 JSON 后直接呈现一个下拉菜单。

| 节点 | 数据文件 | 条目数 |
| --- | --- | ---: |
| **Style Selector** | `json/styles.json` | 32 |
| **Eye Colors Selector** | `json/eye_colors.json` | 26 |
| **Hair Color Selector** | `json/hair_color.json` | 38 |
| **Photo Type Selector** | `json/photo_type.json` | 37 |
| **Expression Selector** | `json/expressions.json` | 49 |
| **Place Selector** | `json/place.json` | 1 |

> ⚠️ `place.json` 目前只有 1 条数据，Place Selector 基本还是空壳，待补充。

### 分类选择器（7 个）

带 `分类 + 项目` 双级下拉菜单，支持分类内随机。

| 节点 | 数据文件 | 条目数 | 分类数 |
| --- | --- | ---: | ---: |
| **Clothing Selector** | `json/clothing.json` | 480 | 30 |
| **Pose Selector** | `json/pose.json` | 272 | 15 |
| **Background Selector** | `json/background.json` | 425 | 9 |
| **Composition Selector** | `json/composition.json` | 94 | 10 |
| **Shoes Selector** | `json/shoes.json` | 54 | 14 |
| **Hairstyles Selector** | `json/hairstyles.json` | 55 | 33 |
| **Body Types Selector** | `json/body_types.json` | 42 | 7 |

<details>
<summary><b>点击展开各节点的分类清单</b></summary>

* **Clothing Selector**（30 类）
  cosplay、上装、下装、丝绸材质、休闲风格、优雅风格、全身组合、内衣 / 泳装、哥特风格、复古风格、套装（有鞋）、学院风、居家休闲、户外、朋克风、正式场合、民族传统、泳装、海滩度假、牛仔材质、甜美风、皮革材质、秋冬、绸缎材质、职业装、街头风、运动风、连衣裙、雪纺材质、其他
* **Pose Selector**（15 类）
  互动姿势、侧面转身、其他、坐姿、手势动作、日常休闲、时尚摆拍、正式姿势、正面朝向、站姿、背面朝向、表情情绪、蹲跪姿、躺姿、运动动态
* **Background Selector**（9 类）
  人群、奇幻、娱乐/活动、室内、室外、日常/生活、科幻、自然景观、运动
  *设计理念*：只保留两个核心标签维度——**物理位置**（室内/室外，其余 7 类是主题场景），避免分类过细导致选择困难。
* **Composition Selector**（10 类）
  其他、商业摄影、夜景摄影、时尚大片、电影感构图、经典人像、自拍生活、艺术创作、街头纪实、风景建筑
* **Shoes Selector**（14 类）
  休闲鞋、凉鞋、安全鞋、居家休闲、帆布鞋、户外鞋、拖鞋、时尚潮流、正装鞋、皮鞋、舞蹈鞋、运动鞋、靴子、高跟鞋
* **Hairstyles Selector**（33 类）
  休闲风格、俏皮风格、修饰脸型、创意剪裁、剪裁工艺、半扎发型、卷发、基础发型、复古风格、局部造型、层次剪裁、手工造型、扎发、摇滚风格、文化发型、日常风格、朋克风格、极简风格、正式场合、民族风、特殊质感、特殊造型、现代风格、盘发、直发、短发、经典发型、编发、自然特征、自然纹理、质感特征、运动风格、长发
* **Body Types Selector**（7 类）
  中性/其他、丰满/曲线、其他/状态、强壮/敦实、极端/夸张、纤细/瘦小、运动/健美

</details>

### 工具节点（1 个）

* **StringJoiner**：多字符串拼接，支持 8 路输入，分隔符可选逗号 / 句号 / 竖线 / 换行 / 自定义。

## 📝 JSON 数据格式 (JSON Format)

所有 JSON 文件存放在插件根目录下的 `json/` 子目录，格式统一如下：

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
```

**支持分类的 7 个节点**（Clothing / Pose / Background / Composition / Shoes / Hairstyles / Body Types）额外支持可选的 `分类` 字段，格式为字符串数组，一个条目可挂多个标签：

```json
{
  "unique_key_name": {
    "描述": "下拉菜单中显示的中文描述",
    "关键词": "实际输出的英文提示词",
    "分类": ["上装", "街头", "运动风"]
  }
}
```

没有 `分类` 字段的条目会被归入自动生成的 **「其他」** 分类。

## 🎮 使用指南 (Usage)

### 输入参数

* **prefix**：前置文本。例如输入 `masterpiece, best quality`。
* **style_select**（单级节点） / **category_select + item_select**（分类节点）：下拉选择菜单。
  * **无 (None)**：不选择任何条目，仅输出 prefix。
  * **随机 (Random)**：在 JSON 中随机选择一个条目。
  * **自定义 (Custom)**：使用下方 `custom_text` 的内容。
  * **分类节点额外支持 `*全部* (随机)`**：在所选分类内随机选择。
* **output_mode**：输出模式。
  * **Key**：输出 JSON 字典的键名（例如 `cinematic_realism`）。
  * **关键词**：输出 `关键词` 字段内容。
  * **描述+关键词**：输出 `描述(关键词)`，便于回溯提示词来源。
* **random_filter**：随机筛选词（逗号分隔）。
  * 匹配范围：**JSON 的 key、描述、关键词、分类标签**（英文大小写不敏感）。
    把 key 也纳入搜索很关键——本插件的数据约定是「英文写在 key 上、关键词字段写中文」，
    不搜 key 的话英文筛选几乎筛不到东西。
  * 多个筛选词之间是「**任一命中**」（OR）关系。
  * 例如输入 `裙子` 只会在相关条目里随机；输入 `dragon` 会命中 key 里含 dragon 的条目。
  * 分类节点里选择 `*全部* (随机)` 时同样遵循此筛选器。
  * 筛选后无匹配项时仅输出 prefix 并打印警告，不会中断。
* **custom_text**：（仅在「自定义」模式下生效）手动输入框的内容。
* **seed**：随机种子。控制随机选择的结果，支持「生成后控制（Fixed / Randomize / Increment）」。
* **🔄 刷新 JSON**：按钮。重新读取 `json/` 下的数据并刷新下拉菜单选项。

### 热更新用法

1. 用任意编辑器修改 `json/` 下的文件并保存。
2. 回到 ComfyUI，点击对应节点上的 **「🔄 刷新 JSON」**。
3. 下拉菜单立即更新，无需重启 ComfyUI，也无需刷新浏览器。

> 刷新是**按节点**的：刷新了 Clothing Selector，Pose Selector 的选项不会跟着变，需分别点击。
> 后端缓存以文件指纹（修改时间 + 大小）判定，文件没变时不会重复读取磁盘。

## 📅 更新日志 (Changelog)

### [2026-10-09] v2.4 - 随机筛选器增强 + 性能与稳定性

**🔧 增强：随机筛选器匹配范围从 1 个字段扩展到 4 个**

* 原先只匹配「描述」，导致输入英文关键词或分类名筛选不到任何结果。
* 现在匹配 **key + 描述 + 关键词 + 分类标签**，且英文大小写不敏感。
* 纳入 key 是关键：本插件的数据约定是「英文写在 key 上、关键词字段写中文」，
  不搜 key 的话英文筛选几乎无效。
* 多个筛选词维持原有的「任一命中」（OR）语义，未改变既有行为。
* 修复分类节点 `*全部* (随机)` **完全忽略筛选器**的问题——此前它只在全局随机模式下生效。
* 筛选器提示文案提取为 `FILTER_PLACEHOLDER` 常量，避免三处硬编码不一致。

**⚡ 性能：用 `{描述: Key}` 索引替代全表扫描**

* 新增 `get_desc_index()`，索引随 JSON 缓存一起失效，无需额外维护。
* 描述反查从 O(n) 降为 O(1)，实测快约 **460 倍**（clothing.json 480 条）。
* 重复描述仍保留「首次出现」的 Key，与原先线性查找（命中即 break）行为完全一致。

**🐛 修复：数组型「关键词」字段导致节点崩溃**

* `json/styles.json` 的 `ForestCinematicSoftLight` 把「关键词」写成了数组，
  而其余 1500+ 条目都是逗号拼接的字符串。选中该条目 + 「关键词」输出模式时，
  `check_and_add_comma()` 会对列表调用 `.strip()`，抛出
  `AttributeError: 'list' object has no attribute 'strip'`。
* 新增 `_as_text()` 统一规整字段值（数组 → `", "` 拼接），在输出提取、
  筛选匹配、标点处理三处都做了兜底。**未修改任何 JSON 数据文件**。

**🧹 整理**

* `_json_file_path()` 从 `BaseCategorizedJsonSelector` 上提到 `BaseJsonSelector`，
  单级节点也能复用，消除基类里重复计算路径的两处内联代码。
* `.gitignore` 补充 `output/` `tmp/` `image/` 及架构分析产物。

### [2026-10-09] v2.3 - JSON 热更新 + 稳定性修复

**🔥 新增：JSON 热更新（彻底解决"改完数据必须重启 ComfyUI"）**

* 后端：JSON 缓存改用「修改时间 + 文件大小」作为指纹，文件一变就自动重载。
* 后端：新增 `POST /mycomfyuitools/refresh` 接口，清缓存并返回指定节点最新的下拉选项。
* 前端：13 个选择器节点新增「🔄 刷新 JSON」按钮，一键刷新选项，无需刷新浏览器。

**🐛 修复：分类映射可能不存在导致节点崩溃**

* `_category_items_map` 之前只在 `INPUT_TYPES()` 里动态创建，一旦 JSON 加载失败，
  `process_text()` 访问它会抛 `AttributeError`。现改为类属性默认值 `{}`，并对
  JSON 缺失、文件损坏、`TARGET_JSON_FILE` 为空等情况全部优雅降级。
* 重构：分类映射的构建逻辑从 `INPUT_TYPES()` 抽成
  `_build_category_items_map()` / `_ensure_category_items_map()` 等方法，
  下拉选项与映射由同一份数据派生，杜绝两者不一致导致的
  `Value not in list: item_select` 报错。
* 连带修复：修改 JSON 后但未点刷新按钮时，「分类内随机」会用到过期条目列表的问题。

**🧹 清理**

* 移除未使用的 `import folder_paths` 依赖。

### [2026-04-16] v2.2 - 新增节点与数据目录迁移

* 新增 `Shoes Selector`（鞋子，分类选择器）。
* 新增 `Expression Selector`（表情，单级选择器，49 种情绪）。
* `Hairstyles Selector` 升级为分类选择器（33 个分类）。
* JSON 数据文件迁移至 `json/` 子目录。
* `BaseCategorizedJsonSelector` 内置 `*全部* (随机)` 选项，消除前后端验证不一致。
* 新增 `clear_json_cache()` 缓存清除方法。

### [2026-04-14] v2.1 - Background Category System

* 为 Background Selector 添加背景分类系统和双级下拉菜单。
* **简化分类系统**：采用极度简化的 9 类标签：环境基调（室内 / 室外）+ 场景类型（科幻 / 奇幻 / 日常/生活 / 娱乐/活动 / 运动 / 人群 / 自然景观）。
* 为所有 425 个背景条目添加分类标签，支持多标签。
* 自动隐藏/显示：当 category_select 为「无」「随机」「自定义」时隐藏项目选择框。

### [2026-04-08] v2.0 - Body Types Category System

* 为 Body Types Selector 添加体型分类系统（7 个分类）和双级下拉菜单。
* 前端复用 `js/widgets.js` 联动逻辑，后端与服装、姿势、构图选择器共享架构。

### [2026-01-12] v1.9 - Pose Category System

* 为 272 个姿势条目添加 15 个姿势类型分类标签，支持多标签。

### [2025-12-28] v1.8 - Composition Category System

* 使用 AI 辅助脚本将 94 个构图条目自动分类到 10 个风格主题。

### [2025-12-27] v1.7 - Clothing Category & Two-level Dropdown

* 使用 AI 辅助脚本将服装条目自动分类到功能分类，首个双级下拉菜单节点。

### [2025-11-21] v1.6 - Random Filter Update

* 增加 `random_filter` 输入框，允许在随机模式下按关键词限定随机范围。
* 优化：筛选后无匹配项时优雅降级，仅输出前置文本并打印警告。

### [2025-11-21] v1.5 - Custom Input & Composition Node

* 下拉菜单增加「自定义 (Custom)」选项与 `custom_text` 输入框。
* 新增 Composition Selector。

### [2025-11-21] v1.4 - Category Expansion

* 代码重构为模块化结构，引入 `BaseJsonSelector` 基类。
* 一次性扩展 Hairstyles、Eye Colors、Background、Body Types、Place、Hair Color、Photo Type 七个类目。

### [2025-11-21] v1.3 - Architecture Refactor

* 将单一节点拆分为多个独立节点（Style、Clothing、Pose）。
* 核心逻辑移至 `selector_nodes.py`，`__init__.py` 仅负责注册。

### [2025-11-21] v1.2 - UX & Stability Improvements

* `seed` 改为内置 Widget 并开启 `control_after_generate`，无需外接 Seed 节点。
* 修复随机模式下缓存导致结果不更新的问题。

### [2025-11-21] v1.1 - Output Logic Enhancements

* 增加 `output_mode` 选项，允许选择输出 Key 或关键词。
* 增加 `check_and_add_comma` 逻辑，确保输出文本末尾标点正确。

### [2025-11-21] v1.0 - Initial Release

* 创建首个 `MyJsonStyleSelector` 节点，实现读取本地 styles.json 并显示在下拉菜单。
* 实现 Prefix + Selection 的文本拼接输出。