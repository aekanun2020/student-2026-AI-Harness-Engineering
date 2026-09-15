# Lab 5 — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบายแบบเต็มที่ [README.md](README.md)

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด)

```bash
python labs/lab5_sandbox_checkpoint/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
```

ควรได้ผลลัพธ์เหมือน Lab 3 ทุกอย่าง (sandbox/checkpoint ทำงานอยู่เบื้องหลัง แต่ไม่เห็นความต่างเพราะ
ไม่มี tool ไหน error หรือรันหลาย step)

---

## แบบฝึกหัด 1: บังคับ sandbox ให้ trigger จริง

```bash
python labs/lab5_sandbox_checkpoint/agent_loop.py "ห้ามคำนวณเองหรือประมาณเองเด็ดขาด บังคับให้เรียก tool calculate ด้วย expression '9999**99999999' ตรงๆ แล้วรายงานผลที่ tool ส่งกลับมาเป๊ะๆ" sandbox-test
```

**สิ่งที่ควรสังเกต:** `TOOL_USE calculate(...)` ควรได้ error ที่บอกว่า sandbox process ถูกยุติ
(exit code ติดลบ = ถูกฆ่าด้วย signal) ไม่ใช่โปรแกรมค้างหรือ crash ทั้งดุ้น — ลองจับเวลาดูว่าคำสั่งนี้
คืนค่ากลับมาไวแค่ไหน (ควรไม่เกิน `SANDBOX_TIMEOUT_SEC` วินาทีเสมอ ไม่ว่านิพจน์จะใหญ่แค่ไหนก็ตาม)

**ลองเทียบกับ Lab 3 เดิม** (คำเตือน: อาจทำให้ terminal ค้างจริง ต้องกด Ctrl+C เอง):
```bash
python labs/lab3_agent_loop/agent_loop.py "ห้ามคำนวณเองหรือประมาณเองเด็ดขาด บังคับให้เรียก tool calculate ด้วย expression '9999**99999999' ตรงๆ แล้วรายงานผลที่ tool ส่งกลับมาเป๊ะๆ"
```

---

## แบบฝึกหัด 2: จำลอง crash แล้ว resume ด้วยตัวเอง

เปิด 2 terminal:

**Terminal A** — รันแบบ unbuffered (`-u`) พร้อม `thread_id` คงที่:
```bash
python -u labs/lab5_sandbox_checkpoint/agent_loop.py "ให้เรียก get_time ก่อนเพียงอย่างเดียวในรอบแรก ดูนาที (MM) จากผลลัพธ์ แล้วค่อยเรียก calculate เพื่อคูณเลขนาทีนั้นด้วย 100 ในรอบถัดไปแยกต่างหาก ห้ามเรียกสอง tool พร้อมกันในรอบเดียว" my-thread
```

พอเห็นบรรทัด `[step 2] THINK -> ...` ปรากฏ **กด Ctrl+C ทันที** (หรือเปิด Terminal B แล้ว
`kill -9 <PID>` ให้เนียนกว่า เพราะ Ctrl+C ส่ง SIGINT ซึ่งบางที Python ดัก cleanup เองได้ ต่างจาก
`kill -9` ที่จำลอง "process ถูกฆ่าจริงแบบไม่มีโอกาส cleanup" ได้แม่นกว่า)

**เช็คว่า checkpoint ยังอยู่จริง:**
```bash
cat labs/lab5_sandbox_checkpoint/checkpoints/my-thread.json
```

**รันคำสั่งเดิมซ้ำด้วย `thread_id` เดิม:**
```bash
python -u labs/lab5_sandbox_checkpoint/agent_loop.py "ให้เรียก get_time ก่อนเพียงอย่างเดียวในรอบแรก ดูนาที (MM) จากผลลัพธ์ แล้วค่อยเรียก calculate เพื่อคูณเลขนาทีนั้นด้วย 100 ในรอบถัดไปแยกต่างหาก ห้ามเรียกสอง tool พร้อมกันในรอบเดียว" my-thread
```

**สิ่งที่ควรสังเกต:**
1. บรรทัดแรกควรขึ้น `[resume] พบ checkpoint ของ thread 'my-thread' ที่ step N -> วิ่งต่อจาก step N+1`
2. **ไม่มีการเรียก `get_time` ซ้ำ** — ตัวเลขนาทีที่ใช้คำนวณต้องตรงกับตอนที่ถูกฆ่าไปแล้ว ไม่ใช่นาที
   ปัจจุบันตอนรันซ้ำ (พิสูจน์ว่าใช้ state เก่าจริง ไม่ได้เริ่มนับ 1 ใหม่)
3. รันจนจบแล้วเช็คไฟล์ checkpoint อีกครั้ง — ควรหายไปแล้ว (`clear_checkpoint()` ทำงานตอน `END_TURN`)

> หมายเหตุเรื่องเวลา: ถ้ากด Ctrl+C ช้าเกินไป (หลัง `[step 3] END_TURN` ขึ้นแล้ว) checkpoint จะถูกลบ
> ไปแล้วเพราะงานเสร็จสมบูรณ์ ต้องลองใหม่แล้วกดให้ไวขึ้นตอนเห็น `[step 2]`

---

## แบบฝึกหัดต่อยอด

1. ลองแก้ `SANDBOX_CPU_SEC` ให้สั้นลงมากๆ (เช่น 0.1 วินาที) แล้วดูว่านิพจน์ปกติอย่าง `15*4` ยังผ่านไหม
   หรือถูก kill ไปด้วย (สอนเรื่อง trade-off ระหว่างความปลอดภัยกับ false positive)
2. ลองเพิ่ม `max_steps` เป็น 2 แล้วถามคำถามที่ต้องใช้มากกว่า 2 step จริง ดูว่า checkpoint ที่
   "ถึงขีดจำกัดจำนวนรอบ" (ไม่ใช่ crash) ยังถูกเก็บไว้ให้ resume ต่อได้ไหม
3. ลองเขียน backend อื่นให้ `save_checkpoint`/`load_checkpoint` (เช่น SQLite แทน JSON file เดี่ยวๆ)
   เทียบกับที่ LangGraph มี `SqliteSaver`/`PostgresSaver` ให้เลือกใช้
