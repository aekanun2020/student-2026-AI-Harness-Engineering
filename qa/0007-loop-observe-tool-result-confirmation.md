# Q&A Log — Entry 0007

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

บันทึก qa แล้วลองดู loop ใน lab 3 นะครับ มันเอา tool result ซึ่งอาจเป็นสิ่งที่ raise วนกลับไปให้ LLM ทำการ observation นะ

## คำตอบ (verbatim)

ใช่เลยครับ ตรงเป๊ะ — ผมยกโค้ดมาดูชัดๆ ให้เห็นว่าเกิดขึ้นตรงไหน:

```python
62: def run_agent(question: str, max_steps: int = 6):
...
67:    for step in range(1, max_steps + 1):
68:        resp = llm.chat(messages=messages, tools=TOOLS)
...
78:            for call in msg.tool_calls:
79:                args = json.loads(call.function.arguments or "{}")
80:                result = dispatch(call.function.name, args)
81:                print(f"           TOOL_USE {call.function.name}({args}) -> {result}")
82:                messages.append({
83:                    "role": "tool", "tool_call_id": call.id,
84:                    "content": result,   # OBSERVE: ป้อนผล tool กลับเข้า context
85:                })
86:            continue   # วนกลับให้ LLM อ่านผล tool
```

**สังเกตจุดสำคัญ:** บรรทัด 80 `result = dispatch(...)` **ไม่สนใจเลยว่า `result` จะเป็นค่าคำนวณสำเร็จ (`"60"`) หรือเป็น error string ที่มาจาก exception ที่ถูก catch ไว้ (`"error: division by zero"`)** — ทั้งสองแบบไหลเข้าโค้ด**เส้นทางเดียวกัน** ไม่มีการแยก if/else ว่า "ถ้าเป็น error ทำแบบหนึ่ง ถ้าสำเร็จทำอีกแบบ" เลย

บรรทัด 82-85 คือจุดที่คุณพูดถึง — เอา `result` (ไม่ว่าจะเป็นอะไร) ห่อเป็น `{"role": "tool", "content": result}` แล้วยัดกลับเข้า `messages` — คอมเมนต์ในโค้ดเองก็เขียนตรงๆ ว่า **`# OBSERVE`** บรรทัด 86 `continue` วนกลับไปเรียก `llm.chat(messages=messages, ...)` ที่บรรทัด 68 อีกครั้ง **พร้อม tool result/error ที่เพิ่งเกิดอยู่ใน `messages` แล้ว** — LLM รอบถัดไปเลยได้ "เห็น" มันแน่นอน 100%

**นี่คือ evidence ที่ตรงกับสิ่งที่ผมสรุปไว้ก่อนหน้าเป๊ะ:** loop นี้ทำ **OBSERVE ได้ถูกต้องสมบูรณ์** (tool result หรือ error ถูกป้อนกลับให้ LLM เห็นแน่นอนทุกครั้ง ไม่มีทางหลุด) — นี่คือ**โครงสร้างที่จำเป็น**สำหรับให้ self-correction เกิดขึ้นได้ แต่ที่ทดสอบแล้วพบว่าโมเดลไม่ retry เอง ไม่ใช่เพราะ loop ทำงานผิดหรือ observe ไม่ถึง (มันถึงแน่นอน ตามที่โค้ดข้างบนพิสูจน์) แต่เป็นเพราะ**ไม่มีใครสั่งโมเดลว่า "เห็น error แล้วให้ทำอะไรต่อ"** — OBSERVE เป็นแค่ "ป้อนข้อมูลให้เห็น" ส่วนจะ "ตัดสินใจทำอะไรกับสิ่งที่เห็น" เป็นเรื่องของ reasoning ของ LLM เอง ซึ่งต้องมี instruction ชี้นำ (ที่ตอนนี้ยังไม่มีใน `SYSTEM` ของ Lab 3)

พูดสรุปเป็นสมการง่ายๆ: **OBSERVE (loop นี้มีแล้ว, ทำงานถูกต้อง) + คำสั่งให้ retry (Lab 3 ยังไม่มี) = self-correction จริง**
