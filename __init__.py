from .selector_nodes import (
    StyleSelector, ClothingSelector, PoseSelector,
    HairstylesSelector, EyeColorsSelector, BackgroundSelector, 
    BodyTypesSelector, PlaceSelector, HairColorSelector, PhotoTypeSelector,
    CompositionSelector,
    StringJoiner
)

# 【已移除 WEB_DIRECTORY = "./js"】

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
    "StringJoiner": "String Joiner",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']