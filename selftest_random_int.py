# -*- coding: utf-8 -*-
"""RandomIntSelector 自测脚本（无需启动 ComfyUI）

运行：python selftest_random_int.py
"""

import sys

from random_int_nodes import (
    RandomIntSelector,
    MODE_RANDOM,
    MODE_SEQUENCE,
    MODE_FIXED,
    SEQ_END_LOOP,
    SEQ_END_HOLD,
)

PASS = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} {detail}")
        sys.exit(1)


def run(mode, lo, hi, **kw):
    node = RandomIntSelector()
    return node.get_value(mode, lo, hi, **kw)["result"]


print("\n=== 1. 随机模式 ===")
vals = [run(MODE_RANDOM, 1, 6, seed=0)[0] for _ in range(2000)]
check("2000 次取值全部落在 [1,6]", all(1 <= v <= 6 for v in vals))
check("六个数字都出现过", set(vals) == {1, 2, 3, 4, 5, 6}, f"实际: {sorted(set(vals))}")

a = run(MODE_RANDOM, 1, 100, seed=42)[0]
b = run(MODE_RANDOM, 1, 100, seed=42)[0]
c = run(MODE_RANDOM, 1, 100, seed=43)[0]
check("同一 seed 结果可复现", a == b, f"{a} != {b}")
print(f"       seed=42 -> {a}, seed=43 -> {c}")

print("\n=== 2. 顺序模式：1~6 步长 1 ===")
node = RandomIntSelector()
seq = [node.get_value(MODE_SEQUENCE, 1, 6, step=1, unique_id="A")["result"][0]
       for _ in range(9)]
check("序列为 1→6 后循环回 1", seq == [1, 2, 3, 4, 5, 6, 1, 2, 3], f"实际: {seq}")

print("\n=== 3. 顺序模式：12~18 步长 2 ===")
node2 = RandomIntSelector()
seq2 = [node2.get_value(MODE_SEQUENCE, 12, 18, step=2, unique_id="B")["result"][0]
        for _ in range(6)]
check("序列为 12,14,16,18 后循环", seq2 == [12, 14, 16, 18, 12, 14], f"实际: {seq2}")

print("\n=== 4. 顺序模式：到尾行为 = 停在最大值 ===")
node3 = RandomIntSelector()
seq3 = [node3.get_value(MODE_SEQUENCE, 1, 3, step=1, on_end=SEQ_END_HOLD,
                        unique_id="C")["result"][0] for _ in range(6)]
check("序列为 1,2,3,3,3,3", seq3 == [1, 2, 3, 3, 3, 3], f"实际: {seq3}")

print("\n=== 5. 顺序模式：reset_sequence 重置 ===")
node4 = RandomIntSelector()
s = [node4.get_value(MODE_SEQUENCE, 1, 5, step=1, unique_id="D")["result"][0]
     for _ in range(3)]
after_reset = node4.get_value(MODE_SEQUENCE, 1, 5, step=1, reset_sequence=True,
                              unique_id="D")["result"][0]
check("重置前走到 3", s == [1, 2, 3], f"实际: {s}")
check("勾选重置后回到最小值 1", after_reset == 1, f"实际: {after_reset}")

print("\n=== 6. 多个节点实例互不干扰（unique_id 隔离） ===")
n1, n2 = RandomInterleaved = RandomIntSelector(), RandomIntSelector()
out1 = [n1.get_value(MODE_SEQUENCE, 1, 4, step=1, unique_id="node-1")["result"][0]
        for _ in range(3)]
out2 = [n2.get_value(MODE_SEQUENCE, 10, 12, step=1, unique_id="node-2")["result"][0]
        for _ in range(3)]
check("实例1 独立走 1,2,3", out1 == [1, 2, 3], f"实际: {out1}")
check("实例2 独立走 10,11,12", out2 == [10, 11, 12], f"实际: {out2}")

print("\n=== 7. 固定模式 ===")
check("固定值在范围内原样输出", run(MODE_FIXED, 1, 6, fixed_value=4)[0] == 4)
check("固定值超出上限被夹到 6", run(MODE_FIXED, 1, 6, fixed_value=99)[0] == 6)
check("固定值低于下限被夹到 1", run(MODE_FIXED, 1, 6, fixed_value=-5)[0] == 1)

print("\n=== 8. 边界处理 ===")
check("最小值 > 最大值时自动交换", run(MODE_FIXED, 18, 12, fixed_value=15)[0] == 15)
check("范围退化为单点时输出该点", run(MODE_RANDOM, 7, 7, seed=1)[0] == 7)
check("步长为 0 时兜底为 1", run(MODE_SEQUENCE, 1, 3, step=0, unique_id="E")[0] == 1)

print("\n=== 9. 输出类型 ===")
r = run(MODE_FIXED, 1, 6, fixed_value=3)
check("三路输出类型正确",
      isinstance(r[0], int) and isinstance(r[1], float) and isinstance(r[2], str),
      f"实际: {[type(x).__name__ for x in r]}")
check("三路数值一致", r == (3, 3.0, "3"), f"实际: {r}")

print("\n=== 10. IS_CHANGED 缓存策略 ===")
RandomIntSelector._SEQ_STATE.clear()
RandomIntSelector._SEQ_SPEC.clear()
check("固定模式签名稳定（可命中缓存）",
      RandomIntSelector.IS_CHANGED(mode=MODE_FIXED, fixed_value=3)
      == RandomIntSelector.IS_CHANGED(mode=MODE_FIXED, fixed_value=3))
check("随机模式签名每次不同（强制重算）",
      RandomIntSelector.IS_CHANGED(mode=MODE_RANDOM, seed=0)
      != RandomIntSelector.IS_CHANGED(mode=MODE_RANDOM, seed=0))
check("顺序模式签名每次不同（强制递增）",
      RandomIntSelector.IS_CHANGED(mode=MODE_SEQUENCE)
      != RandomIntSelector.IS_CHANGED(mode=MODE_SEQUENCE))

print(f"\n{'='*46}")
print(f"全部 {len(PASS)} 项检查通过 ✓")
print(f"{'='*46}\n")
