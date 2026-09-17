"""
Lab 2 (ต่อ) — เปรียบเทียบหลายโมเดลบน OpenRouter
อ้างอิง outline: บทที่ 1.2 / แบบฝึกหัดที่ 2 (ข้อ 3)

ดัดแปลงจาก labs/lab2_llm/compare_models.py ของ repo ต้นทาง — เพิ่มคอลัมน์ "ค่าใช้จ่ายจริง" ต่อโมเดล
และยอดรวมของทั้งการเปรียบเทียบ โค้ดส่วนอื่นเหมือนต้นฉบับ

ส่งคำถามเดียวกันไปหลายโมเดล แล้วบันทึก คำตอบ + token + เวลา + ค่าใช้จ่าย ลงตาราง
เพื่อฝึกเลือกโมเดลให้เหมาะกับงาน/งบประมาณ

รัน:  python labs/lab2_llm/compare_models.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import llm

# ปรับรายชื่อโมเดลได้ตามที่อยากเทียบ (ชื่อโมเดลตามรูปแบบ OpenRouter)
MODELS = [
    "anthropic/claude-sonnet-4.6",
    "openai/gpt-oss-120b",
    "meta-llama/llama-3.1-8b-instruct",
]

QUESTION = "อธิบายความต่างของ Chatbot กับ Agent ใน 2 ประโยค"

USD_TO_THB = 36.0   # อัตราโดยประมาณ ปรับได้ตามจริง
USAGE_ACCOUNTING = {"extra_body": {"usage": {"include": True}}}


def run():
    rows = []
    total_cost = 0.0
    for model in MODELS:
        print(f"\n>>> {model}")
        t0 = time.time()
        try:
            resp = llm.chat(
                messages=[{"role": "user", "content": QUESTION}],
                model=model,
                max_tokens=200,
                **USAGE_ACCOUNTING,
            )
            dt = time.time() - t0
            ans = resp.choices[0].message.content.strip().replace("\n", " ")
            tot = resp.usage.total_tokens
            cost = getattr(resp.usage, "cost", None)
            if cost is not None:
                total_cost += cost
            print(ans)
            rows.append((model, tot, round(dt, 2), cost, ans[:40] + "..."))
        except Exception as e:
            rows.append((model, "-", "-", None, f"ERROR: {e}"))

    # สรุปเป็นตาราง
    print("\n" + "=" * 92)
    print(f"{'model':<36}{'total_tok':>10}{'sec':>7}{'cost_usd':>12}  note")
    print("-" * 92)
    for m, tok, sec, cost, note in rows:
        cost_s = f"{cost:.6f}" if cost is not None else "-"
        print(f"{m:<36}{str(tok):>10}{str(sec):>7}{cost_s:>12}  {note}")
    print("-" * 92)
    print(f"{'รวมทั้งการเปรียบเทียบ':<53}${total_cost:.6f} USD  (≈ {total_cost * USD_TO_THB:.4f} บาท)")


if __name__ == "__main__":
    run()
