"""
ComfyUI_MyComfyuiTools/图片加载器 - core logic

负责: 图片扫描 / 排序 / 进度记录 / 回收站删除
不依赖 ComfyUI 与 torch，可单独测试。
"""

import ctypes
import json
import os
import random
import re
import shutil
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------- 常量

STATE_VERSION = 1
STATE_FILENAME = ".comfy_imageloader_state.json"
FALLBACK_TRASH_DIRNAME = "_trash"
BACKUP_DIRNAME = "_backup"

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".jpe", ".jfif",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tif", ".tiff",
    ".ppm", ".pgm", ".pbm",
    ".avif",
    ".heic", ".heif",
}

SORT_MODES = ["name", "name_desc", "mtime", "mtime_desc", "random"]
AFTER_LOAD_MODES = ["keep", "delete"]

# 扫描时跳过的目录名（避免把回退回收箱里的图再读一遍）
_SKIP_PARTS = {FALLBACK_TRASH_DIRNAME, "__pycache__"}

state_lock = threading.Lock()  # 防止同一目录被并发执行时读串


# ---------------------------------------------------------------- 工具

def _natural_key(s: str):
    """自然排序: img2 < img10"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]


def normalize_dir(directory) -> Path:
    """清理用户粘贴进来的路径（去引号、去首尾空白、展开 ~）"""
    if directory is None:
        raise ValueError("directory 为空，请填写图片文件夹的绝对路径")
    p = str(directory).strip().strip('"').strip("'").strip()
    p = os.path.expanduser(p)
    if not p:
        raise ValueError("directory 为空，请填写图片文件夹的绝对路径")
    root = Path(p)
    if not root.exists():
        raise ValueError(f"目录不存在: {root}")
    if not root.is_dir():
        raise ValueError(f"不是目录（请填文件夹而不是文件）: {root}")
    return root


def _is_skipped(path: Path) -> bool:
    for part in path.parts:
        if part in _SKIP_PARTS or (part.startswith(".") and len(part) > 1):
            return True
    return False


def scan_images(root: Path, recursive: bool = False, sort_by: str = "name", seed: int = 0):
    """扫描目录内图片并按指定规则排序，返回 list[Path]"""
    root = Path(root)
    walker = root.rglob("*") if recursive else root.glob("*")

    files = []
    for p in walker:
        try:
            if not p.is_file():
                continue
        except OSError:
            continue
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        if _is_skipped(p.relative_to(root)):
            continue
        files.append(p)

    if sort_by == "random":
        rng = random.Random(seed if seed else None)
        rng.shuffle(files)
        return files

    reverse = sort_by.endswith("_desc")

    if sort_by.startswith("mtime"):
        def key(p: Path):
            try:
                return (p.stat().st_mtime, _natural_key(p.name))
            except OSError:
                return (0.0, _natural_key(p.name))
        files.sort(key=key, reverse=reverse)
    else:
        files.sort(key=lambda p: _natural_key(p.name), reverse=reverse)

    return files


def rel_key(root: Path, path: Path) -> str:
    """进度记录用的相对路径键（统一为正斜杠，跨会话稳定）"""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------- 进度记录

def _state_file(root: Path) -> Path:
    return root / STATE_FILENAME


def _fallback_state_file(root: Path) -> Path:
    """源目录不可写时，退回到插件目录下的 states/"""
    here = Path(__file__).resolve().parent
    d = here / "states"
    d.mkdir(parents=True, exist_ok=True)
    digest = re.sub(r"[^0-9a-zA-Z]", "_", str(root).lower())[-80:]
    return d / f"{digest}.json"


def load_state(root: Path) -> dict:
    for f in (_state_file(root), _fallback_state_file(root)):
        try:
            if f.exists():
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return {
                        "version": STATE_VERSION,
                        "processed": set(data.get("processed", []) or []),
                        "last": data.get("last", None),
                    }
        except Exception:
            continue
    return {"version": STATE_VERSION, "processed": set(), "last": None}


def save_state(root: Path, state: dict):
    processed = sorted(state.get("processed", set()))
    payload = {
        "version": STATE_VERSION,
        "processed": processed,
        "last": state.get("last"),
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)

    for f in (_state_file(root), _fallback_state_file(root)):
        try:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            return str(f)
        except Exception:
            continue
    return None


def reset_state(root: Path) -> bool:
    removed = False
    for f in (_state_file(root), _fallback_state_file(root)):
        try:
            if f.exists():
                f.unlink()
                removed = True
        except Exception:
            continue
    return removed


def pending_files(root: Path, files, state: dict):
    """按排序结果过滤掉已处理的文件"""
    processed = state.get("processed", set())
    return [p for p in files if rel_key(root, p) not in processed]


# ---------------------------------------------------------------- 删除

def find_state_root(path) -> Path:
    """
    从文件路径向上找，返回存在进度记录文件的那个目录。
    递归模式下文件可能在子目录里，而 state 记在根目录下，所以要逐层往上找。
    """
    p = Path(path)
    try:
        for anc in [p] + list(p.parents):
            if anc.is_dir() and (anc / STATE_FILENAME).exists():
                return anc
    except Exception:
        pass
    return p.parent


def unmark_processed(path) -> bool:
    """
    把某个文件从「已读记录」里移除（下次运行会重新读到它）。
    用于收尾节点跳过删除时回滚进度，避免这张图再也不会被处理。
    """
    p = Path(path)
    root = find_state_root(p)
    state = load_state(root)
    processed = state.get("processed", set())
    if not processed:
        return False
    key = rel_key(root, p)
    hit = key in processed
    if not hit:
        # 兜底: 用文件名匹配
        for k in list(processed):
            if k.endswith("/" + p.name) or k == p.name:
                processed.discard(k)
                hit = True
    processed.discard(key)
    if hit:
        save_state(root, state)
    return hit


def backup_file(path: Path, root: Path = None):
    """删前先复制一份到 <root>/_backup/, 返回副本路径"""
    path = Path(path)
    base = Path(root) if root is not None else path.parent
    d = base / BACKUP_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    dst = d / path.name
    if dst.exists():
        dst = d / f"{path.stem}_{int(time.time())}{path.suffix}"
    shutil.copy2(str(path), str(dst))
    return dst


def output_ready(pattern, wait_seconds: float = 0.0) -> bool:
    """
    「确认」条件: 判断产物文件是否已经生成。
    支持具体路径、通配符(D:\\out\\前缀_*.png)或目录(检查目录内是否有图片)。
    """
    import glob as _glob

    pattern = (pattern or "").strip().strip('"').strip("'")
    if not pattern:
        return True

    def check() -> bool:
        if os.path.isdir(pattern):
            root = Path(pattern)
            for f in root.glob("*"):
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    return True
            return False
        for m in _glob.glob(pattern):
            if os.path.isfile(m):
                return True
        return False

    deadline = time.time() + max(0.0, float(wait_seconds or 0))
    while True:
        if check():
            return True
        if time.time() >= deadline:
            return False
        time.sleep(0.25)


def split_paths(text):
    """把多行/逗号/分号分隔的文本拆成路径列表（不会误切 Windows 盘符冒号）"""
    if not text:
        return []
    parts = re.split(r"[\r\n;,]+", str(text))
    out = []
    for s in parts:
        s = s.strip().strip('"').strip("'").strip()
        if s:
            out.append(s)
    # 去重，保持顺序
    seen = set()
    return [p for p in out if not (p.lower() in seen or seen.add(p.lower()))]


def recycle_bin_supported(path) -> bool:
    """
    判断该路径所在卷能否使用系统回收站。
    exFAT/FAT32/U盘/网络盘没有回收站，这类卷上调用 send2trash 可能被永久删除，
    因此这些情况一律改用「移动到 _trash 文件夹」的安全方案。
    """
    if os.name != "nt":
        return True  # macOS / Linux 交给 send2trash 处理
    try:
        p = Path(path)
        drive = p.drive  # 形如 'D:'，UNC 路径为空
        if not drive:
            return False
        fsname = ctypes.create_unicode_buffer(64)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive + "\\"), None, 0, None, None, None, fsname, 64
        )
        if not ok:
            return False
        return fsname.value.upper() == "NTFS"
    except Exception:
        return False


def trash_file(path: Path, root: Path = None) -> str:
    """
    删除图片，优先送系统回收站。
    返回 'recycle_bin'（已进回收站）或 'move_to_trash'（已移到 _trash 子文件夹）。
    两种方式都不行时抛异常。
    """
    path = Path(path)
    err = None

    if recycle_bin_supported(path):
        try:
            from send2trash import send2trash as _s2t
            _s2t(str(path))
        except Exception as e:
            # 实测: send2trash 在部分 Windows 11 上会误报 FileNotFoundError，
            # 但文件其实已经进了回收站，所以以「文件是否还在原处」为准。
            err = e
    else:
        err = "当前磁盘不是 NTFS（没有系统回收站），改用移动到 _trash"

    if not path.exists():
        if err is not None:
            print(f"[ImageLoader] 已移出目录（send2trash 提示: {err}）: {path.name}")
        return "recycle_bin"

    # 确实没删掉 -> 回退: 移动到 _trash 文件夹（可随时找回）
    if err is not None:
        print(f"[ImageLoader] 回收站不可用({err})，改用移动到 _trash: {path}")

    base = Path(root) if root is not None else path.parent
    trash_dir = base / FALLBACK_TRASH_DIRNAME
    try:
        trash_dir.mkdir(parents=True, exist_ok=True)
        dst = trash_dir / path.name
        if dst.exists():
            stem, suffix = path.stem, path.suffix
            dst = trash_dir / f"{stem}_{int(time.time())}{suffix}"
        shutil.move(str(path), str(dst))
        return "move_to_trash"
    except Exception as e:
        raise RuntimeError(f"删除失败（回收站与移动均不可用）: {path} -> {e}")


# ---------------------------------------------------------------- 读图

def load_image_tensor(path: Path):
    """返回 (image_tensor[1,H,W,3], mask_tensor[H,W])"""
    import numpy as np
    import torch
    from PIL import Image, ImageOps, ImageSequence

    path = Path(path)
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)

        # 动图只取第一帧
        if getattr(img, "n_frames", 1) > 1:
            try:
                img.seek(0)
            except Exception:
                pass

        has_alpha = "A" in img.getbands() or img.mode in ("RGBA", "LA", "PA")
        if has_alpha:
            try:
                mask = np.array(img.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            except Exception:
                mask = None
        else:
            mask = None

        rgb = img.convert("RGB")
        arr = np.array(rgb).astype(np.float32) / 255.0
        image = torch.from_numpy(arr)[None,]

    if mask is None:
        mask = torch.zeros((64, 64), dtype=torch.float32)

    return image, mask
