# Q&A Log — Entry 0001

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

เพิ่มจาก whitelist ที่ calculate() ใน Lab 3 มีอยู่แล้ว

ผมหา whitelist ไม่เจอ

## คำตอบ (verbatim)

whitelist อยู่ที่ [labs/lab3_agent_loop/agent_loop.py:28](../labs/lab3_agent_loop/agent_loop.py:28) ครับ ไม่ได้เขียนคำว่า "whitelist" ตรงๆ ในโค้ด แต่นี่คือกลไก whitelist:

```python
26: def calculate(expression: str) -> str:
27:     # ประเมินเฉพาะนิพจน์เลขคณิตอย่างปลอดภัย (ตัวอย่างการเรียนรู้)
28:     allowed = set("0123456789+-*/(). ")
29:     if not set(expression) <= allowed:
30:         return "error: อนุญาตเฉพาะตัวเลขและ + - * / ( )"
```

**อธิบาย:** `allowed` (บรรทัด 28) คือ**เซตของอักขระที่อนุญาต** — ตัวเลข 0-9, เครื่องหมาย `+ - * / ( ) .` และ space เท่านั้น บรรทัด 29 เช็คว่าอักขระทุกตัวใน `expression` ที่ผู้ใช้ส่งมาต้องเป็นสับเซตของ `allowed` (`set(expression) <= allowed`) ถ้ามีอักขระอื่นปน (เช่นตัวอักษร, `;`, `_`) จะถูกปฏิเสธทันทีที่บรรทัด 30 ก่อนจะเข้าไปถึง `eval()` เลย

นี่คือรูปแบบ **whitelist-based input validation** (อนุญาตเฉพาะสิ่งที่ระบุไว้ ปฏิเสธทุกอย่างที่เหลือ) ต่างจาก blacklist ที่จะพยายามดักอักขระอันตรายทีละตัว — ที่ README/QUESTIONS.md ของ Lab 4 พูดถึงคำว่า "whitelist" ก็หมายถึงกลไกนี้เอง ไม่ได้มีตัวแปรหรือฟังก์ชันชื่อ `whitelist` ตรงๆ ในโค้ด
