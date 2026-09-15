# Lab 1 — ติดตั้งและตรวจสอบสภาพแวดล้อม

> ดัดแปลงจาก [labs/lab1_setup/](https://github.com/aekanun2020/Python-Agent-LangGraph/tree/main/labs/lab1_setup)
> ของ [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph) — ต้นฉบับตรวจ
> 2 อย่าง (LLM + MCP MSSQL Server) แต่ **repo นี้ไม่มี MCP server ให้ต่อเลย** จึงตัดส่วนตรวจ MCP ออก
> เหลือแค่การตรวจ LLM ซึ่งเป็น precondition ที่ Lab อื่นในนี้ใช้จริง
>
> **ตำแหน่งใน [8 Layer ของ repo](../../README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers):**
> ตรวจว่า LLM (แกนกลางของทุก layer) พร้อมใช้ ก่อนจะเริ่มประกอบ layer อื่น

---

## จุดประสงค์การเรียนรู้

- ตั้งค่า Python environment (แนะนำ Miniconda, Python 3.11)
- เชื่อมต่อ LLM API ผ่าน **OpenRouter** โดยใช้ OpenAI SDK + `base_url` (thin client)
- ใช้ `check_env.py` เป็น precondition gate ก่อนเข้าสู่ Lab ถัดไป

---

## ขั้นตอน Setup สภาพแวดล้อม (ทำครั้งเดียว — ใช้ร่วมกันทุก Lab ใน repo นี้)

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

### 3) ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 4) ตั้งค่า environment variables

```bash
cp .env.example .env
```

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

return code 0 (ผ่าน) หรือ 1 (ยังไม่ผ่าน) ตามผลของ `check_llm()`

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
