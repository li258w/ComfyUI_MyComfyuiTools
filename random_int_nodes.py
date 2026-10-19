# -*- coding: utf-8 -*-
"""随机整数节点（v2.6 新增）

一个节点覆盖三种取值方式，输出的一定是整数：

* **随机** —— 在 [最小值, 最大值] 里随机取一个整数。
  seed = 0 时每次都换；seed 固定则同一 seed 永远得到同一个数（可复现）。
* **顺序** —— 从最小值开始按步长递增：1→2→3…→最大值，到头之后按
  「到尾行为」处理（循环回最小值 / 一直停在最大值）。
* **固定** —— 直接指定范围内的一个整数，等于一个可随手改的数值常量。

两个关键设计：

1. **顺序模式要跨执行记忆。** 状态存在类级字典里，用节点的 ``unique_id``
   （ComfyUI 的 hidden 输入）做 key，所以同一个工作流里放多个本节点
   互不干扰；拿不到 unique_id 时退回全局 key。
2. **必须打破 ComfyUI 的执行缓存。** ComfyUI 在输入没变时会直接复用上次
   的输出，那样顺序模式会永远停在第一个值、seed=0 的随机也只会摇一次。
   所以 IS_CHANGED 对「随机 / 顺序」返回单调递增的计数器（缓存签名永不
   相同 → 每次都真的执行）；「固定」模式返回输入指纹，正常吃缓存。
"""

import itertools
import random

# --- 取值模式 ---
MODE_RANDOM = "随机 (Random)"
MODE_SEQUENCE = "顺序 (Sequential)"
MODE_FIXED = "固定 (Fixed)"
SELECT_MODES = [MODE_RANDOM, MODE_SEQUENCE, MODE_FIXED]

# --- 顺序模式走到最大值之后怎么办 ---
SEQ_END_LOOP = "循环 (Loop)"
SEQ_END_HOLD = "停在最大值 (Hold)"
SEQ_END_OPTIONS = [SEQ_END_LOOP, SEQ_END_HOLD]

# 数值上下限：±21 亿，够日常用，又不至于把滑块拉得没法点
INT_LIMIT = 0x7FFFFFFF


class RandomIntSelector:
    """随机 / 顺序 / 固定 三合一的整数取值节点"""

    # 顺序模式的状态：{节点 key: 下一个待输出的值}
    _SEQ_STATE = {}
    # 上一次的参数组合：{节点 key: (lo, hi, step, hold)}，参数一变就自动从头开始
    _SEQ_SPEC = {}
    # IS_CHANGED 用的单调计数器，保证「随机 / 顺序」每次的缓存签名都不同
    _COUNTER = itertools.count()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (SELECT_MODES, {"default": MODE_RANDOM}),
                "min_value": ("INT", {
                    "default": 1, "min": -INT_LIMIT, "max": INT_LIMIT, "step": 1,
                }),
                "max_value": ("INT", {
                    "default": 6, "min": -INT_LIMIT, "max": INT_LIMIT, "step": 1,
                }),
                # 顺序模式的步长
                "step": ("INT", {
                    "default": 1, "min": 1, "max": INT_LIMIT, "step": 1,
                }),
                # 固定模式的值
                "fixed_value": ("INT", {
                    "default": 1, "min": -INT_LIMIT, "max": INT_LIMIT, "step": 1,
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                }),
            },
            "optional": {
                # 顺序模式专属：勾上一次跑一次，序列立刻回到最小值
                "reset_sequence": ("BOOLEAN", {"default": False}),
                # 顺序走到最大值之后：循环回最小值 / 一直停在最大值
                "on_end": (SEQ_END_OPTIONS, {"default": SEQ_END_LOOP}),
            },
            # unique_id 用来隔离不同节点实例的顺序状态
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING")
    RETURN_NAMES = ("int", "float", "string")
    FUNCTION = "get_value"
    CATEGORY = "MyCustomNodes/Utils"

    # ---------- 工具 ----------

    @staticmethod
    def _to_int(value, fallback=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    @classmethod
    def _normalize_range(cls, min_value, max_value):
        """规整成 (lo, hi)。最小值填得比最大值大时自动交换，省得报错。"""
        lo = cls._to_int(min_value, 0)
        hi = cls._to_int(max_value, lo)
        if lo > hi:
            lo, hi = hi, lo
        return lo, hi

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))

    # ---------- 顺序模式 ----------

    def _seq_next(self, key, lo, hi, step, reset, hold_at_end):
        """取出当前值，并把内部指针推到下一个。

        reset 为 True 时本次直接输出最小值；参数组合（lo/hi/step/到尾行为）
        与上几次不同时也自动从最小值重来。
        """
        spec = (lo, hi, step, hold_at_end)
        if reset or key not in self._SEQ_STATE or self._SEQ_SPEC.get(key) != spec:
            value = lo
        else:
            value = self._clamp(self._to_int(self._SEQ_STATE.get(key), lo), lo, hi)

        nxt = value + step
        if nxt > hi:
            # 到头了：要么停在最大值，要么绕回最小值
            nxt = hi if hold_at_end else lo

        self._SEQ_STATE[key] = nxt
        self._SEQ_SPEC[key] = spec
        return value

    # ---------- 主逻辑 ----------

    def get_value(self, mode, min_value, max_value, step=1, fixed_value=0, seed=0,
                  reset_sequence=False, on_end=SEQ_END_LOOP, unique_id=None):
        lo, hi = self._normalize_range(min_value, max_value)

        if mode == MODE_FIXED:
            value = self._clamp(self._to_int(fixed_value, lo), lo, hi)
        elif mode == MODE_SEQUENCE:
            step = max(1, self._to_int(step, 1))
            key = str(unique_id) if unique_id is not None else "_global"
            value = self._seq_next(key, lo, hi, step,
                                   bool(reset_sequence), on_end == SEQ_END_HOLD)
        else:
            # seed=0 → 真随机；seed 固定 → 用局部随机实例，同 seed 结果稳定可复现
            rng = random.Random(seed) if seed else random
            value = rng.randint(lo, hi)

        # ui.text 会把当前值直接显示到节点上，跑完一眼能看到摇到几
        return {
            "ui": {"text": [str(value)]},
            "result": (value, float(value), str(value)),
        }

    @classmethod
    def IS_CHANGED(s, **kwargs):
        # 「固定」模式：输入不变则输出不变，正常走缓存即可
        if kwargs.get("mode") == MODE_FIXED:
            try:
                return repr(sorted(kwargs.items(), key=lambda kv: kv[0]))
            except Exception:
                return True
        # 「随机 / 顺序」：签名每次都不同 → 缓存必然失效 → 每次都真正执行
        return next(s._COUNTER)


NODE_CLASS_MAPPINGS = {
    "RandomIntSelector": RandomIntSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RandomIntSelector": "Random Int (随机整数)",
}
