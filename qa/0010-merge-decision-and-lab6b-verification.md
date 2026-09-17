# Q&A Log — Entry 0010

**วันที่:** 2026-09-17
**Project:** student-2026-AI-Harness-Engineering

---

## คำถามที่ 1 (verbatim)

ตอนนี้ merge ได้เลย หรอควรทำมั้ย เพราะผู้เรียนหลายคนโหลด branch: fable ... ไปแล้ว

## คำตอบที่ 1 (verbatim)

**merge ได้เลย และผมแนะนำให้ merge** — การ merge ไม่ทำให้ผู้เรียนที่โหลด branch ไปแล้วพัง

**เหตุผล:** merge คือการเอา commit ทั้ง 22 ตัวไปใส่ใน `main` ส่วน branch ยังอยู่ที่เดิมไม่ถูกแตะ ผู้เรียนที่ `git checkout fable-revision-docs-chat-users` ไว้แล้ว `git pull` ได้ตามปกติ **ตราบใดที่ไม่ลบ branch ทิ้ง** (GitHub จะขึ้นปุ่ม "Delete branch" หลัง merge — **อย่ากด**)

ตรวจสถานะให้แล้ว: PR #1 เป็น `MERGEABLE` + `CLEAN` · `main` ตามหลังอยู่ 22 commit และ**ไม่มี commit ไหนใน main ที่ branch ไม่มี** แปลว่า merge ได้แบบไม่มีทางชนกันเลย

**ทำไมถึงควรทำตอนนี้ ไม่ใช่รอ:**
- ตอนนี้ใครก็ตามที่ `git clone` ใหม่จะได้ `main` ซึ่งเป็นของเก่าที่ไม่มี Lab 3a/4/5/6/6b เลย — ผู้เรียนคนถัดไปที่ไม่ได้อ่านคำสั่ง checkout จะเจอ repo ที่ใช้ไม่ได้
- ยิ่งรอ ยิ่งมีคนโหลด main ผิดๆ ไปเรื่อยๆ

**ข้อเดียวที่ต้องตัดสินใจต่อ:** หลัง merge แล้วงานใหม่จะไปอยู่ที่ไหน เพราะถ้า commit ใหม่เข้า `main` อย่างเดียว คนที่ยังอยู่บน branch จะไม่ได้ของใหม่ ผมแนะนำ:

1. merge PR #1 (เลือก **"Create a merge commit"** ปกติได้เลย)
2. **ไม่ลบ branch**
3. บอกผู้เรียนครั้งเดียวว่าให้ย้ายมา main เมื่อสะดวก:
```bash
git checkout main && git pull
```
4. งานใหม่หลังจากนี้ทำบน branch ใหม่ (ใช้ prefix `fable-revision-` เหมือนเดิม) แล้ว merge เข้า main เป็นรอบๆ

**สิ่งที่จะถูกเผยแพร่สู่ main** มี 31 ไฟล์เปลี่ยน รวม Lab 6b (sandbox ใน Docker) ที่ทำโดย session อื่นของคุณ — ผมไม่ได้รันทดสอบ Lab 6b เอง ถ้าอยากให้ชัวร์ก่อน merge ผมทดสอบให้ได้ (ต้องมี Docker ทำงานอยู่) ส่วน Lab 3a/4/5/6 ผมรันทดสอบครบแล้วเมื่อวานนี้

จะให้ผม merge ให้เลย หรือคุณกดเองบน GitHub ก็ได้ครับ — บอกมาได้

---

## คำถามที่ 2 (verbatim)

ทดสอบ lab 6b ก่อน แล้วค่อย merge

## คำตอบที่ 2 (verbatim)

merge เรียบร้อยแล้ว หลังทดสอบ Lab 6b ผ่านครบทุกข้อ

**ผลทดสอบ Lab 6b (รันจริงกับ Docker container)**

| แบบฝึกหัด | สิ่งที่เอกสารระบุ | ผลจริง |
|---|---|---|
| คำถามตัวอย่าง | container ประกาศ 3 tool แล้วอ่านไฟล์จากในห้องได้ | `['calculate', 'read_file', 'run_python']` แล้ว `TOOL_USE read_file` ได้เนื้อไฟล์ พร้อม `calculate` → 60 |
| 1 อ่านไฟล์นอกห้อง | ได้ `error: อ่านได้เฉพาะไฟล์ใน workspace (/work)` | ตรงเป๊ะ guardrail ที่ประตูดักไว้ |
| 2 probe ทั้ง 6 ข้อ | api_key ไม่เห็น, uid 10001, host_home ไม่เห็น, เขียนได้แค่ `/tmp`, network blocked, CPU bomb `-24` แล้วยังได้ 60 | ตรงทั้ง 6 ข้อ |
| 3 run_python | `[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]` | ตรงเป๊ะ |

**เจอ 1 จุดที่เอกสารระบุผิด แก้ก่อน merge แล้ว** (commit `99bd40b`) — แบบฝึกหัด 3 บอกว่าถ้าสั่งดาวน์โหลดจะได้ `Network is unreachable` แต่จริงๆ โมเดลเขียนโค้ดด้วยชื่อโดเมน จึงติด DNS ก่อนและได้ `Temporary failure in name resolution` แทน ตอนนี้เอกสารอธิบายทั้งสองแบบแล้ว

**สถานะ repo ตอนนี้**
- PR #1 = **MERGED** ผ่าน merge commit `9af02ac`
- `main` มีเนื้อหาครบ ตรงกับ branch ทุกไฟล์ (diff ว่างเปล่า)
- **branch `fable-revision-docs-chat-users` ยังอยู่** ไม่ได้ลบ ผู้เรียนที่โหลดไปแล้ว `git pull` ได้ตามปกติ
- ข้อจำกัด byte-identical ของ Lab 3 ยังอยู่ครบ ตรวจแล้วทั้ง `agent_loop.py` และ 97 บรรทัดแรกของ README

**สิ่งที่ควรบอกผู้เรียน** — ตอนนี้ `git clone` ธรรมดาได้ของครบแล้วไม่ต้อง checkout อะไร ส่วนคนที่อยู่บน branch เดิม ให้ย้ายมา main เมื่อสะดวก:

```bash
git checkout main && git pull
```

งานใหม่หลังจากนี้ผมแนะนำให้เปิด branch ใหม่ (prefix `fable-revision-` เหมือนเดิม) แล้ว merge เข้า main เป็นรอบๆ ไม่ commit ตรงเข้า main

---

## ผลรันดิบของการทดสอบ Lab 6b (เก็บไว้อ้างอิง)

### คำถามตัวอย่าง

```
[user] อ่านไฟล์ hello.txt แล้วบอกว่า repo นี้มีกี่ Lab แล้ว 15*4 เท่ากับเท่าไร
[sandbox] container พร้อม — tools ที่ประกาศจากในห้อง: ['calculate', 'read_file', 'run_python']
[step 1] THINK -> ขอเรียก 2 tool
           TOOL_USE read_file({'path': 'hello.txt'}) -> นี่คือไฟล์ตัวอย่างใน workspace ของ Lab 6b
container เห็นโฟลเดอร์นี้ที่ /work แบบ read-only เท่านั้น
repo นี้มี Lab 1, 2, 3, 3a, 4, 5, 6 และ 6b

           TOOL_USE calculate({'expression': '15*4'}) -> 60
[step 2] END_TURN
```

### แบบฝึกหัด 1 — อ่านไฟล์นอกห้อง

```
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE read_file({'path': '../../.env'}) -> error: อ่านได้เฉพาะไฟล์ใน workspace (/work) เท่านั้น (ห้ามใช้ .. หรือ path เต็ม)
[step 2] END_TURN
```

### แบบฝึกหัด 2 — probe (ไม่เรียก LLM)

```
[host] OPENROUTER_API_KEY ใน os.environ ของ host: มี

== 1) env / user / cwd ที่เห็นในห้อง
   {"api_key_visible": false, "env_var_count": 8, "uid": 10001, "cwd": "/tmp"}

== 2) อ่านไฟล์: ใน /work ได้ไหม / นอก /work (โฟลเดอร์บ้านของ host) มีไหม
   {"work_files": ["hello.txt"], "host_home_visible": false, "root_dirs": [".dockerenv", "app", "bin", "boot", "dev", "etc", "home", "lib"]}

== 3) เขียนไฟล์: /work (ro mount), /app (read-only fs), /tmp (tmpfs)
   {"/work/escape.txt": "OSError", "/app/escape.txt": "OSError", "/tmp/ok.txt": "WRITTEN"}

== 4) network: ต่อออก 1.1.1.1:53 ได้ไหม
   {"network": "blocked", "error": "OSError: [Errno 101] Network is unreachable"}

== 5) CPU bomb ผ่าน calculate (RLIMIT_CPU ใน Linux container)
   error: process ถูกยุติ (exit code -24, เกิน CPU/memory limit หรือโค้ดพัง)

== 6) server ในห้องยังรับงานต่อได้ไหม หลังข้อ 5
   60
```

### แบบฝึกหัด 3 — run_python

```
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE run_python({'code': '...is_prime...'}) -> เลขเฉพาะ 10 ตัวแรก: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
[step 2] END_TURN
```

### ทดสอบเพิ่ม — สั่งให้ดาวน์โหลดจากอินเทอร์เน็ต (จุดที่พบว่าเอกสารผิด)

```
           TOOL_USE run_python({'code': '...urllib.request.urlopen("https://example.com")...'}) -> error: process ถูกยุติ (exit code 1, เกิน CPU/memory limit หรือโค้ดพัง)
[stderr] urllib.error.URLError: <urlopen error [Errno -3] Temporary failure in name resolution>
```

เอกสารเดิมเขียนว่าจะได้ `Network is unreachable` ซึ่งเป็นข้อความของการต่อด้วยหมายเลข IP ตรงๆ (อย่างที่ `probe_sandbox.py`
ทำในข้อ 4) แต่โมเดลเขียนโค้ดด้วยชื่อโดเมน จึงติดขั้น DNS ก่อนและได้ `Temporary failure in name resolution` แทน —
แก้ QUESTIONS.md ให้อธิบายทั้งสองแบบแล้วใน commit `99bd40b` ก่อน merge
