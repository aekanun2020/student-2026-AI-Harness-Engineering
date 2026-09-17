# Lab 4 — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบาย hook engine และการออกแบบแบบเต็มที่ [README.md](README.md)

> **ก่อนรันทุกคำสั่งในหน้านี้:** เปิด terminal → `cd` เข้าโฟลเดอร์ repo → `source .venv/bin/activate`
> (Windows: `.venv\Scripts\activate` และใช้ `python` แทน `python3`) — ต้องเห็น `(.venv)` หน้า prompt
> ถ้าเจอ error ว่าหา `openai` ไม่เจอ แปลว่าลืมขั้นนี้
> ทุกคำสั่งรันจาก root ของ repo (ไม่ต้อง `cd` เข้าโฟลเดอร์ lab)

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด `agent_loop_hooks.py`)

ถ้ารัน `python labs/lab4_hooks_middleware/agent_loop_hooks.py` โดยไม่พิมพ์คำถามต่อท้าย agent จะใช้
คำถามเดียวกับ Lab 3:

**คำถาม:** `ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร`

คำถามนี้ไม่ควรทำให้ hook ตัวไหนบล็อก (`deny`) เลย (นิพจน์สั้น, ไม่มีข้อมูลลับ, คำตอบมีตัวเลข) — ควรได้
ผลลัพธ์เหมือน Lab 3 เป๊ะ **ไม่มีบรรทัด `HOOK …` โผล่** บวกไฟล์ `labs/lab4_hooks_middleware/agent_audit.log`
ที่บันทึกทุก tool call ไว้ (เปิดดูด้วย text editor ธรรมดาได้)

---

## แบบฝึกหัด: ทำให้แต่ละ hook ทำงานจริง

| # | ระดับ | วิธีทดสอบ | Hook ที่ทำงาน | บรรทัดที่ต้องมองหาบนหน้าจอ |
| --- | --- | --- | --- | --- |
| 1 | 🟢 | `python labs/lab4_hooks_middleware/agent_loop_hooks.py "คำนวณ 1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1"` (นิพจน์ยาว >40 ตัวอักษร) | `guard_calculate_hook` — บล็อก (`deny`) | บรรทัด `HOOK pre_tool DENY calculate: นิพจน์ยาวเกินไป …` และบรรทัด `TOOL_USE calculate(...)` ต้องลงท้ายด้วย `[hook denied] …` **ไม่ใช่ตัวเลขผลลัพธ์** — แปลว่าเครื่องคิดเลขจริงไม่ได้ถูกเรียกเลย |
| 2 | 🟢 | `python labs/lab4_hooks_middleware/test_hooks.py` แล้วเลื่อนหาหัวข้อ `=== TEST RUN 1 ===` ในผลลัพธ์ | `guard_calculate_hook` — แก้ไข (`modify`) | ในผลลัพธ์ TEST RUN 1 บรรทัด `TOOL_USE calculate({'expression': '15*4'})` — สคริปต์ส่ง `" 15*4 "` (มีช่องว่างหน้า-หลัง) เข้ามา แต่ hook ตัดช่องว่างให้ก่อนถึงเครื่องคิดเลข |
| 3 | 🟢 | `python labs/lab4_hooks_middleware/test_hooks.py` แล้วเลื่อนหาหัวข้อ `=== TEST RUN 2 ===` | `redact_secrets_hook` | บรรทัด `HOOK post_tool: [hook] พบ pattern คล้าย secret …` และ `TOOL_USE … -> here is the key: [REDACTED]` — ข้อความ `sk-…` ของจริง**ไม่โผล่**ที่ไหนเลย รวมถึงในไฟล์ `agent_audit.log` |
| 4 | 🟢 | `python labs/lab4_hooks_middleware/test_hooks.py` แล้วดู `=== TEST RUN 1 ===` ช่วงท้าย | `require_number_on_stop_hook` | บรรทัด `[step 2] HOOK stop DENY: คำถามดูเหมือนมีการคำนวณ แต่คำตอบไม่มีตัวเลขเลย` แล้วมี `[step 3] END_TURN` ตามมา — AI ถูกบังคับให้ตอบใหม่จนมีตัวเลข |

> ข้อ 2-4 ใช้ `test_hooks.py` ซึ่ง**ไม่ต้องมี API key และไม่เสียเงิน** — มันสลับตัวเรียก AI จริงเป็นตัวปลอม
> ที่ตอบตามบทที่เขียนไว้ ผลจึงเหมือนเดิมทุกครั้ง (deterministic) ต่างจากข้อ 1 ที่เรียก AI จริง
> รันแล้วต้องเห็น `ALL TESTS PASSED` ที่บรรทัดสุดท้าย

## แบบฝึกหัดต่อยอด — 🔴 สำหรับคนที่เขียน Python ได้แล้ว (ข้ามได้)

1. เพิ่ม hook ใหม่ที่ `deny` คำถามที่มีคำหยาบ/ไม่เหมาะสม ที่ event `pre_llm`
2. เพิ่ม hook `post_tool` ที่ปัดเศษผลลัพธ์จาก `calculate` ให้เหลือทศนิยม 2 ตำแหน่ง
3. ใน `build_default_hooks()` ลองสลับให้ `register("post_tool", audit_log_hook)` มาก่อน
   `redact_secrets_hook` แล้วรัน `test_hooks.py` อีกครั้ง — ต้องเห็น TEST RUN 2 **fail** (บรรทัด
   `assert not secret_leaked`) พิสูจน์ว่าลำดับ hook สำคัญจริง: ถ้า log ก่อน redact ข้อมูลลับจะหลุดลง log

> เฉลยเชิงพฤติกรรม ไม่ใช่เฉลยคำตอบตายตัว — ข้อ 1 ประโยคคำตอบของ AI ต่างกันทุกครั้ง สิ่งที่ต้องตรงคือ
> **มี/ไม่มีบรรทัด `HOOK …`** ที่ระบุไว้ ไม่ใช่ข้อความคำตอบ
