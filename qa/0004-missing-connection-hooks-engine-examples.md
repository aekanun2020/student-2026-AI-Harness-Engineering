# Q&A Log — Entry 0004

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

ผมอ่าน labs/core/hooks.py แล้วอ่าน Hook ตัวอย่าง 4 ตัวใน agent_loop_hooks.py

ทั้งสองหัวข้อใน readme อันนี้พอเข้าใจแต่ละหัวข้อ แต่ผมสังเกตว่า มันไม่มีจุดเชื่อมกันชัดเจน

## คำตอบ (verbatim)

จุดเชื่อมที่หายไประหว่าง 2 หัวข้อนั้นคือฟังก์ชัน **`build_default_hooks()`** ใน [labs/lab4_hooks_middleware/agent_loop_hooks.py:88-99](../labs/lab4_hooks_middleware/agent_loop_hooks.py:88) — README อธิบาย engine (`core/hooks.py`) แยกหนึ่งหัวข้อ แล้วอธิบายฟังก์ชัน hook 4 ตัวแยกอีกหัวข้อ แต่ไม่ได้โชว์โค้ดตรงกลางที่ "เอาสองอย่างมาต่อกัน":

```python
def build_default_hooks() -> HookManager:
    hooks = HookManager()
    hooks.register("pre_tool", audit_log_hook)
    hooks.register("pre_tool", guard_calculate_hook, matcher="calculate")
    hooks.register("post_tool", redact_secrets_hook)
    hooks.register("post_tool", audit_log_hook)
    hooks.register("stop", require_number_on_stop_hook)
    hooks.register("stop", audit_log_hook)
    return hooks
```

**นี่คือจุดเชื่อม:** `hooks.register(event, fn, matcher)` คือการเอา **function ธรรมดา 4 ตัวที่อธิบายไว้ในหัวข้อ "Hook ตัวอย่าง"** ไปผูกเข้ากับ **`HookManager` engine ที่อธิบายไว้ในหัวข้อ "ออกแบบ"** โดยระบุว่าตัวไหนควรทำงานตอน event ไหน

จากนั้น `run_agent()` (ฟังก์ชันหลักของ loop) จะเรียก `hooks.run(event, payload, ...)` ที่จุดต่างๆ 5 จุดตามที่ diagram ในหัวข้อ "ออกแบบ" บอกไว้ — ตรงนี้แหละคือตอนที่ function ที่ register ไว้ **ถูกเรียกจริง**

ลองไล่ trace ทีละขั้นสำหรับเคส "นิพจน์ยาวเกิน 40 ตัวอักษร" ให้เห็นภาพเต็ม:

1. `run_agent()` วนมาถึง tool call `calculate` → เรียก `hooks.run("pre_tool", {...}, tool_name="calculate")` ([บรรทัด 128](../labs/lab4_hooks_middleware/agent_loop_hooks.py:128))
2. ข้างใน `HookManager.run()` (ที่ `core/hooks.py`) จะไล่ลิสต์ hook ที่ register ไว้กับ event `"pre_tool"` ตามลำดับที่ `build_default_hooks()` register ไว้:
   - ตัวแรก `audit_log_hook` (matcher=`None` → fire ทุก tool) → เขียน log → คืน `allow`
   - ตัวที่สอง `guard_calculate_hook` (matcher=`"calculate"` → ตรงกับ `tool_name` ที่ส่งมา) → เช็คความยาว → คืน `HookResult(decision="deny", reason=...)`
3. `HookManager.run()` เจอ `"deny"` → **short-circuit ทันที** คืนผลนี้กลับไปเลย ไม่เรียก hook ที่เหลือ
4. กลับมาที่ `run_agent()` บรรทัด 130: `if pre.decision == "deny":` เป็นจริง → **ไม่เรียก `dispatch()` เลย** (ฟังก์ชัน `calculate()` จริงจาก Lab 3 ไม่ถูกรันเลยด้วยซ้ำ) → แค่พิมพ์ข้อความปฏิเสธแทน

พูดสั้นๆ: **หัวข้อ "ออกแบบ" = สร้างเครื่องมือเปล่า (engine), หัวข้อ "Hook ตัวอย่าง" = ชิ้นส่วนที่จะเสียบเข้าเครื่อง, `build_default_hooks()` = ขั้นตอนเสียบจริง, `run_agent()` = ตัวกดปุ่มให้เครื่องทำงาน** — ทั้ง 4 ส่วนนี้อยู่ในไฟล์เดียวกันหมด (`agent_loop_hooks.py`) แต่ README แบ่งอธิบายเป็นคนละหัวข้อเลยดูขาดกัน

ต้องการให้ผมเพิ่มหัวข้อสั้นๆ ใน README แสดงโค้ด `build_default_hooks()` นี้ พร้อม trace แบบนี้เป็นสะพานเชื่อม 2 หัวข้อไหมครับ?
