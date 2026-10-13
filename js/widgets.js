// ComfyUI自定义widget
// 1) 分类选择器的双级下拉菜单联动（分类 -> 项目）
// 2) 所有选择器节点的"刷新"按钮：拉取服务端最新的 JSON 选项，实现热更新（无需重启 ComfyUI）
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// 支持双级下拉菜单（分类+项目）的节点
const CATEGORIZED_NODES = [
    "JsonClothingSelector",
    "JsonCompositionSelector",
    "JsonPoseSelector",
    "JsonShoesSelector",
    "JsonHairstylesSelector",
    "JsonBodyTypesSelector",
    "JsonBackgroundSelector",
];

// 单级下拉菜单的选择器节点
const PLAIN_NODES = [
    "JsonStyleSelector",
    "JsonEyeColorsSelector",
    "JsonPlaceSelector",
    "JsonHairColorSelector",
    "JsonPhotoTypeSelector",
    "JsonExpressionSelector",
    "JsonAccessorySelector",
];

// 所有带"刷新"按钮的节点（不含 StringJoiner，它没有 JSON 选项）
const ALL_SELECTOR_NODES = CATEGORIZED_NODES.concat(PLAIN_NODES);

// 从 item_select 的完整选项列表里解析出 "分类 -> 项目列表" 映射
// 选项格式: ["[隐藏]", "--- 分类A ---", "*全部* (随机)", "项目1", ...]
function buildCategoryItemMap(itemValues) {
    const map = {};
    let currentCategory = null;
    for (const option of itemValues) {
        if (typeof option === "string" && option.startsWith("--- ")) {
            currentCategory = option.replace("--- ", "").replace(" ---", "");
            map[currentCategory] = [];
        } else if (currentCategory) {
            // "*全部* (随机)" 是特殊选项，不参与随机池
            if (option === "*全部* (随机)") continue;
            map[currentCategory].push(option);
        }
    }
    return map;
}

// 把服务端返回的最新选项写回 widget
function applyFreshOptions(node, required) {
    for (const w of node.widgets) {
        const spec = required ? required[w.name] : null;
        if (!spec || !Array.isArray(spec[0])) continue; // 只处理下拉菜单（选项为数组）
        const values = spec[0];
        const prev = w.value;
        w.options.values = values;
        if (!values.includes(prev)) {
            w.value = values.length > 0 ? values[0] : undefined;
        }
    }
}

async function fetchFreshInput(nodeClass) {
    const resp = await api.fetchApi("/mycomfyuitools/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_class: nodeClass }),
    });
    const data = await resp.json();
    if (!data || !data.ok || !data.input) {
        throw new Error((data && data.error) || "server returned no input");
    }
    return data.input;
}

// ── custom_text 加高 2 行 ──────────────────────────────────
// ComfyUI 给多行文本框预留固定高度（computeLayoutSize 约 60px ≈ 3 行）。
// 要让 custom_text 多显示 2 行，正确做法是告诉框架「我这个 widget 需要更高」，
// 由框架在布局时把节点一起撑开。
// 注意：只声明一次高度即可，不要在事件里反复 node.setSize()，
// 那会和框架的 computeSize 抢布局控制权，导致高度来回跳。
const EXTRA_LINES = 2;                 // custom_text 比默认多显示几行
const BASE_LINE_HEIGHT = 11 * 1.35;    // 与下面 CSS 的 font-size/line-height 保持一致
const FRAME_SPACING = 4;               // 框架在每个 widget 高度外还会加的间距（y += t + 4）
const VISUAL_GAP = 10;                 // 元素与下一个控件之间保留的空隙，对齐 prefix 的观感

// 元素实际渲染高度（用户看到的框高）
const CUSTOM_TEXT_BOX = Math.round(60 + EXTRA_LINES * BASE_LINE_HEIGHT);
// 报给框架的槽位高度 = 框高 + 框架间距 + 视觉空隙
// 两者分开算，框才不会把间距吃掉、压住下方控件。
const CUSTOM_TEXT_SLOT = CUSTOM_TEXT_BOX + FRAME_SPACING + VISUAL_GAP;

// 只对 custom_text 这个 widget 生效。
//
// 关键：框架的布局代码是
//     if (e.computeSize)            t += e.computeSize(width)[1]
//     else if (e.computeLayoutSize) { ... }
// 只要 widget 上存在 computeSize，computeLayoutSize 就永远不会被调用，
// 所以必须覆盖 computeSize（它返回 [宽, 高]）。
function makeCustomTextTaller(node, widget) {
    if (widget.__myTallerPatched) return;
    widget.__myTallerPatched = true;

    const origLayout = widget.computeLayoutSize?.bind(widget);
    const origCompute = widget.computeSize?.bind(widget);

    widget.computeLayoutSize = function (n) {
        const r = origLayout ? origLayout(n) : { minWidth: 20, maxWidth: 1e6 };
        return { ...r, minHeight: CUSTOM_TEXT_SLOT, maxHeight: CUSTOM_TEXT_SLOT };
    };

    widget.computeSize = function (width) {
        const sz = origCompute ? origCompute(width) : [width ?? 0, CUSTOM_TEXT_SLOT];
        return [sz[0], CUSTOM_TEXT_SLOT];
    };

    // 给元素打标记，便于排查（element 缺失时从节点 DOM 里找）
    const el =
        widget.element ||
        (typeof widget.querySelector === "function" ? widget.querySelector("textarea") : null);
    if (el && el.tagName === "TEXTAREA") {
        el.classList.add("my-myct-textarea");
    }
}

// ── 多行文本框样式 ──────────────────────────────────────────
// ComfyUI 的 .comfy-multiline-input 默认按 placeholder 决定视觉高度，
// 而我们的 placeholder 较长会折行，导致第二行压住下方控件。
// 这里给一个与框架预留高度一致的固定高度，超出部分用滚动条。
const MULTILINE_CSS = `
/* 只作用于本插件的三个字段，避免影响其他插件的文本框 */
textarea.comfy-multiline-input {
    font-size: 11px !important;
    line-height: 1.35 !important;
    white-space: pre-wrap;
    word-break: break-word;
    overflow-y: auto !important;
}
/* custom_text 比其他两个多显示 2 行 */
textarea.comfy-multiline-input.my-myct-textarea {
    height: ${CUSTOM_TEXT_BOX}px !important;
    min-height: ${CUSTOM_TEXT_BOX}px !important;
}
`;
if (typeof document !== "undefined" && !document.getElementById("mycomfyuitools-style")) {
    const st = document.createElement("style");
    st.id = "mycomfyuitools-style";
    st.textContent = MULTILINE_CSS;
    document.head.appendChild(st);
}

// ── StringJoiner 接入点名：动态显示 + 自定义名 ──────────────────
// 1) 输入口连上节点 → 标签显示所连节点的标题（过长截断），断开恢复
// 2) slot_labels 每行一个自定义名（第 1 行对应 string_1），未连线的口显示自定义名
// 3) 优先级：连上了显示源标题；没连显示自定义名；都没有显示默认 string_N
// 4) label 只是前端展示，不参与序列化传值——旧工作流打开不受影响
const JOINER_NODES = ["StringJoiner"];
const SLOT_LABEL_MAX = 8;
const INPUT_TYPE = (typeof LiteGraph !== "undefined" && LiteGraph.INPUT) || 1;

function setupStringJoiner(nodeType) {
    // onConnectionsChange 在 nodeType 级只包装一次（每次 onNodeCreated 再包会叠罗汉）
    const origOcc = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (type, index, connected, linkInfo) {
        if (origOcc) origOcc.apply(this, arguments);
        if (type !== INPUT_TYPE) return;
        const input = this.inputs && this.inputs[index];
        if (input && /^string_\d+$/.test(input.name) && this.__joinerRefreshInput) {
            this.__joinerRefreshInput(input, connected);
        }
    };

    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

        const node = this;
        const slotInputs = (node.inputs || []).filter((i) => /^string_\d+$/.test(i.name));
        const labelWidget = (node.widgets || []).find((w) => w.name === "slot_labels");

        const truncate = (s) => {
            const t = String(s || "").trim();
            return t.length > SLOT_LABEL_MAX ? t.slice(0, SLOT_LABEL_MAX) + "…" : t;
        };

        // slot_labels 第 i 行 → 第 i 个输入口的自定义名
        const customLabelOf = (input) => {
            if (!labelWidget) return "";
            const lines = String(labelWidget.value || "").split("\n");
            const idx = slotInputs.indexOf(input);
            return idx >= 0 && idx < lines.length ? lines[idx].trim() : "";
        };

        node.__joinerRefreshInput = (input, connected) => {
            const custom = customLabelOf(input);
            if (connected) {
                let title = "";
                if (input.link != null && node.graph) {
                    const link = node.graph.links[input.link];
                    const origin = link && node.graph.getNodeById(link.origin_id);
                    // origin.title 默认就是节点的显示名（用户改过标题则用自定义标题）
                    title = origin ? truncate(origin.title) : "";
                }
                input.label = title || custom || input.name;
            } else {
                input.label = custom || input.name;
            }
        };

        const refreshAll = () => {
            for (const input of slotInputs) {
                node.__joinerRefreshInput(input, input.link != null);
            }
        };
        node.__joinerRefreshAll = refreshAll;

        if (labelWidget) {
            const origCb = labelWidget.callback;
            labelWidget.callback = function (v) {
                if (origCb) origCb.call(this, v);
                refreshAll();
            };
        }

        // 兜底：等节点挂上 graph 后补一次（重开工作流时连线事件可能已过）
        requestAnimationFrame(() => requestAnimationFrame(refreshAll));
    };
}

app.registerExtension({
    name: "ComfyUI_MyComfyuiTools.CategoryItemWidget",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // StringJoiner 有独立的接入点标签逻辑，不走选择器分支
        if (JOINER_NODES.includes(nodeData.name)) {
            setupStringJoiner(nodeType);
            return;
        }

        if (!ALL_SELECTOR_NODES.includes(nodeData.name)) {
            return;
        }

        const isCategorized = CATEGORIZED_NODES.includes(nodeData.name);

        // 保存原始的onNodeCreated
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            // 调用原始方法
            if (originalOnNodeCreated) {
                originalOnNodeCreated.apply(this);
            }

            const node = this;

            // custom_text 多显示 2 行：告知框架更高的布局高度。
            // DOM 可能尚未挂载，最多重试 30 帧。
            let tries = 0;
            const applyTaller = () => {
                const w = (node.widgets || []).find((x) => x.name === "custom_text");
                if (w && w.element) {
                    makeCustomTextTaller(node, w);
                    return;
                }
                if (tries++ < 30) requestAnimationFrame(applyTaller);
            };
            applyTaller();

            let categoryItemMap = {};
            let onCategoryChange = null;

            if (isCategorized) {
                const categoryWidget = this.widgets.find((w) => w.name === "category_select");
                const itemWidget = this.widgets.find((w) => w.name === "item_select");

                if (!categoryWidget || !itemWidget) {
                    return;
                }

                // 分类选择变化时的处理函数
                onCategoryChange = () => {
                    const selectedCategory = categoryWidget.value;

                    if (
                        selectedCategory &&
                        selectedCategory !== "无 (None)" &&
                        selectedCategory !== "随机 (Random)" &&
                        selectedCategory !== "自定义 (Custom)" &&
                        !selectedCategory.startsWith("--- ")
                    ) {
                        // 获取该分类下的原始项目列表
                        const originalItems = categoryItemMap[selectedCategory] || [];

                        // 在列表开头添加"全部"选项（用特殊格式标识）
                        const items = ["*全部* (随机)"].concat(originalItems);
                        itemWidget.options.values = items;

                        // 如果当前选中的项目不在新列表中，重置选择到"全部"
                        if (items.length > 0 && !items.includes(itemWidget.value)) {
                            itemWidget.value = items[0]; // "*全部* (随机)"
                        }

                        // 显示item_widget
                        if (itemWidget.parentEl) {
                            itemWidget.parentEl.style.display = "";
                        }
                    } else {
                        // 对于"无"、"随机"、"自定义"选项，隐藏item_widget
                        itemWidget.options.values = [];
                        itemWidget.value = "[隐藏]"; // 重置值避免验证错误

                        // 隐藏widget
                        if (itemWidget.parentEl) {
                            itemWidget.parentEl.style.display = "none";
                        }
                    }
                };

                // 初始构建分类 -> 项目映射
                categoryItemMap = buildCategoryItemMap(itemWidget.options.values);

                // 保存原始callback
                const originalCallback = categoryWidget.callback;

                // 监听category_widget变化 - 使用新的回调函数
                categoryWidget.callback = (value) => {
                    // 调用原始callback（如果有）
                    if (originalCallback) {
                        try {
                            originalCallback.call(categoryWidget, value);
                        } catch (e) {
                            // 忽略错误
                        }
                    }
                    onCategoryChange();
                };

                // 初始调用一次
                onCategoryChange();
            }

            // --- 热更新：刷新按钮 ---
            const refresh = async () => {
                try {
                    const input = await fetchFreshInput(nodeData.name);
                    applyFreshOptions(node, input.required);
                    if (isCategorized && onCategoryChange) {
                        // 选项已更新，重建分类映射并重算第二级菜单
                        const itemWidget = node.widgets.find((w) => w.name === "item_select");
                        if (itemWidget) {
                            categoryItemMap = buildCategoryItemMap(itemWidget.options.values);
                        }
                        onCategoryChange();
                    }
                    node.setDirtyCanvas(true, true);
                } catch (e) {
                    console.error("[ComfyUI_MyComfyuiTools] 刷新 JSON 失败:", e);
                }
            };

            this.addWidget("button", "🔄 刷新 JSON", null, () => {
                refresh();
            }, { serialize: false });
        };
    },
});
