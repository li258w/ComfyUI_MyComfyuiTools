// ComfyUI自定义widget实现分类和项目的联动下拉菜单
import { app } from "../../../scripts/app.js";

// 扩展ClothingSelector和CompositionSelector节点（双级下拉菜单联动）
app.registerExtension({
    name: "ComfyUI_MyComfyuiTools.CategoryItemWidget",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 处理ClothingSelector、CompositionSelector、PoseSelector和ShoesSelector节点
        if (nodeData.name !== "JsonClothingSelector" && nodeData.name !== "JsonCompositionSelector" && nodeData.name !== "JsonPoseSelector" && nodeData.name !== "JsonShoesSelector") {
            return;
        }

        // 保存原始的onNodeCreated
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function() {
            // 调用原始方法
            if (originalOnNodeCreated) {
                originalOnNodeCreated.apply(this);
            }

            // 获取widgets
            const categoryWidget = this.widgets.find(w => w.name === "category_select");
            const itemWidget = this.widgets.find(w => w.name === "item_select");

            if (!categoryWidget || !itemWidget) {
                return;
            }

            // 存储所有项目的映射（分类 -> 项目列表）
            const categoryItemMap = {};

            // 从item_widget的options中提取分类信息
            // item_widget的options格式为 ["--- 分类 ---", "项目1", "项目2", ...]
            let currentCategory = null;
            for (const option of itemWidget.options.values) {
                if (typeof option === 'string' && option.startsWith("--- ")) {
                    // 分类标题行
                    currentCategory = option.replace("--- ", "").replace(" ---", "");
                    categoryItemMap[currentCategory] = [];
                } else if (currentCategory) {
                    // 跳过"*全部* (随机)"选项，它将在前端动态添加
                    if (option === "*全部* (随机)") {
                        continue;
                    }
                    // 项目
                    categoryItemMap[currentCategory].push(option);
                }
            }

            // 分类选择变化时的处理函数
            const onCategoryChange = () => {
                const selectedCategory = categoryWidget.value;

                if (selectedCategory && selectedCategory !== "无 (None)" &&
                    selectedCategory !== "随机 (Random)" &&
                    selectedCategory !== "自定义 (Custom)" &&
                    !selectedCategory.startsWith("--- ")) {

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
                        itemWidget.parentEl.style.display = '';
                    }
                } else {
                    // 对于"无"、"随机"、"自定义"选项，隐藏item_widget
                    itemWidget.options.values = [];
                    itemWidget.value = "[隐藏]"; // 重置值避免验证错误

                    // 隐藏widget
                    if (itemWidget.parentEl) {
                        itemWidget.parentEl.style.display = 'none';
                    }
                }
            };

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
        };
    }
});