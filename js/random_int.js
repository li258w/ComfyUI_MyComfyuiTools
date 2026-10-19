// RandomIntSelector：按取值模式显示对应控件，无关的直接藏起来
//   随机 → 最小值 / 最大值 / seed
//   顺序 → 最小值 / 最大值 / 步长 / 重置序列 / 到尾行为
//   固定 → 最小值 / 最大值 / 固定值
import { app } from "../../../scripts/app.js";

const RANDOM_INT_NODES = ["RandomIntSelector"];

const MODE_RANDOM = "随机 (Random)";
const MODE_SEQUENCE = "顺序 (Sequential)";
const MODE_FIXED = "固定 (Fixed)";

const MODE_VISIBLE = {
    [MODE_RANDOM]: ["min_value", "max_value", "seed"],
    [MODE_SEQUENCE]: ["min_value", "max_value", "step", "reset_sequence", "on_end"],
    [MODE_FIXED]: ["min_value", "max_value", "fixed_value"],
};

// 受模式控制的所有 widget，其余（如按钮）不受影响
const MODE_CONTROLLED = [
    "min_value", "max_value", "step", "fixed_value", "seed",
    "reset_sequence", "on_end",
];

function applyModeVisibility(node, mode) {
    const allow = MODE_VISIBLE[mode] || MODE_VISIBLE[MODE_RANDOM];
    for (const w of node.widgets || []) {
        if (!MODE_CONTROLLED.includes(w.name)) continue;
        const show = allow.includes(w.name);
        const display = show ? "" : "none";
        if (w.parentEl) w.parentEl.style.display = display;
        else if (w.element) w.element.style.display = display;
    }
    // 重新量一次高度，否则节点会留一大块空白
    try {
        const sz = node.computeSize();
        node.setSize([Math.max(node.size[0], sz[0]), sz[1]]);
    } catch (e) {
        /* 尺寸计算失败不影响功能 */
    }
    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "ComfyUI_MyComfyuiTools.RandomIntWidget",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (!RANDOM_INT_NODES.includes(nodeData.name)) return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (originalOnNodeCreated) originalOnNodeCreated.apply(this, arguments);

            const node = this;
            const modeWidget = (node.widgets || []).find((w) => w.name === "mode");
            if (!modeWidget) return;

            const originalCallback = modeWidget.callback;
            modeWidget.callback = function (value) {
                if (originalCallback) {
                    try {
                        originalCallback.call(this, value);
                    } catch (e) {
                        /* 忽略原始回调异常 */
                    }
                }
                applyModeVisibility(node, modeWidget.value ?? value);
            };

            // DOM 可能还没挂上，等两帧再应用一次
            requestAnimationFrame(() => requestAnimationFrame(() => {
                applyModeVisibility(node, modeWidget.value);
            }));
        };
    },
});
