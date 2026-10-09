from .selector_nodes import (
    StyleSelector, ClothingSelector, PoseSelector,
    HairstylesSelector, EyeColorsSelector, BackgroundSelector,
    BodyTypesSelector, PlaceSelector, HairColorSelector, PhotoTypeSelector,
    CompositionSelector,
    ShoesSelector,
    ExpressionSelector,
    StringJoiner,
    serialize_input_types
)

# --- 图片加载器模块（v2.5 新增）：文件夹队列读图 + 确认后删除 ---
from .image_loader_nodes import (
    NODE_CLASS_MAPPINGS as _IMAGE_LOADER_NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as _IMAGE_LOADER_NODE_DISPLAY_NAME_MAPPINGS,
)

WEB_DIRECTORY = "./js"

# 注册所有节点类
NODE_CLASS_MAPPINGS = {
    "JsonStyleSelector": StyleSelector,
    "JsonClothingSelector": ClothingSelector,
    "JsonPoseSelector": PoseSelector,
    "JsonHairstylesSelector": HairstylesSelector,
    "JsonEyeColorsSelector": EyeColorsSelector,
    "JsonBackgroundSelector": BackgroundSelector,
    "JsonBodyTypesSelector": BodyTypesSelector,
    "JsonPlaceSelector": PlaceSelector,
    "JsonHairColorSelector": HairColorSelector,
    "JsonPhotoTypeSelector": PhotoTypeSelector,
    "JsonCompositionSelector": CompositionSelector,
    "JsonShoesSelector": ShoesSelector,
    "JsonExpressionSelector": ExpressionSelector,
    "StringJoiner": StringJoiner,
}

# 注册节点的显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "JsonStyleSelector": "Style Selector",
    "JsonClothingSelector": "Clothing Selector",
    "JsonPoseSelector": "Pose Selector",
    "JsonHairstylesSelector": "Hairstyles Selector",
    "JsonEyeColorsSelector": "Eye Colors Selector",
    "JsonBackgroundSelector": "Background Selector",
    "JsonBodyTypesSelector": "Body Types Selector",
    "JsonPlaceSelector": "Place Selector",
    "JsonHairColorSelector": "Hair Color Selector",
    "JsonPhotoTypeSelector": "Photo Type Selector",
    "JsonCompositionSelector": "Composition Selector",
    "JsonShoesSelector": "Shoes Selector",
    "JsonExpressionSelector": "Expression Selector",
    "StringJoiner": "String Joiner",
}

# 合并图片加载器的节点（加载图片·文件夹队列 / 确认删除图片 / 图片队列进度查询）
NODE_CLASS_MAPPINGS.update(_IMAGE_LOADER_NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(_IMAGE_LOADER_NODE_DISPLAY_NAME_MAPPINGS)


# --- 热更新接口 ---
# 前端"刷新"按钮会调用此接口：清空 JSON 缓存，并返回该节点最新的下拉菜单选项。
# 由于 INPUT_TYPES() 会重新读取（带 mtime 指纹校验的）JSON，
# 修改 json/ 下的文件后点一下刷新即可生效，无需重启 ComfyUI。
def _register_refresh_route():
    try:
        from server import PromptServer
        from aiohttp import web
    except Exception as e:
        print(f"[ComfyUI_MyComfyuiTools] 热更新接口未启用（依赖缺失）: {e}")
        return

    server = getattr(PromptServer, "instance", None)
    if server is None:
        print("[ComfyUI_MyComfyuiTools] 热更新接口未启用（PromptServer 未就绪）")
        return

    @server.routes.post("/mycomfyuitools/refresh")
    async def refresh_json_cache(request):
        from .selector_nodes import BaseJsonSelector

        node_class_name = None
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                node_class_name = payload.get("node_class")
        except Exception:
            pass

        # 清空缓存：下一次读取会按文件指纹自动重新加载最新内容
        BaseJsonSelector.clear_json_cache()

        result = {"ok": True}
        if node_class_name:
            cls = NODE_CLASS_MAPPINGS.get(node_class_name)
            if cls is None:
                result["ok"] = False
                result["error"] = f"unknown node_class: {node_class_name}"
            else:
                try:
                    result["input"] = serialize_input_types(cls)
                except Exception as e:
                    result["ok"] = False
                    result["error"] = str(e)
        return web.json_response(result)


# --- 图片加载器的 HTTP 接口 ---
# 供 js/image_loader.js 使用：
#   GET  /mycomfyuitools/imageloader/list_dirs   浏览文件夹
#   GET  /mycomfyuitools/imageloader/next_info   下一张信息 + 队列进度
#   GET  /mycomfyuitools/imageloader/preview     读磁盘图片（节点缩略图）
#   POST /mycomfyuitools/imageloader/reset       清空已读进度
#   GET  /mycomfyuitools/imageloader/open_folder 在资源管理器中打开
def _register_image_loader_routes():
    try:
        import mimetypes
        import os
        import subprocess
        from pathlib import Path

        from aiohttp import web
        from server import PromptServer

        from . import image_loader_core as core
    except Exception as e:
        print(f"[ComfyUI_MyComfyuiTools] 图片加载器接口未启用（依赖缺失）: {e}")
        return

    server = getattr(PromptServer, "instance", None)
    if server is None:
        print("[ComfyUI_MyComfyuiTools] 图片加载器接口未启用（PromptServer 未就绪）")
        return

    routes = server.routes

    def _json(data, status=200):
        return web.json_response(data, status=status)

    def _clean_path(v, default=""):
        if v is None:
            return default
        return str(v).strip().strip('"').strip("'").strip()

    @routes.get("/mycomfyuitools/imageloader/list_dirs")
    async def api_list_dirs(request):
        """列出子目录，供前端文件夹浏览按钮使用"""
        raw = _clean_path(request.query.get("path", ""))

        try:
            if not raw:
                drives = []
                for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    d = f"{c}:\\"
                    if os.path.exists(d):
                        drives.append({"name": d, "path": d, "images": None})
                return _json({"ok": True, "path": "", "parent": None, "dirs": drives})

            root = Path(raw)
            if not root.exists():
                return _json({"ok": False, "error": f"路径不存在: {root}"})
            if not root.is_dir():
                root = root.parent

            dirs = []
            try:
                for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                    if not entry.is_dir():
                        continue
                    name = entry.name
                    if name.startswith(".") or name in ("$Recycle.Bin", "System Volume Information"):
                        continue
                    try:
                        n = sum(
                            1 for f in entry.iterdir()
                            if f.is_file() and f.suffix.lower() in core.IMAGE_EXTS
                        )
                    except Exception:
                        n = None
                    dirs.append({"name": name, "path": str(entry), "images": n})
            except Exception as e:
                return _json({"ok": False, "error": f"无法读取目录: {e}"})

            parent = str(root.parent) if root.parent != root else None
            return _json({"ok": True, "path": str(root), "parent": parent, "dirs": dirs})
        except Exception as e:
            return _json({"ok": False, "error": str(e)})

    @routes.post("/mycomfyuitools/imageloader/reset")
    async def api_reset(request):
        """清空某个目录的已读进度"""
        try:
            data = await request.json()
        except Exception:
            data = {}
        raw = _clean_path(data.get("directory", ""))
        if not raw:
            return _json({"ok": False, "error": "directory 为空"})
        try:
            root = core.normalize_dir(raw)
            removed = core.reset_state(root)
            return _json({"ok": True, "reset": removed, "directory": str(root)})
        except Exception as e:
            return _json({"ok": False, "error": str(e)})

    @routes.get("/mycomfyuitools/imageloader/next_info")
    async def api_next_info(request):
        """返回「下一张会读到的图片」信息 + 队列进度"""
        raw = _clean_path(request.query.get("directory", ""))
        sort_by = request.query.get("sort_by", "name")
        recursive = request.query.get("recursive", "false").lower() in ("1", "true", "yes")
        try:
            seed = int(request.query.get("seed", 0) or 0)
        except Exception:
            seed = 0

        if not raw:
            return _json({"ok": False, "error": "directory 为空"})

        try:
            root = core.normalize_dir(raw)
            files = core.scan_images(root, recursive, sort_by, seed)
            state = core.load_state(root)
            pending = core.pending_files(root, files, state)
            if not pending:
                return _json({
                    "ok": True,
                    "path": "",
                    "filename": "",
                    "total": len(files),
                    "remaining": 0,
                    "done": True,
                })
            nxt = pending[0]
            return _json({
                "ok": True,
                "path": str(nxt),
                "filename": nxt.name,
                "total": len(files),
                "remaining": len(pending),
                "index": len(files) - len(pending) + 1,
                "done": False,
            })
        except Exception as e:
            return _json({"ok": False, "error": str(e)})

    @routes.get("/mycomfyuitools/imageloader/open_folder")
    async def api_open_folder(request):
        """在 Windows 资源管理器中打开该目录"""
        raw = _clean_path(request.query.get("path", ""))
        if not raw:
            return _json({"ok": False, "error": "path 为空"})
        try:
            p = Path(raw)
            target = str(p if p.is_dir() else p.parent)
            if os.name == "nt":
                os.startfile(target)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", target])
            return _json({"ok": True, "opened": target})
        except Exception as e:
            return _json({"ok": False, "error": str(e)})

    @routes.get("/mycomfyuitools/imageloader/preview")
    async def api_preview(request):
        """返回磁盘上任意路径的图片（用于节点缩略图）"""
        raw = _clean_path(request.query.get("path", ""))
        if not raw:
            return web.Response(status=404)
        p = Path(raw)
        if not p.is_file():
            return web.Response(status=404)
        try:
            ctype = mimetypes.guess_type(p.name)[0] or "image/png"
            data = p.read_bytes()
            return web.Response(body=data, content_type=ctype,
                                headers={"Cache-Control": "no-store"})
        except Exception:
            return web.Response(status=500)


_register_refresh_route()
_register_image_loader_routes()

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
