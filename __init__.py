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


_register_refresh_route()

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
