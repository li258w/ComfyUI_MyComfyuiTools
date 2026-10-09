"""
自测脚本 —— 不启动 ComfyUI 也能验证核心逻辑。

用法:
    D:\\AI\\ComfyUI_windows\\V0.7.0\\python_embeded\\python.exe selftest_image_loader.py

注意: 其中「删除」环节会真的把测试图片送进系统回收站（测试图在临时目录下，无影响）。
"""

import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_loader_core import (  # noqa: E402
    load_state, load_image_tensor, normalize_dir, pending_files,
    rel_key, reset_state, scan_images, trash_file, save_state,
)

OK = "✓"
BAD = "✗"
fails = []


def check(cond, msg):
    print(f"  {OK if cond else BAD} {msg}")
    if not cond:
        fails.append(msg)


def make_images(d: Path, n=5):
    from PIL import Image
    d.mkdir(parents=True, exist_ok=True)
    names = []
    for i in range(1, n + 1):
        p = d / f"img_{i}.png"
        Image.new("RGB", (32, 16), (i * 30 % 255, 100, 200)).save(p)
        names.append(p)
        time.sleep(0.01)
    return names


def step(root, sort_by="name", after_load="keep", recursive=False, seed=0):
    """模拟一次节点执行，返回 (filename, remaining) 或抛异常"""
    root = normalize_dir(root)
    files = scan_images(root, recursive, sort_by, seed)
    if not files:
        raise RuntimeError("目录内没有图片")
    state = load_state(root)
    pending = pending_files(root, files, state)
    if not pending:
        raise RuntimeError("已全部读完")
    target = pending[0]
    image, mask = load_image_tensor(target)
    if after_load == "delete":
        trash_file(target, root)
    state.setdefault("processed", set()).add(rel_key(root, target))
    save_state(root, state)
    return target.name, len(pending) - 1, image.shape, mask.shape


print("\n=== 1. 排序规则 ===")
tmp = Path(tempfile.mkdtemp(prefix="ILTest_"))
try:
    make_images(tmp, 5)
    f_asc = [p.name for p in scan_images(tmp, False, "name")]
    f_desc = [p.name for p in scan_images(tmp, False, "name_desc")]
    f_mt = [p.name for p in scan_images(tmp, False, "mtime")]
    f_mtd = [p.name for p in scan_images(tmp, False, "mtime_desc")]
    print("   name      :", f_asc)
    print("   name_desc :", f_desc)
    print("   mtime     :", f_mt)
    print("   mtime_desc:", f_mtd)
    check(f_asc == sorted(f_asc), "文件名升序正确")
    check(f_desc == list(reversed(f_asc)), "文件名降序正确")
    check(f_mt == f_asc, "mtime 升序 == 创建顺序")
    check(f_mtd == list(reversed(f_mt)), "mtime 降序正确")
    r1 = [p.name for p in scan_images(tmp, False, "random", seed=123)]
    r2 = [p.name for p in scan_images(tmp, False, "random", seed=123)]
    check(r1 == r2, "random 相同 seed 可复现")
    check(sorted(r1) == sorted(f_asc), "random 不丢文件")

    print("\n=== 2. 保留模式：依次推进 ===")
    got = []
    for i in range(5):
        name, rem, shape, mshape = step(tmp, "name", "keep")
        got.append((name, rem))
    print("   ", got)
    check([g[0] for g in got] == f_asc, "keep 模式依次读到全部图片")
    check(got[-1][1] == 0, "最后一张 remaining=0")
    try:
        step(tmp, "name", "keep")
        check(False, "读完后再运行应报错")
    except RuntimeError as e:
        check("已全部读完" in str(e), "读完后再运行正确报错中断")

    print("\n=== 3. 重置进度 ===")
    reset_state(tmp)
    name, rem, _, _ = step(tmp, "name", "keep")
    check(name == f_asc[0], f"重置后回到第一张 ({name})")

    print("\n=== 4. 删除模式：文件进入回收站 ===")
    reset_state(tmp)
    before = sorted(p.name for p in tmp.glob("*.png"))
    name, rem, _, _ = step(tmp, "name", "delete")
    after = sorted(p.name for p in tmp.glob("*.png"))
    print(f"    删除 {name} | 删除前 {len(before)} 张 -> 删除后 {len(after)} 张")
    check(name not in after, "被读的图片已从目录移除")
    check(len(after) == len(before) - 1, "目录内数量 -1")
    check(rem == len(after), f"remaining({rem}) 与剩余数量一致")
    name2, _, _, _ = step(tmp, "name", "delete")
    check(name2 != name, f"下一次读到新的一张 ({name2})")

    print("\n=== 5. 图片张量 ===")
    p = next(tmp.glob("*.png"))
    img, mask = load_image_tensor(p)
    check(tuple(img.shape[1:]) == (16, 32, 3) or img.shape[2] == 3,
          f"IMAGE 形状 {tuple(img.shape)} (1,H,W,3)")
    check(img.min() >= 0.0 and img.max() <= 1.0, "像素值归一化到 0~1")
    check(mask.dim() == 2, f"MASK 形状 {tuple(mask.shape)}")

    print("\n=== 6. 空目录 / 无图片 ===")
    empty = tmp / "_empty"
    empty.mkdir()
    try:
        step(empty)
        check(False, "空目录应报错")
    except RuntimeError as e:
        check("没有图片" in str(e) or "目录内没有" in str(e), "空目录正确报错")

    print("\n=== 7. 路径容错 ===")
    r = normalize_dir(f'"{tmp}"')
    check(r == tmp, "自动去掉用户粘贴的引号")
    try:
        normalize_dir(str(tmp / "不存在"))
        check(False, "不存在的路径应报错")
    except ValueError:
        check(True, "不存在的路径正确报错")

    print("\n=== 8. 节点级调用（模拟 ComfyUI 执行） ===")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import importlib
    pkg = importlib.import_module("image_loader_nodes")
    NodeCls = pkg.NODE_CLASS_MAPPINGS["LoadImageFromFolderQueue"]
    node = NodeCls()
    rt = NodeCls.RETURN_TYPES
    rn = NodeCls.RETURN_NAMES
    check(len(rt) == len(rn), f"输出数量与名称一致 ({len(rt)})")

    d2 = Path(tempfile.mkdtemp(prefix="ILNode_"))
    try:
        make_images(d2, 3)
        out1 = node.load(str(d2), "name", "keep", False, False, 0)
        check(len(out1) == len(rt), f"load() 返回 {len(out1)} 个值，与 RETURN_TYPES({len(rt)}) 匹配")
        print("     输出:", {rn[i]: (tuple(out1[i].shape) if hasattr(out1[i], "shape") else out1[i])
                             for i in range(len(rt))})
        out2 = node.load(str(d2), "name", "keep", False, False, 0)
        check(out1[2] != out2[2], f"再次运行读到下一张 ({out1[2]} -> {out2[2]})")
        check(out2[5] == 1, f"remaining=1 (实际 {out2[5]})")

        ic1 = NodeCls.IS_CHANGED(directory=str(d2), sort_by="name", after_load="keep",
                                 recursive=False, reset_progress=False, seed=0)
        out3 = node.load(str(d2), "name", "keep", False, False, 0)
        ic2 = NodeCls.IS_CHANGED(directory=str(d2), sort_by="name", after_load="keep",
                                 recursive=False, reset_progress=False, seed=0)
        check(ic1 != ic2, "IS_CHANGED 每次运行都会变化（不会被缓存跳过）")
        try:
            node.load(str(d2), "name", "keep", False, False, 0)
            check(False, "读完后应报错中断")
        except RuntimeError:
            check(True, "读完后报错中断队列")
        # delete 模式
        node.load(str(d2), "name", "keep", False, True, 0)  # reset
        before_n = len(list(d2.glob("*.png")))
        node.load(str(d2), "name", "delete", False, False, 0)
        check(len(list(d2.glob("*.png"))) == before_n - 1, "delete 模式文件被移出目录")
    finally:
        shutil.rmtree(d2, ignore_errors=True)

    print("\n=== 9. 收尾节点：确认删除 ===")
    d3 = Path(tempfile.mkdtemp(prefix="ILDel_"))
    try:
        make_images(d3, 3)
        Del = pkg.NODE_CLASS_MAPPINGS["ConfirmDeleteImage"]
        dnode = Del()
        check(Del.OUTPUT_NODE is True, "收尾节点标记为 OUTPUT_NODE（无下游也会执行）")
        check(len(Del.RETURN_TYPES) == len(Del.RETURN_NAMES), "输出数量与名称一致")

        def call(*a, **kw):
            r = dnode.confirm_delete(*a, **kw)
            return (r["result"], r) if isinstance(r, dict) else (r, {})

        # 9.1 开关关闭时不删
        p1 = str(sorted(d3.glob("*.png"))[0])
        out, _ = call(p1, enabled=False)
        check(out[0] == 0 and Path(p1).exists(), "enabled=False 时不删除")

        # 9.2 产物未生成 -> 跳过删除 + 回滚进度
        reset_state(normalize_dir(d3))
        first = node.load(str(d3), "name", "keep", False, False, 0)
        fp = first[4]  # RETURN_NAMES[4] = file_path
        out, _ = call(fp, confirm_output=str(d3 / "没有这个产物.png"), wait_seconds=0)
        check(out[0] == 0 and Path(fp).exists(), "产物未生成时跳过删除，源文件保留")
        check("已撤回" in out[2], f"跳过时回滚了已读记录 -> {out[2][:38]}")
        again = node.load(str(d3), "name", "keep", False, False, 0)
        check(again[2] == Path(fp).name, f"回滚后重新读到同一张 ({again[2]})")

        # 9.3 产物已生成 -> 真的删除（并先备份）
        out, raw = call(fp, confirm_output=fp, wait_seconds=0, backup_first=True)
        check(out[0] == 1 and not Path(fp).exists(), "产物存在时正常删除")
        check((d3 / "_backup").is_dir() and any((d3 / "_backup").iterdir()),
              "backup_first 生成了备份副本")
        check("ui" in raw and "text" in raw["ui"], "返回 ui.text（状态会显示在节点上）")

        # 9.4 批量 + 跳过不存在的文件
        rest = [str(p) for p in sorted(d3.glob("*.png"))]
        out, _ = call("\n".join(rest + [str(d3 / "ghost.png")]), on_missing="skip")
        check(out[0] == len(rest), f"批量删除 {len(rest)} 个并跳过不存在的 1 个 -> {out[2][:36]}")
        try:
            call(str(d3 / "ghost.png"), on_missing="error")
            check(False, "on_missing=error 应报错")
        except RuntimeError:
            check(True, "on_missing=error 正确报错中断")

        print("\n=== 10. 路径拆分 / 产物确认 ===")
        from image_loader_core import output_ready as oready, split_paths as sp
        check(sp("a.png;b.png\nc.png") == ["a.png", "b.png", "c.png"], "支持分号/换行分隔")
        check(sp(r"C:\x\a.png") == [r"C:\x\a.png"], "不会误切 Windows 盘符冒号")
        check(oready(fp, 0) is False, "已删除的文件 -> 产物确认失败")
        check(oready(str(d3 / "_backup"), 0) is True, "填目录时检查目录内是否有图片")
    finally:
        shutil.rmtree(d3, ignore_errors=True)

finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n" + "=" * 46)
if fails:
    print(f"{BAD} 失败 {len(fails)} 项:")
    for f in fails:
        print("   -", f)
    sys.exit(1)
print(f"{OK} 全部通过")
