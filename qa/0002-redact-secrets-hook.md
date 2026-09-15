# Q&A Log — Entry 0002

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

redact คืออะไร อ่าน readme แล้วไม่เข้าใจ

## คำตอบ (verbatim)

"Redact" แปลว่า **การปิด/ลบข้อมูลที่อ่อนไหวออกจากข้อความ ก่อนส่งข้อความนั้นต่อไปให้คนอื่น (หรือระบบอื่น) เห็น** — เหมือนเวลาเอกสารราชการมีคำถูกป้ายดำทับไว้ไม่ให้อ่านออก

ในบริบทของ `redact_secrets_hook` ที่ [labs/lab4_hooks_middleware/agent_loop_hooks.py](../labs/lab4_hooks_middleware/agent_loop_hooks.py):

```python
SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{10,}")

def redact_secrets_hook(payload: dict) -> HookResult:
    result = payload.get("result", "")
    if SECRET_PATTERN.search(result):
        redacted = SECRET_PATTERN.sub("[REDACTED]", result)
        return HookResult(decision="modify", data={"result": redacted}, ...)
    return HookResult(decision="allow")
```

**อธิบายเป็นขั้นตอน:**
1. `result` คือผลลัพธ์ดิบที่ tool ส่งกลับมา (เช่นสมมติมี tool ที่ดันคืนค่าที่มี API key ปนมาด้วย)
2. `SECRET_PATTERN` คือ pattern ที่ดักจับข้อความหน้าตาเหมือน API key (ขึ้นต้นด้วย `sk-` ตามด้วยตัวอักษร/ตัวเลขยาวๆ)
3. ถ้าเจอ pattern นี้ใน `result` → **redact** คือเอาส่วนที่แมทช์ (ตัว secret จริงๆ) มา**แทนที่ด้วยคำว่า `[REDACTED]`** ด้วย `SECRET_PATTERN.sub(...)`

**ตัวอย่างจริง** (จาก `test_hooks.py` ที่เราเทสไว้):

| ก่อน redact | หลัง redact |
|---|---|
| `here is the key: sk-ABCDEFGHIJ1234567890` | `here is the key: [REDACTED]` |

**ทำไมต้องมี:** ค่าที่ redact แล้วนี่แหละที่จะถูกป้อนกลับเข้าไปใน context ของ LLM ต่อ (และถูก log ลง `agent_audit.log`) — ถ้าไม่ redact ก่อน ตัว secret จริงจะหลุดเข้าไปอยู่ใน conversation history ของ LLM และอาจโผล่ในคำตอบที่ LLM ตอบกลับผู้ใช้ หรือถูกบันทึกลง log แบบดิบๆ ซึ่งเป็นความเสี่ยงด้านความปลอดภัย — hook นี้เลยดัก "ปิดตา" ไม่ให้ LLM เห็นค่า secret ตัวจริงเลย เห็นแค่ `[REDACTED]` แทน
