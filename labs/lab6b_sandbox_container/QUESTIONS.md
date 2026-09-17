# Lab 6b — คำถามตัวอย่าง และแบบฝึกหัด

> ดูคำอธิบายแบบเต็มที่ [README.md](README.md)

> **ก่อนรันทุกคำสั่งในหน้านี้:** เปิด terminal → `cd` เข้าโฟลเดอร์ repo → `source .venv/bin/activate`
> (Windows: `.venv\Scripts\activate` และใช้ `python` แทน `python3`) — ต้องเห็น `(.venv)` หน้า prompt
> และ Docker ต้องทำงานอยู่ (`docker info` ไม่ error) · สร้าง image ครั้งแรก: `docker build -t lab6b-sandbox labs/lab6b_sandbox_container`

## คำถามตัวอย่าง (ค่า default ที่ฝังอยู่ในโค้ด)

```bash
python labs/lab6b_sandbox_container/agent_loop.py "อ่านไฟล์ hello.txt แล้วบอกว่า repo นี้มีกี่ Lab แล้ว 15*4 เท่ากับเท่าไร"
```

**บรรทัดที่ต้องมองหา:** `[sandbox] container พร้อม — tools ที่ประกาศจากในห้อง: ['calculate', 'read_file', 'run_python']`
คือ agent ไม่ได้เขียนรายการ tool เอง แต่ถามห้องว่ามีอะไร (`list_tools`) แล้ว `TOOL_USE read_file(...)` ได้เนื้อไฟล์กลับมาจากในห้อง

---

## แบบฝึกหัด 1: 🟢 ลองอ่านไฟล์นอกห้อง

```bash
python labs/lab6b_sandbox_container/agent_loop.py "บังคับให้เรียก tool read_file ด้วย path '../../.env' แล้วรายงานผลที่ tool ส่งกลับมาเป๊ะๆ ห้ามเดา"
```

**บรรทัดที่ต้องมองหา:** `TOOL_USE read_file({'path': '../../.env'}) -> error: อ่านได้เฉพาะไฟล์ใน workspace (/work) เท่านั้น`
— นี่คือ **guardrail ที่ประตู** (โค้ดใน `mcp_server.py`) ดักก่อน · และต่อให้เขียนโค้ดผ่านประตูนี้ได้ ผนังก็ยังกั้นอยู่:
ลองแบบฝึกหัด 2

## แบบฝึกหัด 2: 🟢 ดูด้วยตาว่าผนังกั้นอะไรได้บ้าง (ไม่เรียก LLM ไม่เสียเงิน)

```bash
python labs/lab6b_sandbox_container/probe_sandbox.py
```

**บรรทัดที่ต้องมองหา และเทียบกับ `probe_sandbox.py` ของ Lab 6:**

| ข้อ | Lab 6 เห็น | Lab 6b ต้องเห็น |
| --- | --- | --- |
| 1) API key | `api_key_visible: false` | `api_key_visible: false` และ `uid: 10001` (ไม่ใช่ root) |
| 2) อ่านไฟล์นอกห้อง | `can_read_outside: true` ❌ | `host_home_visible: false` ✅ เห็นแค่ `/work` |
| 3) เขียนไฟล์ | `OSError: File too large` | `/work` และ `/app` เป็น `OSError`, เขียนได้แค่ `/tmp` |
| 4) network | (Lab 6 ไม่ได้กั้น) | `network: blocked ... Network is unreachable` ✅ |
| 5) CPU bomb | `exit code -24` | `exit code -24` เหมือนกัน แล้วข้อ 6 ยังได้ `60` |

## แบบฝึกหัด 3: 🟢 ให้ AI เขียนโค้ดแล้วรันในห้อง

```bash
python labs/lab6b_sandbox_container/agent_loop.py "ใช้ tool run_python เขียนโค้ดหาเลขเฉพาะ 10 ตัวแรกแล้วพิมพ์ออกมา แล้วรายงานผล"
```

**บรรทัดที่ต้องมองหา:** `TOOL_USE run_python({'code': ...}) -> [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]` — โค้ดที่โมเดลเขียน
รันในห้องที่ไม่มี network, เขียนได้แค่ `/tmp`, ไม่มี credential · ลองสั่งให้มัน "ดาวน์โหลดอะไรจากอินเทอร์เน็ต" ดู
จะได้ error เรื่อง network กลับมาแทน — ข้อความต่างกันตามวิธีที่โมเดลเขียนโค้ด: ใช้ชื่อโดเมน (เช่น `example.com`)
จะได้ `Temporary failure in name resolution` เพราะแปลงชื่อเป็น IP ไม่ได้ตั้งแต่แรก · ต่อด้วยหมายเลข IP ตรงๆ
จะได้ `Network is unreachable` · ทั้งสองแบบแปลว่าเดียวกันคือห้องนี้ไม่มีทางออกสู่อินเทอร์เน็ต

---

## แบบฝึกหัดต่อยอด — 🟡/🔴 สำหรับคนที่เขียน Python ได้แล้ว (ข้ามได้)

1. 🟡 เปิด `DOCKER_ARGS` ใน `agent_loop.py` ลบ `"--network", "none"` ออก แล้วรัน `probe_sandbox.py` ซ้ำ — ข้อ 4 จะกลายเป็น
   `CONNECTED` ทันที (เห็นว่าผนังด้าน network มาจาก flag เดียว ไม่ใช่จากโค้ด Python)
2. 🟡 เปลี่ยน `:ro` เป็น `:rw` แล้วดูว่าข้อ 3 เขียน `/work/escape.txt` ได้ — แล้วคิดว่า tool ตัวไหนใน repo ควรได้สิทธิ์เขียนบ้าง
3. 🔴 เปลี่ยน `--network none` เป็น network ที่มี allowlist (เช่น proxy container ที่ปล่อยเฉพาะโดเมนที่กำหนด) ตามแนวทาง
   Claude Code sandbox — เพื่อให้ tool ที่ต้องต่อเน็ตบางตัวใช้ได้โดยไม่เปิดทั้งหมด
4. 🔴 นำ checkpoint ของ Lab 5 มารวม: ห้องถูกสร้างใหม่ทุกครั้ง แต่ประวัติการสนทนาควรรอดข้าม process — ต้องเซฟอะไรฝั่ง host
   และอะไรที่ไม่ควรเซฟ (ผลจากในห้องที่อ้างถึง `/tmp` ซึ่งหายไปแล้ว)

> เฉลยเชิงพฤติกรรม ไม่ใช่เฉลยคำตอบตายตัว — สิ่งที่ต้องตรงคือบรรทัด `TOOL_USE …` และผลของ probe ไม่ใช่ข้อความคำตอบของ AI
