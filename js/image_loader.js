/*
 * ComfyUI_MyComfyuiTools/图片加载器 - 前端扩展
 * - directory 控件旁的「浏览文件夹」按钮
 * - 节点内显示「下一张会读到哪张图」的缩略图与剩余数量
 * - 「重置进度」「在资源管理器中打开」快捷操作
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_NAME = "LoadImageFromFolderQueue";

/* ------------------------------------------------------------ 工具 */

function getWidget(node, name) {
    return node.widgets ? node.widgets.find((w) => w.name === name) : null;
}

function jget(url) {
    return fetch(url, { cache: "no-store" }).then((r) => r.json());
}

function q(v) {
    return encodeURIComponent(v == null ? "" : String(v));
}

function nextInfoUrl(node) {
    const wDir = getWidget(node, "directory");
    const wSort = getWidget(node, "sort_by");
    const wRec = getWidget(node, "recursive");
    const wSeed = getWidget(node, "seed");
    const dir = (wDir?.value || "").trim();
    if (!dir) return null;
    return (
        `/mycomfyuitools/imageloader/next_info?directory=${q(dir)}` +
        `&sort_by=${q(wSort?.value || "name")}` +
        `&recursive=${wRec?.value ? "true" : "false"}` +
        `&seed=${q(wSeed?.value || 0)}`
    );
}

/* ------------------------------------------------------------ 预览刷新 */

function scheduleRefresh(node, delay = 250) {
    if (node.__ilTimer) clearTimeout(node.__ilTimer);
    node.__ilTimer = setTimeout(() => refreshPreview(node), delay);
}

async function refreshPreview(node) {
    const box = node.__ilPreview;
    if (!box) return;
    const img = box.__img;
    const info = box.__info;

    const url = nextInfoUrl(node);
    if (!url) {
        img.style.display = "none";
        info.textContent = "未设置目录 — 点「浏览文件夹」选择";
        info.style.color = "#c78b3c";
        return;
    }

    try {
        const data = await jget(url);
        if (!data.ok) {
            img.style.display = "none";
            info.textContent = data.error || "读取失败";
            info.style.color = "#d9534f";
            return;
        }
        if (data.done || !data.path) {
            img.style.display = "none";
            info.textContent = `✅ 已全部读完（共 ${data.total} 张）`;
            info.style.color = "#7bb661";
            return;
        }
        img.onload = () => {
            img.style.display = "block";
            node.setDirtyCanvas(true, true);
        };
        img.onerror = () => {
            img.style.display = "none";
        };
        img.src = `/mycomfyuitools/imageloader/preview?path=${q(data.path)}&t=${Date.now()}`;
        img.style.display = "block";
        info.style.color = "";
        info.textContent =
            `下一张: ${data.filename}\n` +
            `第 ${data.index} / ${data.total} 张，剩余 ${data.remaining} 张`;
    } catch (e) {
        info.textContent = "预览请求失败: " + e;
        info.style.color = "#d9534f";
    }
}

/* ------------------------------------------------------------ 文件夹选择弹窗 */

function openFolderPicker(currentPath, onPick) {
    const mask = document.createElement("div");
    mask.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:10000;" +
        "display:flex;align-items:center;justify-content:center;";

    const panel = document.createElement("div");
    panel.style.cssText =
        "background:#2a2a2a;border:1px solid #555;border-radius:8px;" +
        "width:560px;max-width:90vw;max-height:80vh;display:flex;flex-direction:column;" +
        "box-shadow:0 8px 32px rgba(0,0,0,.6);color:#e8e8e8;font-size:13px;";

    const header = document.createElement("div");
    header.style.cssText =
        "padding:10px 14px;border-bottom:1px solid #444;font-weight:600;" +
        "display:flex;justify-content:space-between;align-items:center;";
    header.textContent = "选择图片文件夹";
    const close = document.createElement("span");
    close.textContent = "✕";
    close.style.cssText = "cursor:pointer;opacity:.7;padding:0 4px;";
    close.onclick = () => mask.remove();
    header.appendChild(close);

    const pathBar = document.createElement("div");
    pathBar.style.cssText =
        "padding:8px 14px;border-bottom:1px solid #3a3a3a;display:flex;gap:6px;align-items:center;";
    const pathInput = document.createElement("input");
    pathInput.value = currentPath || "";
    pathInput.placeholder = "输入路径后回车，例如 D:\\素材";
    pathInput.style.cssText =
        "flex:1;background:#1c1c1c;border:1px solid #444;color:#e8e8e8;" +
        "border-radius:4px;padding:5px 8px;font-size:12px;";
    const upBtn = document.createElement("button");
    upBtn.textContent = "↑ 上级";
    const goBtn = document.createElement("button");
    goBtn.textContent = "转到";
    for (const b of [upBtn, goBtn]) {
        b.style.cssText =
            "background:#3a3a3a;border:1px solid #555;color:#e8e8e8;border-radius:4px;" +
            "padding:5px 10px;cursor:pointer;font-size:12px;";
    }

    const list = document.createElement("div");
    list.style.cssText = "flex:1;overflow:auto;padding:6px 8px;min-height:220px;";

    const footer = document.createElement("div");
    footer.style.cssText =
        "padding:10px 14px;border-top:1px solid #444;display:flex;justify-content:flex-end;gap:8px;";
    const pickBtn = document.createElement("button");
    pickBtn.textContent = "选择此文件夹";
    pickBtn.style.cssText =
        "background:#4a7ebb;border:none;color:#fff;border-radius:4px;" +
        "padding:6px 14px;cursor:pointer;font-weight:600;";
    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "取消";
    cancelBtn.style.cssText =
        "background:#3a3a3a;border:1px solid #555;color:#e8e8e8;border-radius:4px;" +
        "padding:6px 14px;cursor:pointer;";
    cancelBtn.onclick = () => mask.remove();

    pathBar.append(pathInput, upBtn, goBtn);
    footer.append(cancelBtn, pickBtn);
    panel.append(header, pathBar, list, footer);
    mask.appendChild(panel);
    document.body.appendChild(mask);

    let cur = currentPath || "";

    async function load(p) {
        list.innerHTML = "<div style='padding:10px;opacity:.6'>读取中…</div>";
        const res = await jget(`/mycomfyuitools/imageloader/list_dirs?path=${q(p)}`);
        if (!res.ok) {
            list.innerHTML = `<div style="padding:10px;color:#d9534f">${res.error || "读取失败"}</div>`;
            return;
        }
        cur = res.path || p || "";
        if (pathInput.value !== cur) pathInput.value = cur;

        list.innerHTML = "";
        for (const d of res.dirs || []) {
            const row = document.createElement("div");
            row.style.cssText =
                "display:flex;justify-content:space-between;align-items:center;" +
                "padding:6px 8px;border-radius:4px;cursor:pointer;";
            row.onmouseenter = () => (row.style.background = "#333");
            row.onmouseleave = () => (row.style.background = "transparent");

            const left = document.createElement("span");
            left.textContent = "📁 " + d.name;
            const right = document.createElement("span");
            right.style.opacity = ".55";
            right.textContent = d.images == null ? "" : `${d.images} 张`;

            row.append(left, right);
            row.onclick = () => load(d.path);
            row.ondblclick = () => {
                onPick(d.path);
                mask.remove();
            };
            list.appendChild(row);
        }
        if (!res.dirs || res.dirs.length === 0) {
            list.innerHTML =
                "<div style='padding:10px;opacity:.6'>（没有子文件夹，可直接选择当前目录）</div>";
        }
    }

    upBtn.onclick = async () => {
        const res = await jget(`/mycomfyuitools/imageloader/list_dirs?path=${q(cur)}`);
        if (res.ok && res.parent) load(res.parent);
        else if (cur) load("");
    };
    goBtn.onclick = () => load(pathInput.value.trim());
    pathInput.onkeydown = (e) => {
        if (e.key === "Enter") load(pathInput.value.trim());
        e.stopPropagation();
    };
    pickBtn.onclick = () => {
        onPick(pathInput.value.trim() || cur);
        mask.remove();
    };
    mask.onclick = (e) => {
        if (e.target === mask) mask.remove();
    };

    load(currentPath || "");
    pathInput.focus();
}

/* ------------------------------------------------------------ 扩展主体 */

app.registerExtension({
    name: "MyComfyuiTools.ImageLoader.Preview",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== NODE_NAME) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
            const node = this;

            /* --- 浏览按钮 --- */
            const browseBtn = node.addWidget(
                "button",
                "📁 浏览文件夹…",
                null,
                () => {
                    const wDir = getWidget(node, "directory");
                    openFolderPicker((wDir?.value || "").trim(), (p) => {
                        if (!p) return;
                        if (wDir) {
                            wDir.value = p;
                            if (wDir.callback) wDir.callback(p);
                        }
                        scheduleRefresh(node, 60);
                    });
                },
                { serialize: false }
            );

            /* --- 重置进度按钮 --- */
            const resetBtn = node.addWidget(
                "button",
                "🔄 重置进度",
                null,
                async () => {
                    const wDir = getWidget(node, "directory");
                    const dir = (wDir?.value || "").trim();
                    if (!dir) {
                        alert("请先填写或选择文件夹路径");
                        return;
                    }
                    if (!confirm(`确定清空该目录的已读记录？\n\n${dir}\n\n下次运行将从第一张重新开始。`)) {
                        return;
                    }
                    try {
                        const res = await fetch("/mycomfyuitools/imageloader/reset", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ directory: dir }),
                        }).then((x) => x.json());
                        if (!res.ok) alert("重置失败: " + (res.error || "未知错误"));
                    } catch (e) {
                        alert("重置失败: " + e);
                    }
                    scheduleRefresh(node, 60);
                },
                { serialize: false }
            );

            /* --- 预览区 --- */
            const box = document.createElement("div");
            box.style.cssText =
                "width:100%;display:flex;flex-direction:column;gap:4px;" +
                "background:rgba(0,0,0,.25);border-radius:4px;padding:6px;box-sizing:border-box;";

            const img = document.createElement("img");
            img.style.cssText =
                "width:100%;max-height:190px;object-fit:contain;display:none;" +
                "background:#111;border-radius:3px;";

            const info = document.createElement("div");
            info.style.cssText =
                "font-size:11px;line-height:1.45;white-space:pre-wrap;word-break:break-all;" +
                "color:#bbb;min-height:30px;";

            const openLink = document.createElement("span");
            openLink.textContent = "在资源管理器中打开";
            openLink.style.cssText =
                "font-size:11px;color:#5fa8e8;cursor:pointer;text-decoration:underline;align-self:flex-start;";
            openLink.onclick = async () => {
                const wDir = getWidget(node, "directory");
                const dir = (wDir?.value || "").trim();
                if (!dir) return;
                try {
                    await fetch(`/mycomfyuitools/imageloader/open_folder?path=${q(dir)}`);
                } catch (e) {
                    /* ignore */
                }
            };

            box.append(img, info, openLink);
            box.__img = img;
            box.__info = info;
            node.__ilPreview = box;

            const domWidget = node.addDOMWidget("next_preview", "div", box, {
                serialize: false,
                hideOnZoom: false,
            });
            domWidget.computeSize = () => [300, 230];

            /* --- 把按钮挪到 directory 控件后面 --- */
            const widgets = node.widgets || [];
            const dirIdx = widgets.findIndex((w) => w.name === "directory");
            if (dirIdx >= 0) {
                widgets.splice(widgets.indexOf(browseBtn), 1);
                widgets.splice(widgets.indexOf(resetBtn), 1);
                widgets.splice(dirIdx + 1, 0, browseBtn, resetBtn);
            }

            /* --- 控件变化时刷新 --- */
            for (const name of ["directory", "sort_by", "recursive", "seed"]) {
                const w = getWidget(node, name);
                if (!w) continue;
                const orig = w.callback;
                w.callback = function (...args) {
                    const out = orig ? orig.apply(this, args) : undefined;
                    scheduleRefresh(node);
                    return out;
                };
            }

            node.setSize([
                Math.max(node.size[0], 340),
                Math.max(node.size[1], 460),
            ]);

            /* --- 执行完成后刷新（文件可能已被删除，进度已前进） --- */
            node.__ilOnExecuted = (e) => {
                if (e?.detail?.node === node.id || e?.detail?.node === String(node.id)) {
                    scheduleRefresh(node, 400);
                }
            };
            api.addEventListener("executed", node.__ilOnExecuted);

            scheduleRefresh(node, 500);

            const onRemoved = node.onRemoved;
            node.onRemoved = function () {
                api.removeEventListener("executed", node.__ilOnExecuted);
                if (node.__ilTimer) clearTimeout(node.__ilTimer);
                return onRemoved ? onRemoved.apply(this, arguments) : undefined;
            };

            return r;
        };
    },
});
