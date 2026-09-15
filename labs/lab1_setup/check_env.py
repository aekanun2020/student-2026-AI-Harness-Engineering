"""
Lab 1 — ติดตั้งและตรวจสอบสภาพแวดล้อมการพัฒนา

ดัดแปลงจาก labs/lab1_setup/check_env.py ของ
https://github.com/aekanun2020/Python-Agent-LangGraph — ต้นฉบับตรวจ 2 อย่าง (LLM + MCP MSSQL
Server) แต่ repo นี้ไม่มี MCP server ให้ต่อเลย จึงตัด check_mcp() ออก เหลือแค่การตรวจ precondition
ที่ repo นี้ใช้จริง:

  เรียก LLM ผ่าน OpenRouter ได้จริง (thin client: OpenAI SDK + base_url)

รัน:  python labs/lab1_setup/check_env.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import config, llm


def check_llm() -> bool:
    print("ตรวจ OpenRouter (LLM) ...")
    try:
        resp = llm.chat(
            messages=[{"role": "user", "content": "ตอบสั้น ๆ คำเดียวว่า 'พร้อม'"}],
            max_tokens=20,
        )
        answer = resp.choices[0].message.content
        print(f"      โมเดล {config.OPENROUTER_MODEL} ตอบ: {answer!r}")
        return True
    except Exception as e:
        print(f"      ❌ เรียก LLM ไม่สำเร็จ: {e}")
        return False


def main():
    print("=" * 60)
    print("Lab 1 — ตรวจสอบสภาพแวดล้อมการพัฒนา")
    print("=" * 60)
    ok_llm = check_llm()
    print("-" * 60)
    if ok_llm:
        print("✅ environment พร้อม — ไปต่อ Lab 2 ได้เลย")
        return 0
    print("⚠️  ยังไม่พร้อม — แก้ตามข้อความ ❌ ด้านบนก่อน")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
