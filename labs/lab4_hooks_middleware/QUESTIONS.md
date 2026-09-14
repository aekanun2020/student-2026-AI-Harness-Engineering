# Lab 4 — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบาย hook engine และการออกแบบแบบเต็มที่ [README.md](README.md)

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด `agent_loop_hooks.py`)

ถ้ารัน `python labs/lab4_hooks_middleware/agent_loop_hooks.py` โดยไม่ใส่ argument agent จะใช้
คำถามเดียวกับ Lab 3:

**คำถาม:** `ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร`

คำถามนี้ไม่ควร trigger hook ไหนเป็น `deny` เลย (นิพจน์สั้น, ไม่มี secret, คำตอบมีตัวเลข) — ควรได้
ผลลัพธ์เหมือน Lab 3 เป๊ะ บวกไฟล์ `agent_audit.log` ที่มี audit trail ของทุก tool call

---

## แบบฝึกหัด: ทดสอบให้แต่ละ hook trigger จริง

| # | วิธีทดสอบ | Hook ที่ควร trigger | พฤติกรรมที่ควรเห็น |
| --- | --- | --- | --- |
| 1 | `python agent_loop_hooks.py "คำนวณ 1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1"` (นิพจน์ยาว >40 ตัวอักษร) | `guard_calculate_hook` — decision `deny` | เห็นบรรทัด `HOOK pre_tool DENY` และ `dispatch()` (`calculate` จริง) **ไม่ถูกเรียกเลย** |
| 2 | ตั้งคำถามที่ทำให้ LLM ส่ง `expression: " 15*4 "` (มีช่องว่างหน้า-หลัง) | `guard_calculate_hook` — decision `modify` | ใน `agent_audit.log` ค่า `args.expression` ที่ถูก log ต้องถูก trim แล้ว (`"15*4"` ไม่มีช่องว่าง) |
| 3 | รัน `python test_hooks.py` (ไม่ต้องมี API key) — ดู TEST RUN 2 | `redact_secrets_hook` | `agent_audit.log` ต้อง**ไม่มี**ข้อความ `sk-...` ดิบหลุดออกมาเลย มีแต่ `[REDACTED]` แทน |
| 4 | รัน `python test_hooks.py` — ดู TEST RUN 1 (LLM ตอบแบบไม่มีตัวเลข) | `require_number_on_stop_hook` | เห็นบรรทัด `HOOK stop DENY` 1 ครั้ง แล้ว agent ต้องพยายามตอบใหม่จนมีตัวเลข |

> เคส #1, #3, #4 รันซ้ำได้ผลแน่นอน (deterministic) เพราะ `test_hooks.py` stub คำตอบ LLM ไว้แล้ว
> ส่วนเคส #2 ถ้ารันกับ LLM จริง (ไม่ใช่ test) ผลอาจไม่คงที่เพราะขึ้นกับว่า LLM จะใส่ช่องว่างในนิพจน์
> หรือไม่ — ถ้าอยากเห็นแบบควบคุมได้ 100% ให้แก้ `test_hooks.py` เพิ่ม case ทดสอบเองได้

## แบบฝึกหัดต่อยอด (เขียน hook เพิ่มเอง)

1. เพิ่ม hook ใหม่ที่ `deny` คำถามที่มีคำหยาบ/ไม่เหมาะสม ก่อนถึง `pre_llm`
2. เพิ่ม hook `post_tool` ที่ปัดเศษผลลัพธ์จาก `calculate` ให้เหลือทศนิยม 2 ตำแหน่ง
3. ลองสลับลำดับ `register("post_tool", audit_log_hook)` ให้มาก่อน `redact_secrets_hook` แล้วรัน
   `test_hooks.py` อีกครั้ง — ควรเห็น `assert not secret_leaked` **fail** (พิสูจน์ว่าลำดับ hook สำคัญจริง)
