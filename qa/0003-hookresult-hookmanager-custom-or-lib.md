# Q&A Log — Entry 0003

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

```
@dataclass
class HookResult:
    decision: str = "allow"                 # allow | deny | modify
    reason: str | None = None
    data: dict | None = None
    additional_context: str | None = None

class HookManager:
    def register(self, event, fn, matcher=None): ...
    def run(self, event, payload, tool_name=None) -> HookResult: ...

อันนี้ใช้ lib/mod/framework อะไร หรือ custom
```

## คำตอบ (verbatim)

**Custom ครับ ไม่ได้ใช้ framework ไหนเลย** — ทั้ง `HookResult` และ `HookManager` เป็นโค้ดที่เขียนเองทั้งหมด ดูจาก import ที่ [labs/core/hooks.py:29-30](../labs/core/hooks.py:29):

```python
from collections import defaultdict
from dataclasses import dataclass
import re
```

มีแค่ 2 อย่างที่มาจาก **Python standard library** (ไม่ใช่ third-party library):
- `dataclasses.dataclass` — decorator มาตรฐานของ Python เอง (ตั้งแต่ Python 3.7) ใช้สร้าง class ที่เก็บข้อมูลแบบสั้นๆ โดยไม่ต้องเขียน `__init__` เอง (ให้ `decision`, `reason`, `data`, `additional_context` เป็น field พร้อมค่า default)
- `collections.defaultdict` — ใช้เก็บ hook function หลายตัวต่อ 1 event
- `re` — ใช้ทำ matcher แบบ regex

ส่วน **logic ทั้งหมด** (`register()`, `run()`, กลไก allow/deny/modify, การ short-circuit ตอนเจอ deny) **เขียนเองล้วนๆ** ไม่ได้อิงจาก library อย่าง LangChain, LangGraph หรือ SDK ตัวไหนเลย — เป็นแค่แนวคิด (ไม่ใช่โค้ด) ที่ยืมมาจากการอ่านเอกสารของ Claude Code Hooks กับ OpenAI Agents SDK Guardrails ตามที่อธิบายไว้ใน docstring บรรทัด 3-10 ของไฟล์ (ลิงก์เอกสารทั้งสองอยู่ตรงนั้น)

พูดง่ายๆ คือ: **แนวคิดยืมมา แต่โค้ดเขียนเอง 100%**
