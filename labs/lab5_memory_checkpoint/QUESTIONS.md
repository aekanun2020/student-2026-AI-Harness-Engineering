# Lab 5 — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบายแบบเต็มที่ [README.md](README.md)

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด)

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง" my-thread
```

รันครั้งแรกจะไม่มี checkpoint ให้โหลด agent จะเห็นแค่ note เริ่มต้น (`ผู้ใช้ชื่อผู้เรียนในหลักสูตร...`)

---

## แบบฝึกหัด 1: พิสูจน์ external memory ข้าม process

```bash
python labs/lab5_memory_checkpoint/agent_loop.py "ผมชอบเลข 42 มากที่สุด ช่วยคำนวณ 42*2 ให้หน่อย" mem-demo
python labs/lab5_memory_checkpoint/agent_loop.py "เมื่อกี้ผมบอกว่าผมชอบเลขอะไร แล้วผลคูณที่ขอให้คำนวณคือเท่าไร" mem-demo
```

**สิ่งที่ควรสังเกต:** คำสั่งที่สองเป็น `python` process ใหม่เอี่ยม ไม่มี state อะไรค้างใน RAM จาก
รอบแรกเลย แต่ควรตอบถูกทั้งเลข 42 และผลลัพธ์ 84 ได้ — เพราะโหลดมาจาก
`labs/lab5_memory_checkpoint/checkpoints/mem-demo.json`

**ลองเทียบกับ Lab 3** (ที่ไม่มี memory ข้าม process เลย): รันคำถามที่ 2 กับ `agent_loop.py` ของ
Lab 3 ดูว่ามันตอบไม่ได้เลยว่าคุณชอบเลขอะไร (เพราะไม่มีการจำอะไรข้ามการรันเลย)

---

## แบบฝึกหัด 2: บังคับให้ compaction ทำงาน

รันคำถามสั้นๆ ซ้ำหลายครั้งด้วย `thread_id` เดียวกัน (แต่ละครั้งคือ 1 turn ~2 ข้อความในบทสนทนา
ต้องการ ~12 ข้อความถึงจะ trigger):

```bash
for i in 1 2 3 4 5 6; do
  python labs/lab5_memory_checkpoint/agent_loop.py "คำนวณ $i บวก $i ให้หน่อย" compact-demo
done
```

**สิ่งที่ควรสังเกต:** ที่ turn ประมาณที่ 3-4 ควรเห็นบรรทัด `[compaction] ย่อ N ข้อความเป็นสรุป 1 ก้อน`
โผล่ขึ้นมา แล้ว turn ถัดไปที่ `[resume]` ควรรายงาน `history` สั้นลงกว่าที่ควรจะเป็นถ้าไม่มี compaction
เลย (ลองนับดูว่าถ้าไม่ compact จะมีกี่ข้อความ เทียบกับที่เห็นจริง)

---

## แบบฝึกหัด 3: จำลอง crash กลาง turn แล้ว resume (ต้องใช้ 2 terminal หรือสคริปต์)

เหมือนแบบฝึกหัดใน [Lab 6](../lab6_sandbox/README.md) แต่ประยุกต์กับ memory — ใช้คำถามที่บังคับ
ให้ต้องมี 2 step จริง:

```bash
python -u labs/lab5_memory_checkpoint/agent_loop.py "ให้เรียก get_time ก่อนเพียงอย่างเดียวในรอบแรก ดูนาที (MM) จากผลลัพธ์ แล้วค่อยเรียก calculate เพื่อคูณเลขนาทีนั้นด้วย 100 ในรอบถัดไปแยกต่างหาก ห้ามเรียกสอง tool พร้อมกันในรอบเดียว" crash-test
```

พอเห็น `[step 2] THINK -> ...` ปรากฏ กด **Ctrl+C** หรือ `kill -9 <PID>` จาก terminal อื่นทันที —
เช็ค `labs/lab5_memory_checkpoint/checkpoints/crash-test.json` ว่า `"pending": true` แล้วรันคำสั่ง
เดิมซ้ำด้วย `thread_id` เดิม (ใส่คำถามอะไรก็ได้ เพราะตอน `pending=true` มันจะไม่ใช้คำถามใหม่)

**สิ่งที่ควรสังเกต:** ต้องเห็น `[resume] turn ก่อนหน้าค้างกลางทาง` แล้ว**ไม่เรียก `get_time` ซ้ำ**
ใช้เลขนาทีเดิมจากก่อนถูกฆ่าไปคำนวณต่อเลย

---

## แบบฝึกหัดต่อยอด

1. ลองลด `COMPACT_AFTER_MESSAGES` ให้ต่ำมากๆ (เช่น 4) แล้วดูว่า compaction ถี่ขึ้นแค่ไหน สังเกตว่า
   note (`mem.notes`) ไม่เคยถูก compact ทิ้งเลยไม่ว่าจะรันกี่รอบ (ต่างจาก `history`)
2. ลองเพิ่ม note เพิ่มเติมระหว่างการสนทนา (เช่น เพิ่มบรรทัด `mem.add_note(...)` ใน `main()` ตามเงื่อนไข
   บางอย่าง) แล้วดูว่า note ใหม่นี้โผล่ใน `context()` ของทุก turn ถัดไปจริงไหม แม้จะ compact ไปแล้ว
3. เทียบกับ [LangGraph checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence)
   ที่มี backend หลายแบบ (`InMemorySaver`/`SqliteSaver`/`PostgresSaver`) — ลองเขียน backend อื่นให้
   `save_checkpoint`/`load_checkpoint` ของเรา (เช่น SQLite) แทนไฟล์ JSON เดี่ยวๆ
