"""
ComfyUI_MyComfyuiTools/图片加载器 - 节点定义

Load Image (Folder Queue):
    从指定文件夹按排序规则每次读取一张图片，读取后按开关决定「保留」或「送回收站」。
    已读过的文件会被记录，下次运行自动按排序读下一张，不会卡在同一张。
"""

import os
import sys
import time
from pathlib import Path

try:
    # 作为插件包的一部分被 ComfyUI 导入
    from . import image_loader_core as core
except ImportError:
    # 以独立模块方式导入（自测脚本场景）
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import image_loader_core as core

CATEGORY = "MyCustomNodes/Image"


class LoadImageFromFolderQueue:
    """
    文件夹队列式加载器：一次一张，读完即删（可选保留）。
    """

    CATEGORY = CATEGORY
    FUNCTION = "load"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("IMAGE", "MASK", "filename", "name_no_ext", "file_path", "remaining")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "图片文件夹绝对路径，例如 D:\\素材\\待处理",
                    "tooltip": "目标文件夹的绝对路径。可用节点上的「浏览」按钮选择。",
                }),
                "sort_by": (core.SORT_MODES, {
                    "default": "name",
                    "tooltip": "name=文件名升序；name_desc=倒序；mtime=最旧的先；mtime_desc=最新的先；random=随机",
                }),
                "after_load": (core.AFTER_LOAD_MODES, {
                    "default": "keep",
                    "tooltip": "keep=读完保留文件（进度仍会前进）；delete=读完送进系统回收站",
                }),
            },
            "optional": {
                "recursive": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否包含子文件夹里的图片",
                }),
                "reset_progress": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "置为 True 时会清空该目录的已读记录，从第一张重新开始。用完记得改回 False。",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "仅 random 排序时有效。0=每次真随机；固定数值=可复现的随机顺序",
                }),
            },
        }

    # ------------------------------------------------------------ 缓存控制
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        让每次运行队列都真正推进一步：
        值随「待读文件列表 + 已读进度」变化，因此不会误用 ComfyUI 的缓存结果。
        """
        try:
            if kwargs.get("reset_progress", False):
                # 重置模式下每次都重新执行
                return f"reset|{time.time()}"

            root = core.normalize_dir(kwargs.get("directory", ""))
            files = core.scan_images(
                root,
                recursive=bool(kwargs.get("recursive", False)),
                sort_by=kwargs.get("sort_by", "name"),
                seed=int(kwargs.get("seed", 0) or 0),
            )
            state = core.load_state(root)
            pending = core.pending_files(root, files, state)
            head = core.rel_key(root, pending[0]) if pending else "EMPTY"
            return f"{len(files)}|{len(pending)}|{head}"
        except Exception as e:
            return f"ERR|{type(e).__name__}|{e}"

    # ------------------------------------------------------------ 主逻辑
    def load(self, directory, sort_by="name", after_load="keep",
             recursive=False, reset_progress=False, seed=0):

        root = core.normalize_dir(directory)

        with core.state_lock:
            if reset_progress:
                core.reset_state(root)

            files = core.scan_images(
                root,
                recursive=bool(recursive),
                sort_by=sort_by,
                seed=int(seed or 0),
            )
            if not files:
                raise RuntimeError(
                    f"[ImageLoader] 目录内没有找到图片: {root}\n"
                    f"支持的格式: {', '.join(sorted(core.IMAGE_EXTS))}"
                )

            state = core.load_state(root)
            pending = core.pending_files(root, files, state)

            if not pending:
                raise RuntimeError(
                    f"[ImageLoader] 目录内的 {len(files)} 张图片已全部读取完，队列停止。\n"
                    f"目录: {root}\n"
                    f"如需重新开始：把 reset_progress 打开再运行一次，"
                    f"或删除目录下的 {core.STATE_FILENAME}，"
                    f"或点击节点上的「重置进度」按钮。"
                )

            target = pending[0]
            key = core.rel_key(root, target)

            # 1) 先读图，读失败就不推进进度
            try:
                image, mask = core.load_image_tensor(target)
            except Exception as e:
                raise RuntimeError(
                    f"[ImageLoader] 图片读取失败，已跳过删除以免数据丢失: {target}\n原因: {e}"
                )

            # 2) 按开关处理文件
            action = "keep"
            if after_load == "delete":
                action = core.trash_file(target, root)
                if action == "recycle_bin":
                    print(f"[ImageLoader] 已送入回收站: {target}")
                else:
                    print(f"[ImageLoader] 回收站不可用，已移动到 _trash: {target}")

            # 3) 记录进度（无论保留还是删除都前进，保证下次读到下一张）
            state.setdefault("processed", set()).add(key)
            state["last"] = {
                "file": key,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": after_load,
                "result": action,
            }
            core.save_state(root, state)

            remaining = len(pending) - 1

        filename = target.name
        stem = target.stem
        file_path = str(target)

        print(
            f"[ImageLoader] 读取第 {len(files) - remaining}/{len(files)} 张: {filename} "
            f"| 处理: {after_load}({action}) | 剩余未读: {remaining}"
        )

        # 顺序必须与 RETURN_TYPES / RETURN_NAMES 一致:
        # IMAGE, MASK, filename, name_no_ext, file_path, remaining
        return (image, mask, filename, stem, file_path, remaining)


class ConfirmDeleteImage:
    """
    收尾节点：流程跑完（图片已保存）之后再删除源文件。

    用法：把「加载图片·文件夹队列」的 file_path 接过来，放在保存节点之后。
    可设置一个「产物确认」条件——只有产物文件真的出现了才删，避免中途报错丢图。
    """

    CATEGORY = CATEGORY
    FUNCTION = "confirm_delete"
    OUTPUT_NODE = True  # 保证即使没有下游节点也会被执行
    RETURN_TYPES = ("INT", "STRING", "STRING")
    RETURN_NAMES = ("deleted_count", "deleted_paths", "status")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_paths": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "要删除的图片路径，可连线接上游 file_path；多个用换行/逗号隔开",
                    "tooltip": "通常直接接「加载图片·文件夹队列」的 file_path 输出",
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "可选。接上处理链末端的 IMAGE，确保整条流程跑完后才删",
                }),
                "enabled": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "总开关。关掉后只报告不删除，方便先空跑验证",
                }),
                "confirm_output": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "可选，产物确认：如 D:\\out\\前缀_*.png 或 D:\\out",
                    "tooltip": "填了就会先确认产物存在，不存在则跳过删除（不报错）",
                }),
                "wait_seconds": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 60,
                    "tooltip": "产物还没出现时最多等几秒（保存大图可能慢）",
                }),
                "backup_first": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "删除前先复制一份到 <源目录>/_backup/，双保险",
                }),
                "on_missing": (["skip", "error"], {
                    "default": "skip",
                    "tooltip": "源文件已不在（比如被别处删了）时的处理：skip=警告继续 / error=报错中断",
                }),
                "rollback_on_skip": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "跳过删除时，把该文件从「已读记录」里撤回，下次运行会重新读到它，不会漏处理",
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 收尾动作每次都要真正跑一遍
        return time.time()

    @staticmethod
    def _out(count, paths, status):
        """返回 ui.text，让状态直接显示在节点下方"""
        return {"ui": {"text": status.splitlines() or [status]},
                "result": (count, paths, status)}

    def confirm_delete(self, file_paths, image=None, enabled=True, confirm_output="",
                       wait_seconds=3, backup_first=False, on_missing="skip",
                       rollback_on_skip=True):

        paths = core.split_paths(file_paths)

        if not enabled:
            return self._out(0, "", "⏸ 已跳过：enabled=False，未删除任何文件")

        if not paths:
            return self._out(0, "", "⚠ 没有传入任何文件路径，未删除")

        # --- 产物确认 ---
        if (confirm_output or "").strip():
            ok = core.output_ready(confirm_output, wait_seconds)
            if not ok:
                msg = f"⚠ 未检测到产物「{confirm_output}」，已跳过删除（源文件保留）"
                print(f"[ImageLoader] {msg}")
                if rollback_on_skip:
                    n = sum(1 for s in paths if core.unmark_processed(s))
                    if n:
                        msg += f"｜已撤回 {n} 个文件的已读记录，下次会重新处理"
                return self._out(0, "", msg)

        deleted, missing, failed = [], [], []

        for raw in paths:
            p = Path(str(raw).strip().strip('"').strip("'"))
            if not p.is_file():
                missing.append(str(p))
                if on_missing == "error":
                    raise RuntimeError(f"[ImageLoader] 要删除的文件不存在: {p}")
                continue
            try:
                if backup_first:
                    dst = core.backup_file(p)
                    print(f"[ImageLoader] 已备份: {dst}")
                how = core.trash_file(p)
                deleted.append(str(p))
                print(f"[ImageLoader] 确认删除完成({how}): {p}")
            except Exception as e:
                failed.append(f"{p} -> {e}")
                print(f"[ImageLoader] 删除失败: {p} -> {e}")

        parts = [f"已删除 {len(deleted)} 个文件"]
        if missing:
            parts.append(f"{len(missing)} 个不存在（已跳过）")
        if failed:
            parts.append(f"{len(failed)} 个失败")
        status = "✅ " + "｜".join(parts) if not failed else "❌ " + "｜".join(parts) + "\n" + "\n".join(failed)

        return self._out(len(deleted), "\n".join(deleted), status)


class ImageQueueStatus:
    """辅助节点：只看某个文件夹队列的进度，不读图。"""

    CATEGORY = CATEGORY
    FUNCTION = "status"
    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("total", "remaining", "next_file", "status_text")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": "", "multiline": False}),
                "sort_by": (core.SORT_MODES, {"default": "name"}),
            },
            "optional": {
                "recursive": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time()

    def status(self, directory, sort_by="name", recursive=False, seed=0):
        root = core.normalize_dir(directory)
        files = core.scan_images(root, bool(recursive), sort_by, int(seed or 0))
        state = core.load_state(root)
        pending = core.pending_files(root, files, state)
        nxt = pending[0].name if pending else ""
        text = (
            f"共 {len(files)} 张，已读 {len(files) - len(pending)} 张，剩余 {len(pending)} 张"
            + (f"，下一张: {nxt}" if nxt else "（已全部读完）")
        )
        return (len(files), len(pending), nxt, text)


NODE_CLASS_MAPPINGS = {
    "LoadImageFromFolderQueue": LoadImageFromFolderQueue,
    "ConfirmDeleteImage": ConfirmDeleteImage,
    "ImageQueueStatus": ImageQueueStatus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromFolderQueue": "加载图片·文件夹队列 (读完可删除)",
    "ConfirmDeleteImage": "确认删除图片 (收尾)",
    "ImageQueueStatus": "图片队列进度查询",
}
