# Lab 5 — Memory (Compaction + Notes) + Checkpoint

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** — ส่วนความจำ (`ConversationMemory`:
> compaction + notes) นำมาจากบทเรียนเรื่อง memory ของหลักสูตร แล้วเพิ่ม **checkpoint** เข้าไปเพื่อให้
> ความจำนั้นอยู่รอดแม้ปิดโปรแกรมแล้วเปิดใหม่ (ทุกอย่างที่ต้องใช้อยู่ในโฟลเดอร์นี้แล้ว)
>
> Sandbox แยกออกไปอยู่ **[Lab 6](../lab6_sandbox/README.md)** เพราะเป็นคนละ Layer (6 vs 2)

---

## จุดประสงค์การเรียนรู้

- เข้าใจ **Compaction** — เมื่อบทสนทนายาวเกินเกณฑ์ ให้ LLM สรุปของเก่าเป็นย่อหน้าเดียวเพื่อรักษา
  token budget โดยไม่ทิ้งข้อมูลสำคัญ
- เข้าใจ **Notes** — fact ที่ต้องจำไว้เสมอ ไม่ถูกกระทบแม้ compaction จะย่อ history ทิ้งไปแล้ว
- เข้าใจความต่างระหว่าง **"memory ที่อยู่ใน RAM"** (หายเมื่อ process ตาย) กับ **"external memory
  ที่รอดข้าม context reset จริง"** (ต้อง persist ลงดิสก์/DB)
- เห็น **checkpoint** — การบันทึกสถานะลงไฟล์เป็นระยะ เพื่อให้ปิดโปรแกรมแล้วเปิดใหม่ก็คุยต่อได้ และถ้า
  โปรแกรมล่มกลางทางก็กลับมาทำต่อจากจุดที่ค้างได้ ไม่ต้องเริ่มใหม่

**เทียบกับสิ่งที่คุณเคยเห็นในหน้าแชท:** เคยสังเกตไหมว่า ChatGPT/Claude จำได้ว่าคุณเคยบอกอะไรไว้เมื่อวาน?
Lab นี้สร้างสิ่งนั้นเองให้เห็นว่าข้างในทำยังไง — และ **compaction** คือเหตุผลที่แชทยาวๆ AI จะเริ่ม "ลืม"
รายละเอียดตอนต้น (มันสรุปทิ้งเพื่อประหยัดที่ เก็บไว้แค่ใจความ)

---

## ทดสอบจริงทั้ง 3 อย่าง (ไม่ใช่แค่ทฤษฎี)

### 1) External memory รอดข้าม process จริง

```
=== รันครั้งที่ 1 (process ใหม่) ===
[user] ผมชอบเลข 42 มากที่สุด ช่วยคำนวณ 42*2 ให้หน่อย
[answer] ผลลัพธ์ของ 42 × 2 = 84 ครับ ... จะจำไว้เลยว่าคุณชื่นชอบเลข 42

=== รันครั้งที่ 2 (process ใหม่อีกรอบ — คนละ process กับรอบแรกเป๊ะๆ) ===
[resume] โหลด memory ของ thread 'mem-test' -> history 4 ข้อความ, notes 1 รายการ
[user] เมื่อกี้ผมบอกว่าผมชอบเลขอะไร แล้วผลคูณที่ขอให้คำนวณคือเท่าไร
[answer] จากการสนทนาก่อนหน้า คุณบอกว่าชอบเลข 42 มากที่สุดครับ และผลคูณ ... คือ 42 × 2 = 84
```

process ที่ 2 **ไม่มี state ใดๆ หลงเหลือจาก process ที่ 1 เลยในความหมายของ RAM** (คนละ process,
คนละ interpreter) แต่ตอบถูกเป๊ะเพราะโหลดจาก checkpoint file — นี่คือ "external memory" ตัวจริง
ถ้าเก็บความจำไว้แค่ในตัวแปรของโปรแกรม (`self.history` ใน RAM) พอปิดโปรแกรมก็หายหมด เปิดใหม่จะจำอะไร
ไม่ได้เลย — checkpoint คือสิ่งที่ทำให้มันไม่หาย

### 2) Compaction ทำงานร่วมกับ checkpoint ได้ถูกต้อง

```
=== turn 2 ===
[user] คำนวณ 2 บวก 2 ให้หน่อย
[answer] ผลลัพธ์ของ 2 + 2 = 4 ครับ
[compaction] ย่อ 10 ข้อความเป็นสรุป 1 ก้อน (เหลือ 5 ข้อความ)

=== turn 3 (process ใหม่) ===
[resume] โหลด memory ของ thread 'mem-test' -> history 5 ข้อความ, notes 1 รายการ
```

`maybe_compact()` trigger ที่ `COMPACT_AFTER_MESSAGES = 12` พอดี แล้ว**สถานะหลัง compact ก็ถูก checkpoint ต่อทันที** (turn ถัดไปโหลดมาเห็น 5 ข้อความ
ไม่ใช่ 12 ข้อความเดิม) — พิสูจน์ว่า compaction กับ checkpoint ทำงานร่วมกันถูกต้อง ไม่ชนกัน

### 3) Resume หลัง crash กลาง turn

รันเป็น subprocess จริงแล้ว `SIGKILL` (คำสั่งให้ระบบปฏิบัติการฆ่าโปรแกรมทันทีแบบไม่มีโอกาสเซฟ —
เหมือนดึงปลั๊ก) ทันทีที่ step 2 เริ่ม (คำถามบังคับให้ต้องรู้ผล `get_time`
ก่อนถึงจะ `calculate` ต่อได้ — บังคับ 2 step จริง):

```
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE get_time({}) -> 2026-09-15 13:19:25
[step 2] THINK -> ขอเรียก 1 tool
>>> KILL -9 <<<
```

checkpoint บนดิสก์: `pending: True, history len: 3` — รันซ้ำด้วย `thread_id` เดิม (คำถามว่างเปล่า
เพราะ resume ไม่ต้องการคำถามใหม่):

```
[resume] โหลด memory ของ thread 'crash-mem' -> history 3 ข้อความ, notes 1 รายการ
[resume] turn ก่อนหน้าค้างกลางทาง (ถูกขัดจังหวะ) -> วิ่งต่อโดยไม่เพิ่มคำถามใหม่
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE calculate({'expression': '19*100'}) -> 1900
[answer] ... นาที (MM): 19 ... 19 × 100 = 1900
```

ใช้เลข `19` (นาทีจาก `get_time` ที่บันทึกไว้ก่อนถูกฆ่า) **ไม่เรียก `get_time` ซ้ำ** — พิสูจน์ resume
ใช้ state เดิมจริง

---

## วิธีรัน

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "<คำถาม>" [thread_id]
```

`thread_id` = ชื่อบทสนทนาที่**คุณตั้งเอง** (เช่น `my-thread`) — ใช้ชื่อเดิมซ้ำ = คุยต่อเรื่องเดิมแม้ process
ก่อนหน้าจะปิดไปแล้ว · ใช้ชื่อใหม่ = เริ่มบทสนทนาใหม่ · `[ ]` ในคำสั่งแปลว่าใส่หรือไม่ใส่ก็ได้ ไม่ใส่จะใช้
`"default"` — checkpoint เก็บเป็นไฟล์ที่ `labs/lab5_memory_checkpoint/checkpoints/<thread_id>.json`
(ไม่ถูกอัปโหลดขึ้น GitHub เพราะเป็นข้อมูลตอนรัน ไม่ใช่โค้ด)

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)

---

> **สำหรับผู้สอน/ผู้ตรวจ — ที่มาของโค้ด:** ดัดแปลงจาก `labs/lab7_memory/agent_memory.py` ของ repo ต้นทาง
> - **คงไว้เหมือนเดิม:** class `ConversationMemory` ทั้งก้อน (`history` / `notes` / `context()` / `maybe_compact()`) — logic การจำและการสรุปไม่แก้เลย
> - **ปรับ:** สลับ MCP tools (`ToolRegistry`) เป็น local tools ของ Lab 3 และแก้ถ้อยคำ `SYSTEM` — เพราะ repo นี้ไม่มี MCP server
> - **เพิ่มใหม่:** checkpoint (บันทึก/โหลด JSON ต่อ `thread_id`) และ entry point แบบรับคำถามจาก CLI ทีละครั้ง
