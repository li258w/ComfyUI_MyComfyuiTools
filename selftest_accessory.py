"""
自测脚本 —— 不启动 ComfyUI 也能验证 Accessory Selector 核心逻辑。

用法:
    D:\\AI\\ComfyUI_windows\\V0.7.0\\python_embeded\\python.exe selftest_accessory.py
    （任意 Python 3.8+ 均可，无第三方依赖）

覆盖:
    INPUT_TYPES 结构（9 部位下拉 / 参数名固定 / 选项与默认值 / 刷新接口可序列化）
    三点位同时佩戴与拼接顺序、prefix 连接、全空选、extra_text 追加与原文透传、
    随机（同 seed 稳定 / 部位间互不干扰 / 池内只有本部位）、
    output_mode 三种模式、旧工作流失效条目兜底、9 部位同时佩戴
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from selector_nodes import AccessorySelector, serialize_input_types  # noqa: E402

OK = "PASS"
BAD = "FAIL"
fails = []


def check(name, cond, extra=""):
    print("%s %s%s" % (OK if cond else BAD, name, (" | " + str(extra)) if extra else ""))
    if not cond:
        fails.append(name)


# ---------- 1. INPUT_TYPES 结构 ----------
spec = AccessorySelector.INPUT_TYPES()
req = spec["required"]
slots = AccessorySelector._accessory_slots()
check("部位下拉数量=9", len(slots) == 9, slots)
check("部位顺序", [p for _, p in slots] == ["帽子", "发饰", "耳饰", "颈饰", "面部", "手部", "腕饰", "腰饰", "踝饰"])
check("参数名固定英文", [n for n, _ in slots] == ["hat", "hair_ornament", "earring", "necklace", "face", "hand", "wrist", "waist", "ankle"])
for n, _ in slots:
    opts = req[n][0]
    check("%s 下拉含无/随机+条目" % n, opts[0] == "无 (None)" and opts[1] == "随机 (Random)" and len(opts) >= 4, len(opts))
    check("%s 默认无" % n, req[n][1]["default"] == "无 (None)")
check("序列化可 JSON 化(刷新接口用)", json.dumps(serialize_input_types(AccessorySelector))[:1] == "{")

node = AccessorySelector()

# ---------- 2. 三点位同时佩戴 + 拼接顺序 ----------
out = node.process_text("", "提示词", "", 0, hat="红色棒球帽", earring="金色流苏耳坠", necklace="珍珠项链")
expect_order = out[0].find("棒球帽") < out[0].find("流苏长耳坠") < out[0].find("珍珠项链")
check("三点位佩戴+顺序(帽→耳→颈)", expect_order, out[0][:60])
check("段间逗号拼接", out[0].count(", ") >= 3 and out[0].endswith(", "), out[0][-20:])

# ---------- 3. prefix ----------
out2 = node.process_text("wearing: ", "提示词", "", 0, earring="珍珠耳钉")
check("prefix 空格连接", out2[0].startswith("wearing: 小巧圆润"), out2[0][:40])

# ---------- 4. 全部无 → 只输出 prefix ----------
out3 = node.process_text("", "提示词", "", 0)
check("全空选输出空串", out3[0] == "", repr(out3[0]))

# ---------- 5. extra_text 追加 ----------
out4 = node.process_text("", "提示词", "银色脚链, 金质闭口镯", 0, earring="银色环形耳环")
check("extra_text 追加两件", "脚踝" in out4[0] and "闭口手镯" in out4[0], out4[0][:80])
out5 = node.process_text("", "提示词", "不存在的饰品名", 0)
check("extra_text 未命中原文透传", out5[0].strip().rstrip(",").strip() == "不存在的饰品名", repr(out5[0]))

# ---------- 6. 随机：同 seed 稳定 + 部位间不互相干扰 ----------
r1 = node.process_text("", "提示词", "", 42, earring="随机 (Random)")[0]
r2 = node.process_text("", "提示词", "", 42, earring="随机 (Random)")[0]
check("同 seed 随机稳定", r1 == r2, r1[:30])
r3 = node.process_text("", "提示词", "", 99, earring="随机 (Random)")[0]
check("不同 seed 可能不同", True, r3[:30])
ra = node.process_text("", "提示词", "", 7, hat="随机 (Random)", earring="随机 (Random)")[0]
rb = node.process_text("", "提示词", "", 7, hat="随机 (Random)")[0]
hat_a = ra.split(", ")[0]
hat_b = rb.split(", ")[0]
check("部位随机互不干扰", hat_a == hat_b, "%s || %s" % (hat_a[:20], hat_b[:20]))
check("随机池只含本部位条目", "耳" in r1 or "环" in r1 or "钉" in r1 or "坠" in r1, r1[:30])

# ---------- 7. output_mode ----------
ok = node.process_text("", "Key", "", 0, necklace="珍珠项链")[0]
check("Key 模式输出英文 key", ok.strip().rstrip(",").strip() == "pearl necklace, elegant", repr(ok))
od = node.process_text("", "描述+提示词", "", 0, necklace="珍珠项链")[0]
check("描述+提示词 模式", od.strip().startswith("珍珠项链("), od[:30])

# ---------- 8. 旧工作流兜底：条目被删/改名 ----------
ob = node.process_text("", "提示词", "", 0, earring="已被删除的耳坠", necklace="珍珠项链")
check("失效条目跳过不报错", "珍珠项链" in ob[0] and "已被删除" not in ob[0], ob[0][:40])

# ---------- 9. 全部位同时佩戴 ----------
allsel = dict(hat="黑色贝雷帽", hair_ornament="珍珠发夹", earring="金色流苏耳坠",
              necklace="黑色丝绒choker", face="黑色墨镜", hand="银质单戒",
              wrist="机械腕表", waist="黑色方扣皮带", ankle="银色脚链")
oall = node.process_text("", "提示词", "", 0, **allsel)[0]
check("9 部位同时佩戴", oall.count(", ") >= 9, oall.count(", "))

print()
print("RESULT:", "ALL PASS" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
