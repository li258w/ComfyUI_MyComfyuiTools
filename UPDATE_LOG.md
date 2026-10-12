# 更新记录

---

## [2026-10-12] 数据整理：发型分类体系重构（`json/hairstyles.json`）

**问题**：发型 JSON 的分类标签是**形态 + 风格场景**两套维度混着用的，
37 个分类里有一大半是「朋克风 / 复古风 / 正式场合 / 日常 / 俏皮 / 运动」这类风格标签，
还有「自然纹理 / 质感特征 / 特殊质感 / 基础发型」这类空泛标签。结果是：

* 同一个发型被打上 3 个标签，风格标签一变就得另立一条（数据冗余、互相打架）；
* 下拉里 37 个类目很多只有 1~2 条内容，选起来像在翻废话；
* 风格诉求本来就该由 Style / 提示词侧追加，不该占着发型下拉的位置。

**处理**：

| 项目 | 改前 | 改后 |
| --- | --- | --- |
| 条目数 | 59 | **43** |
| 分类数 | 37 | **7** |
| Key 格式 | `with (bob cut hair)` / 整句英文提示词，两种风格混用 | 统一为规范英文短语（`bob cut hair`） |

* **新分类（7 个）**：短发、中长发、直发、卷发、编发与脏辫、扎发与盘发、局部与修剪。
  其中「局部与修剪」「扎发与盘发」「编发与脏辫」为本次新命名（旧体系的
  「扎发」「盘发」「半扎发型」「编发」「层次剪裁」「局部造型」等统一归并到此三者）。
  分类维度只保留**发型本身的形态**：长度、直卷、编扎方式、修剪手法。
* **删 16 条**：`long hair` / `short hair` / `straight hair` / `wavy hair` / `natural hair`
  这类已被「直发 / 卷发 / 短发」覆盖的同义重复项，加上 `gibson tuck`、
  `twisted updo`、`taper cut`、`side part`、`side-swept`、`middle ponytail`
  等与其他条目区分度不高的款式。
* **保留 43 条**全部补齐 `描述`（下拉短标签）+ `提示词`（输出文案）+ `分类` 三字段，
  沿用 v2.4 之后的字段约定。
* 清理遗留副本文件 `json/hairstyles - 副本.json`（内容与重构前完全一致，无信息损失）。

**连带修改**：`readme.md` 中 Hairstyles Selector 的条目数 / 分类数表格与分类清单同步更新
（59 → 43、37 → 7）。其余 6 个分类选择器的数字已逐个核对，与现状一致，无需改动。

**注意**：分类标签变了，工作流里如果 hardcode 了旧的 `category_select` 值
（例如「盘发」「复古风格」），需要重新选一次。

## [2026-10-11] 字段改名：`关键词` → `提示词`

**原因**：原数据里 `关键词` 存的是 30~90 字的完整输出文案，`描述` 存的是下拉显示的短标签，
两个字段名与实际语义正好相反（`关键词` 本该是短标签、`描述` 本该是长文案）。

**没有对调内容**，而是给字段正名——对调会让下拉框显示长文案（单行看不全）、输出反而变短。

| 改动范围 | 内容 |
| --- | --- |
| JSON 数据 | 13 个文件、1615 条条目的 `"关键词"` 字段名全部改为 `"提示词"`（内容不变） |
| `selector_nodes.py` | 字段读取改为 `提示词`；新增 `normalize_output_mode()`，旧工作流保存的 `关键词` / `描述+关键词` 自动映射到新值 |
| `output_mode` 选项 | 下拉显示改为 `Key` / `提示词` / `描述+提示词` |
| 文档 | readme.md、AGENTS.md、clothing_rules.md 同步更新；本文件的历史条目保留原文不改 |

**兼容性**：已保存的工作流中 `output_mode` 的旧字符串值仍可正常工作，无需手动改工作流。
筛选器同时兼容新旧字段名，`_as_text()` 继续兜底数组型字段（`styles.json` 的 `ForestCinematicSoftLight`）。

## [2026-10-09] v2.5 - 新增图片加载器模块（文件夹队列读图 + 确认后删除）

新增 3 个节点，分类 `MyCustomNodes/Image`：

| 节点类 | 显示名 |
| --- | --- |
| `LoadImageFromFolderQueue` | 加载图片·文件夹队列 (读完可删除) |
| `ConfirmDeleteImage` | 确认删除图片 (收尾) |
| `ImageQueueStatus` | 图片队列进度查询 |

### 新增文件

```text
image_loader_core.py       # 扫描 / 排序 / 进度记录 / 删除（不依赖 ComfyUI 与 torch，可单独测）
image_loader_nodes.py      # 3 个节点类
js/image_loader.js         # 缩略图预览 + 文件夹浏览按钮 + 重置进度按钮
selftest_image_loader.py   # 自测脚本（无需启动 ComfyUI）
docs/图片加载器使用说明.md   # 完整接线与参数说明
requirements.txt           # send2trash
```

`__init__.py` 里用 `NODE_CLASS_MAPPINGS.update(...)` 合并新节点，并新增
`_register_image_loader_routes()`（路由前缀 `/mycomfyuitools/imageloader/*`）。

### 关键设计决策

**1. 两种删除模式互斥**

| 想要的效果 | 加载节点 `after_load` | 收尾节点 |
| --- | --- | --- |
| 读出来就删，不等结果 | `delete` | 不需要 |
| 确认出图成功后再删 | **`keep`** | 必须接 |

原因是执行顺序：加载节点一读到图就立刻执行 `after_load`。若设 `delete`，
收尾节点拿到 `file_path` 时文件已经没了（跳过或报错），「确认后删」也就失去意义。

**2. 收尾节点必须标记 `OUTPUT_NODE = True`**

ComfyUI 只调度「输出节点及其祖先链」。普通节点没有下游就**根本不会执行**——
你会以为删了其实没删。设为 OUTPUT_NODE 后，即使孤零零放在画布上也会执行。

**3. `confirm_output` 用通配符而不是目录**

填目录时判断的是「目录里有没有图片」，而目录里通常有以前生成的图，
会导致**这次保存失败也误判成产物已生成照样删**。要真正确认这张存好了，
应填带前缀的通配符，例如 `D:\out\前缀_*.png`。

**4. `rollback_on_skip`**

跳过删除时会把该文件从「已读记录」里撤回，下次运行重新读到它——
不会因为一次失败就永久漏掉这张图。

### 踩过的坑（重要，改代码前先看）

**🐛 `send2trash` 在本机 Win11 上会误报 `FileNotFoundError`**

现象：删除后文件确实进了回收站（已用 Shell COM 枚举回收站确认），
但 `send2trash` 仍抛 `FileNotFoundError`。
**原因**：它用 pywin32 的 `IFileOperation`（modern 实现），异步操作返回时抛异常，
并不代表失败。
**处理**：判定改为「**以文件是否还在原处为准**」，不再以是否抛异常为准。
另外非 NTFS 卷（exFAT U盘 / 网络盘）没有回收站，自动降级为移到 `<源目录>/_trash/`。

**🐛 不加 `IS_CHANGED` 时 ComfyUI 会缓存住，永远读同一张**

加载节点用 `IS_CHANGED` 返回指纹强制每次运行真的推进，否则第二次运行会被缓存跳过。

**🐛 本机有「两套 custom_nodes」，只有 V0.7.0 那份生效**

```text
V0.7.0\ComfyUI\custom_nodes                          ← 启动脚本用这个，实际生效
ComfyUI_windows_portable\ComfyUI\custom_nodes        ← 不生效
```

只有 `models` / `output` 是符号链接共享的，`custom_nodes` 各自独立。
**插件必须放在 V0.7.0 那份下面。**

### 自测

```bash
D:\AI\ComfyUI_windows\V0.7.0\python_embeded\python.exe selftest_image_loader.py
```

覆盖 10 节：5 种排序、逐张推进、重置、删除与回收、张量形状、空目录报错、
路径容错、输出数量匹配、收尾节点各分支（开关 / 产物确认 / 跳过回滚 / 备份 / 批量 / 缺失报错）。
全部通过。

---

## [2026-10-09] v2.4 - 随机筛选器增强 + 索引性能 + 数组字段崩溃修复

### 🔧 增强：random_filter 匹配范围从 1 个字段扩展到 4 个

**问题**：`random_filter` 只匹配「描述」字段。用户的 JSON 数据约定是
「英文写在 key 上、关键词字段写中文」，所以输入英文关键词或分类名几乎筛不到结果。

**改动**：新增 `_collect_search_text(key, content)` 与 `_match_filter(key, content, lower_terms)`，
搜索范围扩大为 **key + 描述 + 关键词 + 分类标签**，英文大小写不敏感
（对中文无副作用）。多个筛选词维持原有「任一命中」（OR）语义，未改变既有行为。

**顺带修复**：分类节点选择 `*全部* (随机)` 时，`random_filter` 此前被**完全忽略**
——它只在 `category_select = 随机 (Random)` 的全局随机分支生效。
现在分类内随机会先按筛选词缩小候选池，无匹配时打印警告并降级为只输出 prefix。

**提示文案**：三处硬编码的 placeholder 提取为模块级常量 `FILTER_PLACEHOLDER`。

### ⚡ 性能：描述反查改用索引

**问题**：`process_text` 里靠遍历全表比对 `content["描述"] == style_select` 来反查 Key，
O(n) 且每次执行都要重跑一遍。

**改动**：新增 `get_desc_index(file_path)`，返回 `{描述: Key}` 映射。
索引存放在 JSON 缓存条目内，随文件指纹变化自动重建，无需额外失效逻辑。
重复描述时保留「首次出现」的 Key，与原先线性查找（命中即 break）行为完全一致。

**实测**：clothing.json（480 条）上快约 **460 倍**（10.1ms → 0.02ms / 40×60 次查询）。

### 🐛 修复：数组型「关键词」字段导致节点崩溃

**问题**：`json/styles.json` 的 `ForestCinematicSoftLight` 条目把「关键词」写成数组：

```json
"ForestCinematicSoftLight": {
  "描述": "绿色电影色调、软自然光...",
  "关键词": ["greenish-gray cinematic tone", "soft natural light", ...]
}
```

其余 1500+ 条目都是逗号拼接的字符串。选中该条目 + 「关键词」输出模式时，
列表被直接送进 `check_and_add_comma()`，抛出：

```
AttributeError: 'list' object has no attribute 'strip'
```

**改动**：新增 `_as_text(value)` 把数组/元组规整为 `", "` 拼接的字符串，
在三处做兜底：输出提取（`关键词` / `描述`）、筛选文本收集、`check_and_add_comma` 入口。
**未修改任何 JSON 数据文件**——如需把该条目改成字符串形式，请手工确认后再改。

### 🧹 整理

* `_json_file_path()` 从 `BaseCategorizedJsonSelector` 上提到 `BaseJsonSelector`，
  单级节点也能复用；顺带消除基类 `INPUT_TYPES` / `process_text` 里重复计算路径的
  两处内联代码。
* `.gitignore` 补充 `output/`、`tmp/`、`image/`、`*.bmp|tiff|webp`、`*_b64.txt`
  以及架构分析产物 `comfyui-selector-architecture.*`、`.code-review-graph/`。
  效果：仓库未跟踪文件数从数十降到 0。

### 🧪 验证

* **回归基线**（重构前后逐项一致）：Style 下拉 35、Clothing category 33 / item 1213 / 分类 30
* **索引等价性**：与旧线性查找逐条比对结果完全一致
* **筛选正确性**：9 个筛选词 × 200 次抽样，命中集合 100% 落在四字段匹配池内
  （cosplay 7/7、连衣裙 86/97、长袖 44/45、皮革 18/18、街头 87/100、
  dragon 3/3、wuxia 1/1、robe 10/10、无匹配 0/0 降级）
* **分类内随机**：遵循筛选、seed 可复现、无匹配降级、具体项选择不受筛选影响
* **崩溃修复**：三种 output_mode 全部正常输出
* **全部 13 个节点**的选项数量与分类映射无回归

### 📁 本次改动文件

- `selector_nodes.py` — 筛选器扩展、描述索引、`_as_text` 兜底、`_json_file_path` 上提
- `.gitignore` — 忽略运行/调试产物
- `readme.md` / `UPDATE_LOG.md` / `AGENTS.md` — 同步 v2.4

### ⚠️ 遗留项（需用户决定）

* `image/` 下约 4.4MB 临时测试文件与 552KB 的架构分析 HTML **已被 git 跟踪**，
  `.gitignore` 对已跟踪文件无效。若要移出版本控制需执行 `git rm --cached`，
  属于会改动 git 索引的操作，未擅自执行。
* `place.json` 仍只有 1 条数据。
* `json/styles.json` 的 `ForestCinematicSoftLight` 建议把「关键词」改成字符串，
  与其余条目保持一致（代码已能兼容，不改也不影响使用）。

---

## [2026-10-09] v2.3 - JSON 热更新 + 分类映射稳定性修复

本次是一次「体验修复」迭代，没有新增节点或数据，但解决了两个长期影响使用的问题。

### 🔥 新增：JSON 热更新

**问题**：`_JSON_CACHE` 是无过期时间的永久字典缓存，且 `INPUT_TYPES()` 只在 ComfyUI
启动时调用一次。导致修改任何 JSON 数据文件后，都必须重启 ComfyUI 才能看到新内容。

**解决方案**：三层改动。

1. **缓存指纹化** — `BaseJsonSelector._JSON_CACHE` 的结构由 `{path: data}` 改为
   `{path: {"signature": (mtime, size), "data": {...}}}`。每次 `get_json_data()` 用
   `os.stat` 比对指纹，文件一旦被修改就自动重新加载。文件被删除或改名时，
   会自动丢弃残留缓存，避免读到过期数据。
2. **新增刷新接口** — `__init__.py` 注册 `POST /mycomfyuitools/refresh`，
   body 可选 `{node_class}`。作用是清空 JSON 缓存，并返回指定节点最新的
   `INPUT_TYPES()` 结果。新增模块级函数 `serialize_input_types()`，负责把
   `INPUT_TYPES()` 里的元组（`(选项列表, 配置字典)`）转成 JSON 安全的 `[值, 配置]`。
3. **前端刷新按钮** — `js/widgets.js` 重写，给 13 个选择器节点加上「🔄 刷新 JSON」按钮。
   点击后请求刷新接口、写回最新选项、重建分类映射并重跑 `onCategoryChange()`；
   原选中值若已不存在会自动回落到第一项。

**为什么这条路线可行**：ComfyUI `server.py` 的 `node_info()` 在每次 `/object_info` 请求时
都会重新调用 `INPUT_TYPES()`，因此只要缓存会失效，新选项就能真正传到前端。

**注意**：刷新是按节点生效的，刷新 Clothing 不会影响 Pose，需分别点击。
改 `.py` / `.js` 代码本身仍然需要重启 ComfyUI。

### 🐛 修复：分类映射可能不存在导致节点崩溃

**问题**：`_category_items_map` 只在 `INPUT_TYPES()` 里被动态赋值。一旦 JSON 加载失败
（文件缺失、JSON 语法错误、`TARGET_JSON_FILE` 为空等），这个属性根本不会被创建，
而 `process_text()` 会直接访问 `self.__class__._category_items_map`，抛出：

```
AttributeError: type object 'XxxSelector' has no attribute '_category_items_map'
```

已用 `git show HEAD:selector_nodes.py` 导出旧版本对照，确认该异常真实存在。

**解决方案**：

1. 将 `_category_items_map = {}` 和 `_category_map_source = None` 声明为类属性作为兜底。
2. 重构 `BaseCategorizedJsonSelector`，把原先埋在 `INPUT_TYPES()` 里约 60 行的
   内联构建逻辑抽成四个方法：
   * `_json_file_path()` — 统一的 JSON 路径解析
   * `_build_category_items_map(data)` — 从 JSON 数据构建「分类 → 项目描述列表」映射
   * `_category_options_and_items(category_map)` — 由映射派生两级下拉选项
   * `_ensure_category_items_map()` — 返回最新映射，数据变化时自动重建
3. `_ensure_category_items_map()` 以 `(文件路径, id(数据对象))` 作为来源指纹：
   `get_json_data()` 在文件未变时返回同一个缓存对象，重新加载后则是新对象，
   据此判断是否需要重建。构建过程包在 try/except 中，出错时降级为空映射。

**附带收益**：

* 下拉选项和分类映射现在由同一份数据派生，结构上杜绝了
  `Value not in list: item_select: '*全部* (随机)'` 这类前后端不一致的验证错误。
* 修复了「改了 JSON 但没点刷新按钮时，分类内随机仍使用过期条目列表」的问题。

### 🧹 清理

* 移除 `selector_nodes.py` 中从未使用的 `import folder_paths`，插件不再依赖 ComfyUI 内部模块，
  可脱离 ComfyUI 环境直接导入测试。

### 🧪 验证

* **回归基线**（重构前后必须完全一致，已逐项核对）
  | 指标 | 改前 | 改后 |
  | --- | ---: | ---: |
  | Style Selector 下拉选项 | 35 | 35 |
  | Clothing category_select | 33 | 33 |
  | Clothing item_select | 1213 | 1213 |
  | Clothing 分类映射 | 30 | 30 |
* **分类节点构建**：Pose 15 分类 / 693 项，Background 9 分类 / 850 项，均正常。
* **异常场景**：JSON 文件缺失、`TARGET_JSON_FILE` 为空，均不再抛异常，降级输出错误提示文本。
* **接口测试**：用 ComfyUI 自带的 aiohttp 环境实测 `/mycomfyuitools/refresh`，
  返回 200 与正确的 `INPUT_TYPES()`；未知 `node_class` 与空 body 均优雅处理。
* **输出回归**：无 / 具体项 / 随机可复现 / 随机+筛选 / 自定义 / 分类内随机 /
  分类+具体项 / StringJoiner 共 12 个用例全部正常。

### 📁 本次改动文件

- `selector_nodes.py` — 缓存指纹化、`serialize_input_types()`、分类映射重构
- `__init__.py` — 新增 `POST /mycomfyuitools/refresh` 路由与路由注册函数
- `js/widgets.js` — 重写，新增「🔄 刷新 JSON」按钮，抽出 `buildCategoryItemMap()` / `applyFreshOptions()`
- `readme.md` — 节点数、分类数、数据统计全面校准，新增热更新说明与 v2.3 日志
- `AGENTS.md` — 同步架构说明与版本信息

### 🚀 下一步

* `random_filter` 目前只匹配「描述」字段，建议扩展到「关键词」和「分类」标签，
  这样可以直接用英文关键词或分类名筛选。
* 目前靠「描述」字符串反查 Key（O(n) 全表扫描），若 JSON 中出现重复描述会永远命中第一条，
  建议建立「描述 → Key」索引。
* `place.json` 仅 1 条数据，Place Selector 待补充。
* `image/` `output/` `tmp/` 下约 4MB 临时测试文件尚未纳入 `.gitignore`。

---

## [2026-04-09] v2.1 修复总结

### 🔧 **修复的问题：**

1. **Body Types Selector 验证错误** (`fb537a1`)
   - **问题**: `Value not in list: item_select: '*全部* (随机)' not in (list of length 50)`
   - **原因**: 前端 widgets.js 动态添加"*全部* (随机)"选项，但后端验证时该选项不在 item_select 列表中
   - **解决方案**: 在 BaseCategorizedJsonSelector 的 item_select 选项中包含"*全部* (随机)"选项

2. **分类选择器显示问题** (`a422815`)
   - **问题**: "*全部* (随机)"选项重复和显示混乱
   - **原因**: 后端在 item_select 中不包含"*全部* (随机)"，前端动态添加导致不一致
   - **解决方案**: 修正 BaseCategorizedJsonSelector，在每个分类标题后添加"*全部* (随机)"选项；添加 JSON 缓存清除功能

3. **Body Types 分类系统实现** (`bf58414`)
   - **新增**: 双级下拉菜单（分类+项目），支持分类内随机选择
   - **分类**: 纤细/瘦小、丰满/曲线、运动/健美、强壮/敦实、中性/其他、极端/夸张、其他/状态

### ✅ **验证结果：**

所有分类选择器当时均正确工作（此为当时统计，条目数后续有增长）：
ClothingSelector、CompositionSelector、PoseSelector、ShoesSelector、HairstylesSelector、BodyTypesSelector

### 📋 **使用说明：**

1. 重启 ComfyUI 后，所有分类选择器应正常工作
2. 缓存管理：如需清除 JSON 缓存，可调用 `BaseJsonSelector.clear_json_cache()`

> 📌 说明：本次更新日志中「重启 ComfyUI 后生效」的约定已在 v2.3 被热更新机制取代，
> 详见上方 [2026-10-09] 条目。