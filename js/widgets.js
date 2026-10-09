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

app.registerExtension({
    name: "ComfyUI_MyComfyuiTools.CategoryItemWidget",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
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
