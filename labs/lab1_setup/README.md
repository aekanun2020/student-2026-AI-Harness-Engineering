# Lab 1 — ติดตั้งและตรวจสอบสภาพแวดล้อม

> ดัดแปลงจาก Lab 1 ของ repo ต้นทางของหลักสูตร — ต้นฉบับตรวจ
> 2 อย่าง (LLM + MCP MSSQL Server) แต่ **repo นี้ไม่มี MCP server ให้ต่อเลย** จึงตัดส่วนตรวจ MCP ออก
> เหลือแค่การตรวจ LLM ซึ่งเป็น precondition ที่ Lab อื่นในนี้ใช้จริง
>
> **ตำแหน่งใน [8 Layer ของ repo](../../README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers):**
> ตรวจว่า LLM (แกนกลางของทุก layer) พร้อมใช้ ก่อนจะเริ่มประกอบ layer อื่น

---

## จุดประสงค์การเรียนรู้

- ตั้งค่า Python environment (แนะนำ Miniconda, Python 3.11)
- เชื่อมต่อ LLM API ผ่าน **OpenRouter** โดยใช้ OpenAI SDK + `base_url` (thin client) —
  แปลว่าเราใช้ไลบรารีของ OpenAI แต่ชี้ไปที่ OpenRouter ซึ่งเป็นตัวกลางที่ให้เลือกโมเดลจากหลายบริษัท
  (Anthropic, OpenAI, Meta ฯลฯ) ได้ด้วยคีย์เดียว
- ใช้ `check_env.py` เป็น precondition gate ก่อนเข้าสู่ Lab ถัดไป

---

## ขั้นตอน Setup สภาพแวดล้อม (ทำครั้งเดียว — ใช้ร่วมกันทุก Lab ใน repo นี้)

### 0) ติดตั้ง Python (ถ้ายังไม่มี)

ดาวน์โหลด Python 3.11 ขึ้นไปจาก https://www.python.org/downloads/ (Windows: ตอนติดตั้งติ๊ก
**"Add Python to PATH"** ด้วย) แล้วเปิด terminal เช็คว่าใช้ได้:

```bash
python3 --version    # ควรเห็น Python 3.11.x หรือใหม่กว่า (Windows อาจต้องพิมพ์ python แทน python3)
```

### 1) Clone repository

```bash
git clone https://github.com/aekanun2020/student-2026-AI-Harness-Engineering.git
cd student-2026-AI-Harness-Engineering
```

### 2) สร้างและเปิดใช้งาน virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

venv = กล่องแยกสำหรับติดตั้งไลบรารีของโปรเจกต์นี้โดยเฉพาะ ไม่ปนกับโปรแกรมอื่นในเครื่อง —
ถ้าเห็น `(.venv)` โผล่หน้า prompt ใน terminal แปลว่าเปิดใช้งานแล้ว

> **⚠️ จุดที่คนติดบ่อยที่สุด:** บรรทัด `source .venv/bin/activate` ต้องพิมพ์ใหม่**ทุกครั้งที่เปิด terminal ใหม่**
> (สร้าง venv ครั้งเดียวพอ แต่ต้อง activate ทุกครั้ง) — ถ้าวันนี้รันได้แต่พรุ่งนี้เจอ `ModuleNotFoundError: No module named 'openai'`
> เกือบทุกครั้งคือลืมขั้นนี้

### 3) ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 4) ตั้งค่า environment variables

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

> ไฟล์ที่ชื่อขึ้นต้นด้วยจุด (`.env`) จะ**ถูกซ่อน**ใน Finder/File Explorer ตามค่าเริ่มต้น หาไม่เจอไม่ต้องแปลกใจ —
> เปิดจาก terminal ได้เลย: `open -e .env` (Mac) หรือ `notepad .env` (Windows)

จากนั้นแก้ไขไฟล์ `.env` ให้มีค่าดังนี้:

| ตัวแปร | ค่า | หมายเหตุ |
|--------|-----|----------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | ขอคีย์ได้ที่ https://openrouter.ai/keys |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | endpoint มาตรฐาน OpenRouter |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4.6` | โมเดลที่ทดสอบแล้ว |

> ⚠️ ไฟล์ `.env` ถูก `.gitignore` ไว้แล้ว — **ห้าม commit คีย์จริงขึ้น repo เด็ดขาด**

---

## วิธีรัน Lab 1

```bash
python labs/lab1_setup/check_env.py
```

---

## อธิบายจุดสำคัญของโค้ด

ไฟล์: [`check_env.py`](check_env.py)

### `check_llm()` — ตรวจ OpenRouter (LLM)

เรียก `llm.chat()` ด้วย prompt สั้น (`"ตอบสั้น ๆ คำเดียวว่า 'พร้อม'"`) แล้วอ่าน `resp.choices[0].message.content`
และแสดงชื่อโมเดลจาก `config.OPENROUTER_MODEL` เพื่อยืนยันว่า API key ถูกต้องและเชื่อมต่อ OpenRouter ได้จริง

### `main()` — gate ก่อนไป Lab 2

สรุปผลเป็นบรรทัดเดียว: เห็น **✅** = พร้อม ไป Lab 2 ได้ · เห็น **⚠️** = ยังไม่พร้อม อ่านบรรทัด ❌ ด้านบนว่าติดอะไร
(ในเชิงเทคนิค: โปรแกรมจบด้วย return code 0 เมื่อผ่าน และ 1 เมื่อไม่ผ่าน — ไม่ต้องสนใจถ้ายังไม่เขียนโค้ด)

---

## ผลลัพธ์ที่คาดหวัง

```
============================================================
Lab 1 — ตรวจสอบสภาพแวดล้อมการพัฒนา
============================================================
ตรวจ OpenRouter (LLM) ...
      โมเดล anthropic/claude-sonnet-4.6 ตอบ: 'พร้อม'
------------------------------------------------------------
✅ environment พร้อม — ไปต่อ Lab 2 ได้เลย
```
