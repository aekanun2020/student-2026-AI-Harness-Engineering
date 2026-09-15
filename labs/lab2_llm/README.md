# Lab 2 — เรียกใช้ LLM API ครั้งแรก เปรียบเทียบโมเดล และดูค่าใช้จ่ายจริง

> ดัดแปลงจาก Lab 2 ของ repo ต้นทางของหลักสูตร **Agentic AI Development with Python** (Module 1.2) —
> เพิ่มการแสดง**ค่าใช้จ่ายจริงเป็นเงิน**ของทุกครั้งที่เรียก API โค้ดส่วนอื่นเหมือนต้นฉบับ

> **ตำแหน่งใน [8 Layer ของ repo](../../README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers):** แกนกลางสุด คือตัว **LLM (reasoning/decision)** เอง — เรียกโมเดลตรงๆ ยังไม่มี layer ห่อ (ยังไม่ใช่ agent loop)

---

## จุดประสงค์การเรียนรู้

- เข้าใจโครงสร้าง **messages** และ **role** (system / user / assistant) ที่ใช้กับ LLM API
- อ่านและตีความ **token usage** (prompt / completion / total) เพื่อบริหารต้นทุนและ context window
- เห็น**ค่าใช้จ่ายจริงเป็นเงิน**ที่ถูกหักจากเครดิต OpenRouter ในทุกครั้งที่เรียก — และเข้าใจว่ามันคิดจากอะไร
- เปรียบเทียบผลลัพธ์ เวลาตอบสนอง และราคาของหลายโมเดลบน OpenRouter เพื่อเลือกโมเดลให้เหมาะกับงาน

---

## สิ่งที่ต้องเตรียมก่อน (Prerequisites)

- ทำ Setup สภาพแวดล้อมใน [Lab 1](../lab1_setup/README.md) ให้เสร็จก่อน (venv + `.env` ที่มี API key)

---

## วิธีรัน

รันจาก root ของ repo (โฟลเดอร์ที่มี README.md หลัก) หลัง activate venv แล้ว:

```bash
# ไฟล์ที่ 1: เรียก LLM ครั้งแรก + ดู token usage + ค่าใช้จ่าย
python labs/lab2_llm/first_llm.py "อธิบาย Agent Loop ใน 2 ประโยค"

# ไฟล์ที่ 2: เปรียบเทียบหลายโมเดลด้วยคำถามเดียวกัน (เรียก 3 โมเดล = 3 ค่าใช้จ่าย)
python labs/lab2_llm/compare_models.py
```

---

## ค่าใช้จ่ายเกิดขึ้นยังไง และดูได้จากไหน

### OpenRouter คิดเงินยังไง

- **ไม่ใช่เหมาจ่ายรายเดือน** แบบ ChatGPT Plus — ต้องเติมเงินเป็นเครดิต (USD) ไว้ก่อน แล้วถูกหักทีละนิดทุกครั้งที่เรียก
- หักตาม **จำนวน token** ที่ใช้ ไม่ใช่ตามจำนวนครั้ง — แต่ละโมเดลมีราคาต่อ 1 ล้าน token ต่างกัน และ
  **token ขาเข้า (prompt) กับขาออก (completion) ราคาไม่เท่ากัน** ขาออกมักแพงกว่าหลายเท่า
- ดังนั้น: คำถามยาว + คำตอบยาว + โมเดลแพง = จ่ายมาก / คำถามสั้น + `max_tokens` ต่ำ + โมเดลเล็ก = จ่ายน้อย

### ดูค่าใช้จ่ายจริงจาก response ได้เลย ไม่ต้องคำนวณเอง

OpenRouter มีฟีเจอร์ **usage accounting** — ถ้าส่ง `"usage": {"include": true}` ไปกับ request มันจะแนบ
`usage.cost` (USD ที่หักจริง) กลับมาใน response โค้ดของ Lab นี้ส่งผ่าน `**kwargs` ของ `llm.chat()`:

```python
USAGE_ACCOUNTING = {"extra_body": {"usage": {"include": True}}}
resp = llm.chat(messages=messages, max_tokens=max_tokens, **USAGE_ACCOUNTING)

cost = getattr(resp.usage, "cost", None)   # USD ที่ OpenRouter หักจริงสำหรับ call นี้
```

ทำไมใช้ `getattr(..., None)`: ไม่ใช่ทุก provider ที่แนบ `cost` มา — ถ้าไม่มี โปรแกรมจะพิมพ์ว่าไม่มีข้อมูล
แทนที่จะพัง

`resp.usage` ยังมี `cost_details` แยกให้ดูด้วยว่าเป็นค่า prompt เท่าไร ค่า completion เท่าไร
(ลอง `print(resp.usage.model_extra)` ดูได้)

### ตัวเลขจริงจากการทดสอบ

| การเรียก | token (prompt/completion) | ค่าใช้จ่าย |
| --- | --- | --- |
| `first_llm.py` ถาม "ตอบว่า ok คำเดียว" (claude-sonnet-4.6) | 21 / 4 | $0.000123 ≈ 0.004 บาท |
| `first_llm.py` ถาม "อธิบาย Agent Loop ใน 2 ประโยค" | ~80 / ~100 | ~$0.002 ≈ 0.07 บาท |
| `compare_models.py` (3 โมเดล) | รวม ~650 | ~$0.003-0.005 รวม ≈ 0.1-0.2 บาท |

ครั้งละไม่กี่สตางค์ — แต่ Lab ถัดๆ ไปที่ agent วน loop หลายรอบ (Lab 3+) หรือรันซ้ำหลายครั้ง (Lab 5) จะ
สะสมเร็วกว่านี้ **นิสัยที่ควรฝึกตั้งแต่ Lab นี้: ดูบรรทัด `[cost]` ทุกครั้ง**

> `USD_TO_THB = 36.0` ในโค้ดเป็นอัตราโดยประมาณเพื่อให้เห็นภาพเป็นบาท ปรับได้ตามอัตราจริง —
> ตัวเลขที่ OpenRouter หักคือ USD

---

## `llm` กับ `config` มาจากไหน?

หลายคนสงสัยว่า `llm.chat(...)` ที่เรียกใน Lab นี้ ตัว `llm` เป็น object ที่ได้มาอย่างไร
— คำตอบคือ **`llm` ไม่ใช่ instance ของคลาส แต่เป็น "module"** ที่ import มาจาก `labs/core/`

> ส่วนนี้ (ถึงหัวข้อ "ใต้ฝา") อธิบายกลไก Python — **ข้ามได้ถ้ายังไม่เขียนโค้ด** ไม่กระทบการรัน

บรรทัดต้นไฟล์ของ Lab 2 ทำสองอย่าง:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # (1) เพิ่ม root repo เข้า import path

from labs.core import config, llm   # (2) import โมดูลกลางที่ใช้ร่วมทุก Lab
```

- **(1)** `sys.path.insert(...)` ทำให้ Python มองเห็นแพ็กเกจ `labs.*` แม้รันสคริปต์ตรงๆ จาก root
  (เลยรันได้ทั้ง `python labs/lab2_llm/first_llm.py`)
- **(2)** `llm` คือไฟล์ `labs/core/llm.py` ทั้งไฟล์ — เรียก `llm.chat(...)` ก็คือเรียก **ฟังก์ชัน** `chat()` ในโมดูลนั้น
  ส่วน `config` คือ `labs/core/config.py` ที่โหลดค่าจาก `.env`

### ใต้ฝา: `llm.chat()` ทำงานอย่างไร

ไฟล์ `labs/core/llm.py` มีแค่ 2 ฟังก์ชันหลัก:

```python
from openai import OpenAI
from . import config

def build_client() -> OpenAI:
    return OpenAI(
        api_key=config.require_api_key(),       # อ่านคีย์จาก .env (ผ่าน config)
        base_url=config.OPENROUTER_BASE_URL,     # ชี้ base_url ไป OpenRouter — นี่คือหัวใจ "thin client"
    )

def chat(messages, model=None, tools=None, **kwargs):
    client = build_client()                      # สร้าง OpenAI client (ชี้ OpenRouter)
    params = {"model": model or config.OPENROUTER_MODEL, "messages": messages}
    if tools: params["tools"] = tools
    params.update(kwargs)                        # max_tokens, extra_body ฯลฯ ส่งผ่านตรงนี้
    return client.chat.completions.create(**params)
```

จุดที่ต้องเข้าใจ:
- `llm.chat()` ใช้ **OpenAI SDK ตัวจริง** แต่เปลี่ยน `base_url` เป็นของ OpenRouter — นี่คือนิยามของ
  "thin client" ตาม outline บท 1.2 (ไม่ต้องใช้ framework แยกของ OpenRouter)
- `api_key`, `base_url`, `model` เริ่มต้น ทั้งหมดมาจาก `config` ซึ่งอ่านมาจาก `.env` —
  จึง **เปลี่ยนโมเดล/คีย์/endpoint ได้จากจุดเดียว** โดยไม่แตะโค้ด Lab
- `**kwargs` คือช่องที่ทำให้ Lab ส่ง `max_tokens` และ `extra_body` (Lab 2) หรือ `tools` (Lab 3+) เข้าไปได้
  โดย `core/llm.py` ไม่ต้องรู้จักพารามิเตอร์เหล่านั้นล่วงหน้า — usage accounting ใน Lab นี้ก็ใช้ช่องนี้

> สรุป: `llm` = โมดูล `labs/core/llm.py`, `llm.chat()` = ฟังก์ชันที่ห่อ `OpenAI(...).chat.completions.create(...)`
> ไว้ชั้นเดียว ทุก Lab ตั้งแต่ Lab 2 เป็นต้นไปจึงเรียก LLM ด้วยรูปแบบเดียวกันหมด

---

## อธิบายจุดสำคัญของโค้ด

### `first_llm.py` — โครงสร้าง messages, token usage และค่าใช้จ่าย

#### ฟังก์ชัน `ask(question, max_tokens)`

```python
messages = [
    {"role": "system", "content": SYSTEM},   # system : กำหนดบทบาท/พฤติกรรม
    {"role": "user",   "content": question}, # user   : คำถามจากผู้ใช้
]
resp = llm.chat(messages=messages, max_tokens=max_tokens, **USAGE_ACCOUNTING)
```

- ตัวแปร `SYSTEM` คือ system prompt ที่กำหนดบทบาทของ LLM (สิ่งเดียวกับ Custom Instructions ในหน้าแชท)
- `resp.choices[0].message.content` คือคำตอบของโมเดล
- `resp.usage` มีฟิลด์ `prompt_tokens`, `completion_tokens`, `total_tokens` — ใช้ติดตามค่าใช้จ่ายและตรวจว่าใกล้ context limit หรือยัง
- `resp.usage.cost` คือ USD ที่ถูกหักจริง (มีเพราะเราส่ง `USAGE_ACCOUNTING` ไป)
- การตั้ง `max_tokens` ต่ำๆ เป็นวิธีฝึกดูผลของ output limit — และเป็นวิธีคุมค่าใช้จ่ายขาออกโดยตรง

### `compare_models.py` — เปรียบเทียบโมเดล

#### ฟังก์ชัน `run()`

ส่ง `QUESTION` เดียวกัน (`"อธิบายความต่างของ Chatbot กับ Agent ใน 2 ประโยค"`) ไปยังหลายโมเดลใน `MODELS` list โดยใช้ `llm.chat(model=model, ...)` แล้ววัด:
- `resp.usage.total_tokens` — จำนวน token ที่ใช้
- `time.time()` ก่อน/หลัง — เวลาตอบสนอง (วินาที)
- `resp.usage.cost` — ค่าใช้จ่ายของโมเดลนั้น และ `total_cost` สะสมของทั้งการเปรียบเทียบ

สรุปผลเป็นตาราง `model / total_tok / sec / cost_usd / note` เพื่อเปรียบเทียบได้ทันที — สังเกตว่าโมเดล
ที่ใช้ token พอๆ กันอาจมี cost ต่างกันหลายเท่า เพราะราคาต่อ token ต่างกัน

> จุดที่ควรเปิดอ่าน: parameter `model=model` ใน `llm.chat()` — แสดงว่า OpenRouter รองรับการเลือกโมเดล
> ต่อ request ได้ (ส่งชื่อโมเดลต่างกันในแต่ละครั้งที่เรียก) โดยใช้ base_url/คีย์เดิมจาก `config`

---

## ผลลัพธ์ที่คาดหวัง

### `first_llm.py`

```
============================================================
[user]   อธิบาย Agent Loop ใน 2 ประโยค
[assistant] Agent Loop คือ...
------------------------------------------------------------
[token] prompt=82 completion=97 total=179
[cost]  $0.001701 USD  (≈ 0.0612 บาท)  <- หักจากเครดิต OpenRouter จริง
[model] anthropic/claude-sonnet-4.6
```

### `compare_models.py`

```
============================================================================================
model                                total_tok    sec    cost_usd  note
--------------------------------------------------------------------------------------------
anthropic/claude-sonnet-4.6                236   5.80    0.003120  **Chatbot** คือระบบที่โต้ตอบกับ...
openai/gpt-oss-120b                        271   3.57    0.000098  Chatbot คือระบบสนทนาที่ออกแบบ...
meta-llama/llama-3.1-8b-instruct           229   7.22    0.000014  1.  **Chatbot** เป็นระบบคอมพิ...
--------------------------------------------------------------------------------------------
รวมทั้งการเปรียบเทียบ                                $0.003232 USD  (≈ 0.1164 บาท)
```

ตัวเลข token/เวลา/cost จะต่างกันทุกครั้ง — สิ่งที่ควรสังเกตคือ**สัดส่วน**: โมเดลใหญ่แพงกว่าโมเดลเล็ก
หลายสิบเท่าทั้งที่ token ใกล้กัน

> ถ้าโมเดลใดขึ้น `ERROR` ในตาราง มักเป็นเพราะโมเดลนั้นบน OpenRouter ไม่ว่างชั่วคราว ไม่ใช่คุณทำผิด ลองรันใหม่

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)
