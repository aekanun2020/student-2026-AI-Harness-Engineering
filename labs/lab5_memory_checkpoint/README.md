# Lab 5 — Memory (Compaction + Notes) + Checkpoint

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** และดัดแปลงจาก
> [labs/lab7_memory/agent_memory.py](https://github.com/aekanun2020/Python-Agent-LangGraph/blob/main/labs/lab7_memory/agent_memory.py)
> ของ Python-Agent-LangGraph — คง `ConversationMemory` (history/notes/compaction) ไว้ใกล้เคียง
> ต้นฉบับที่สุด แล้วเพิ่ม **checkpoint** เข้าไปเพื่อให้ "external memory" ที่ต้นฉบับอ้างว่ามี
> กลายเป็น external จริง (ดูหัวข้อ "สิ่งที่ต่างจากต้นฉบับ" ด้านล่าง)
>
> Sandbox แยกออกไปอยู่ **[Lab 6](../lab6_sandbox/README.md)** เพราะเป็นคนละ Layer (6 vs 2)

---

## จุดประสงค์การเรียนรู้

- เข้าใจ **Compaction** — เมื่อบทสนทนายาวเกินเกณฑ์ ให้ LLM สรุปของเก่าเป็นย่อหน้าเดียวเพื่อรักษา
  token budget โดยไม่ทิ้งข้อมูลสำคัญ
- เข้าใจ **Notes** — fact ที่ต้องจำไว้เสมอ ไม่ถูกกระทบแม้ compaction จะย่อ history ทิ้งไปแล้ว
- เข้าใจความต่างระหว่าง **"memory ที่อยู่ใน RAM"** (หายเมื่อ process ตาย) กับ **"external memory
  ที่รอดข้าม context reset จริง"** (ต้อง persist ลงดิสก์/DB)
- เห็น **checkpoint** ทำหน้าที่เดียวกับใน Lab 6 (มด/step) และ Lab 3/3a/4 (Layer 5) — แต่ประยุกต์ใช้
  กับ multi-turn memory แทนที่จะเป็น single-shot loop

---

## สิ่งที่ต่างจากต้นฉบับ (`labs/lab7_memory/agent_memory.py`)

| ส่วน | ต้นฉบับ Lab 7 | ที่นี่ (Lab 5) |
| --- | --- | --- |
| `ConversationMemory` (history/notes/`context()`/`maybe_compact()`) | ต้นฉบับ | **เหมือนเดิมทุกบรรทัด** ไม่แก้ logic เลย |
| Tools | `ToolRegistry` ต่อ MCP MSSQL Server จริงผ่าน `config.MCP_SERVER_URL` | Local tools ของ Lab 3 (`get_time`/`calculate`) เพราะ repo นี้ไม่มี MCP server ให้ต่อ |
| `SYSTEM` | DB-analyst persona อ้างอิง MCP tools ตรงๆ | ปรับให้เข้ากับ local tools แต่คงประโยค "จำบริบทการสนทนาก่อนหน้าได้" ไว้ (หัวใจของบทเรียน) |
| **Checkpoint** | ❌ ไม่มี — `history`/`notes` เป็นแค่ attribute ใน RAM ของ object เดียว process ตายก็หายหมด (ชื่อ "memory" แต่ไม่ external จริง) | ✅ **เพิ่มใหม่** — บันทึก `history`/`notes` ลง JSON ต่อ `thread_id` หลังจบทุก step/turn |
| Entry point | `main()` เรียก `turn()` ตายตัว 2 รอบในโค้ดเดียว (single process) | `main()` รับคำถามจาก CLI ทีละครั้ง โหลด memory จาก checkpoint ก่อนเสมอ — **แต่ละครั้งที่รันคือ process ใหม่จริง** ทำให้พิสูจน์ "รอดข้าม context reset" ได้ตรงไปตรงมากว่า |

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
ต่างจาก `self.history` ของ Lab 7 ต้นฉบับที่ถ้าลองปิด-เปิด process ใหม่จะจำอะไรไม่ได้เลย

### 2) Compaction ทำงานเหมือนต้นฉบับเป๊ะ

```
=== turn 2 ===
[user] คำนวณ 2 บวก 2 ให้หน่อย
[answer] ผลลัพธ์ของ 2 + 2 = 4 ครับ
[compaction] ย่อ 10 ข้อความเป็นสรุป 1 ก้อน (เหลือ 5 ข้อความ)

=== turn 3 (process ใหม่) ===
[resume] โหลด memory ของ thread 'mem-test' -> history 5 ข้อความ, notes 1 รายการ
```

`maybe_compact()` (โค้ดเดิมจาก Lab 7 ไม่เปลี่ยนแม้แต่บรรทัดเดียว) trigger ที่ `COMPACT_AFTER_MESSAGES
= 12` พอดี แล้ว**สถานะหลัง compact ก็ถูก checkpoint ต่อทันที** (turn ถัดไปโหลดมาเห็น 5 ข้อความ
ไม่ใช่ 12 ข้อความเดิม) — พิสูจน์ว่า compaction กับ checkpoint ทำงานร่วมกันถูกต้อง ไม่ชนกัน

### 3) Resume หลัง crash กลาง turn (เหมือนที่ทดสอบใน Lab 6 แต่ประยุกต์กับ memory)

รันเป็น subprocess จริงแล้ว `SIGKILL` ทันทีที่ step 2 เริ่ม (คำถามบังคับให้ต้องรู้ผล `get_time`
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

รันซ้ำด้วย `thread_id` เดิมหลายครั้ง = เหมือนคุยต่อในบทสนทนาเดิม แม้ process ก่อนหน้าจะปิดไปแล้ว
ไม่ใส่ `thread_id` จะใช้ `"default"` — checkpoint เก็บที่ `labs/lab5_memory_checkpoint/checkpoints/`
(gitignored เพราะเป็น runtime state ไม่ใช่ source)

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)
