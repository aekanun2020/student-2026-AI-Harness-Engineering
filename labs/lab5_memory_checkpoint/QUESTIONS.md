# Lab 5 — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบายแบบเต็มที่ [README.md](README.md)

> **ก่อนรันทุกคำสั่งในหน้านี้:** เปิด terminal → `cd` เข้าโฟลเดอร์ repo → `source .venv/bin/activate`
> (Windows: `.venv\Scripts\activate` และใช้ `python` แทน `python3`) — ต้องเห็น `(.venv)` หน้า prompt
> ถ้าเจอ error ว่าหา `openai` ไม่เจอ แปลว่าลืมขั้นนี้

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด)

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง" my-thread
```

คำสุดท้าย `my-thread` = **ชื่อบทสนทนาที่คุณตั้งเอง** — ใช้ชื่อเดิมซ้ำ = คุยต่อเรื่องเดิม, ใช้ชื่อใหม่ = เริ่ม
บทสนทนาใหม่ (ไม่ใส่จะใช้ชื่อ `default`)

รันครั้งแรกจะไม่มีความจำเก่าให้โหลด (ไม่มีบรรทัด `[resume]`) AI จะตอบว่ายังไม่มีอะไรให้จำ — รันซ้ำด้วยชื่อเดิม
จึงจะเห็น `[resume]`

---

## แบบฝึกหัด 1: 🟢 พิสูจน์ว่าความจำอยู่รอดแม้ปิดโปรแกรมแล้วเปิดใหม่

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "ผมชอบเลข 42 มากที่สุด ช่วยคำนวณ 42*2 ให้หน่อย" mem-demo
python labs/lab5_memory_checkpoint/agent_loop.py "เมื่อกี้ผมบอกว่าผมชอบเลขอะไร แล้วผลคูณที่ขอให้คำนวณคือเท่าไร" mem-demo
```

**บรรทัดที่ต้องมองหา:** คำสั่งที่สองต้องขึ้น `[resume] โหลด memory ของ thread 'mem-demo' -> history 4 ข้อความ …`
ก่อน แล้ว `[answer]` ต้องตอบถูกทั้ง **42** และ **84** — ทั้งที่คำสั่งที่สองเป็นการเปิดโปรแกรมใหม่ทั้งหมด
(ความจำในเครื่องจากรอบแรกหายไปหมดแล้ว) เพราะมันอ่านกลับมาจากไฟล์
`labs/lab5_memory_checkpoint/checkpoints/mem-demo.json` — ลองเปิดไฟล์นั้นดูก็ได้ เป็นข้อความอ่านออก

**ลองเทียบกับ Lab 3** (ที่ไม่มีความจำข้ามการรันเลย):
```bash
python labs/lab3_agent_loop/agent_loop.py "เมื่อกี้ผมบอกว่าผมชอบเลขอะไร แล้วผลคูณที่ขอให้คำนวณคือเท่าไร"
```
AI จะตอบไม่ได้ว่าคุณชอบเลขอะไร — ไม่มี `[resume]` และไม่มีไฟล์ความจำ

---

## แบบฝึกหัด 2: 🟢 บังคับให้ compaction (การสรุปย่อบทสนทนาเก่า) ทำงาน

รันคำถามสั้นๆ ซ้ำ **6 ครั้ง** ด้วยชื่อบทสนทนาเดียวกัน (แต่ละครั้ง = 1 turn ≈ 2 ข้อความ ต้องสะสมถึง ~12
ข้อความถึงจะสรุป) — พิมพ์ทีละบรรทัด เปลี่ยนแค่ตัวเลข:

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 1 บวก 1 ให้หน่อย" compact-demo
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 2 บวก 2 ให้หน่อย" compact-demo
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 3 บวก 3 ให้หน่อย" compact-demo
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 4 บวก 4 ให้หน่อย" compact-demo
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 5 บวก 5 ให้หน่อย" compact-demo
python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ 6 บวก 6 ให้หน่อย" compact-demo
```

(Mac/Linux ใช้ทางลัดได้: `for i in 1 2 3 4 5 6; do python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ $i บวก $i ให้หน่อย" compact-demo; done`
— Windows PowerShell ใช้ไม่ได้ ให้พิมพ์ทีละบรรทัดตามด้านบน)

**บรรทัดที่ต้องมองหา:** รอบใดรอบหนึ่งช่วงกลางๆ จะขึ้น `[compaction] ย่อ N ข้อความเป็นสรุป 1 ก้อน (เหลือ M ข้อความ)`
แล้วรอบถัดไปบรรทัด `[resume] … history M ข้อความ` จะเป็นตัวเลขที่**เล็กกว่า**รอบก่อนหน้า — ความจำถูกสรุปย่อ
แต่ AI ยังตอบเรื่องเก่าได้ (ลองถามในรอบที่ 7 ว่า "รอบแรกสุดผมให้คำนวณอะไร")

---

## แบบฝึกหัด 3: 🟢 จำลองโปรแกรมล่มกลางทาง แล้วกลับมาทำต่อ

ใช้คำถามที่บังคับให้ AI ต้องทำ 2 รอบ (ต้องรู้เวลาก่อนถึงจะคำนวณต่อได้):

```bash
python -u labs/lab5_memory_checkpoint/agent_loop.py "ให้เรียก get_time ก่อนเพียงอย่างเดียวในรอบแรก ดูนาที (MM) จากผลลัพธ์ แล้วค่อยเรียก calculate เพื่อคูณเลขนาทีนั้นด้วย 100 ในรอบถัดไปแยกต่างหาก ห้ามเรียกสอง tool พร้อมกันในรอบเดียว" crash-test
```

(`-u` = ให้พิมพ์ผลออกมาทันทีทีละบรรทัด ไม่งั้นจะเห็นผลช้าและกดหยุดไม่ทัน)

**พอเห็นบรรทัด `[step 2] THINK -> …` ปรากฏ ให้กด Ctrl+C ทันที** (มีเวลาราว 2-5 วินาที) — จะเห็นข้อความ
error ยาวๆ ลงท้ายด้วย `KeyboardInterrupt` **นั่นปกติ** เราตั้งใจหยุดมันเองเพื่อจำลองว่าโปรแกรมล่ม

เช็คว่าความจำก่อนล่มถูกเซฟไว้: เปิดไฟล์ `labs/lab5_memory_checkpoint/checkpoints/crash-test.json`
ต้องเห็น `"pending": true` (แปลว่ามีงานค้างอยู่)

แล้วรันคำสั่งสั้นๆ นี้ (ใส่คำถามอะไรก็ได้ เพราะมีงานค้าง โปรแกรมจะทำงานเก่าต่อโดยไม่รับคำถามใหม่):
```bash
python labs/lab5_memory_checkpoint/agent_loop.py "ต่อ" crash-test
```

**บรรทัดที่ต้องมองหา:** `[resume] turn ก่อนหน้าค้างกลางทาง (ถูกขัดจังหวะ) -> วิ่งต่อโดยไม่เพิ่มคำถามใหม่`
แล้ว**ไม่มี `TOOL_USE get_time` อีก** — ไปที่ `TOOL_USE calculate` ทันที ใช้เลขนาทีเดิมจากก่อนล่ม

> ถ้ากด Ctrl+C ช้าเกินไป (เห็น `[answer]` ขึ้นแล้ว) งานเสร็จสมบูรณ์ไปแล้ว ไม่มีอะไรค้าง — ลองใหม่ด้วยชื่อ
> บทสนทนาใหม่ (เช่น `crash-test2`) แล้วกดให้ไวขึ้น

---

## แบบฝึกหัดต่อยอด — 🟡/🔴 สำหรับคนที่เขียน Python ได้แล้ว (ข้ามได้)

1. 🟡 ลองลด `COMPACT_AFTER_MESSAGES` ใน `agent_loop.py` ให้ต่ำมากๆ (เช่น 4) แล้วดูว่า compaction ถี่ขึ้น
   แค่ไหน และเปิดไฟล์ checkpoint ดูว่าข้อความ `[สรุปบทสนทนาก่อนหน้า] …` ถูกเซฟลงไฟล์แทนของเก่าจริง
2. 🔴 เทียบกับ [LangGraph checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence)
   ที่มี backend หลายแบบ (`InMemorySaver`/`SqliteSaver`/`PostgresSaver`) — ลองเขียน backend อื่นให้
   `save_checkpoint`/`load_checkpoint` ของเรา (เช่น SQLite) แทนไฟล์ JSON เดี่ยวๆ

> เฉลยเชิงพฤติกรรม ไม่ใช่เฉลยคำตอบตายตัว — ประโยคคำตอบของ AI ต่างกันทุกครั้ง สิ่งที่ต้องตรงคือบรรทัด
> `[resume]` / `[compaction]` และ **มี/ไม่มี `TOOL_USE`** ที่ระบุไว้ ไม่ใช่ข้อความคำตอบ
