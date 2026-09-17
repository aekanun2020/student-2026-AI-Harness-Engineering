"""
Lab 3 (เสริม) — เปิดดูข้างใน `resp` และ `msg` ของบรรทัดที่ 69 ใน agent_loop.py

    msg = resp.choices[0].message

ตอบ 2 คำถาม:
  (1) นอกจาก resp.choices แล้ว หลังจุด resp. มีอะไรให้เรียกได้อีก
  (2) msg บรรจุอะไรบ้าง — และต่างกันอย่างไรระหว่างรอบที่ AI "ขอเรียก tool" กับรอบที่ AI "ตอบเป็นข้อความ"

ไม่แก้ agent_loop.py — คัดลอกส่วน TOOLS/SYSTEM มาเหมือนเดิมแล้วเรียก LLM 2 ครั้งเพื่อเทียบกัน
รัน:  python labs/lab3_agent_loop/inspect_response.py
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import llm

# ---- เหมือน Lab 3 ทุกตัวอักษร: schema ของ tool ที่ส่งให้ LLM ----
TOOLS = [
    {"type": "function", "function": {
        "name": "get_time", "description": "คืนวันเวลาปัจจุบัน",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "calculate", "description": "คำนวณนิพจน์เลขคณิต เช่น 15*4",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "นิพจน์ เช่น (15+5)*2"}},
            "required": ["expression"]},
    }},
]
SYSTEM = "คุณเป็นผู้ช่วยที่ใช้ tool ได้ ถ้าจำเป็นให้เรียก tool ก่อนตอบ ตอบเป็นภาษาไทย"


def show(title: str, obj) -> None:
    """พิมพ์ object แบบอ่านง่าย: ชนิด + ทุก field ที่มีจริง (ผ่าน .model_dump() ของ pydantic)"""
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    print(f"ชนิด (type): {type(obj).__module__}.{type(obj).__name__}")
    data = obj.model_dump()
    print("field ทั้งหมดที่มีจริง:", list(data.keys()))
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def inspect_one(question: str) -> None:
    print(f"\n\n{'#' * 70}\n# คำถาม: {question}\n{'#' * 70}")
    resp = llm.chat(messages=[{"role": "system", "content": SYSTEM},
                              {"role": "user", "content": question}], tools=TOOLS)

    # ---------- (1) resp. มีอะไรได้อีก ----------
    show("(1) resp — ผลลัพธ์ทั้งก้อนที่ API ส่งกลับมา", resp)
    print("\nที่ใช้บ่อย:")
    print(f"  resp.id                     = {resp.id}")
    print(f"  resp.model                  = {resp.model}   <- โมเดลที่ตอบจริง (OpenRouter อาจสลับ)")
    print(f"  resp.created                = {resp.created} "
          f"({datetime.datetime.fromtimestamp(resp.created):%Y-%m-%d %H:%M:%S})")
    print(f"  resp.usage.prompt_tokens    = {resp.usage.prompt_tokens}   <- ที่ Lab 2 ใช้พิมพ์ [token]")
    print(f"  resp.usage.completion_tokens= {resp.usage.completion_tokens}")
    print(f"  resp.usage.total_tokens     = {resp.usage.total_tokens}")
    print(f"  len(resp.choices)           = {len(resp.choices)}   <- ปกติ 1 (ขอหลายคำตอบได้ด้วย n=)")
    print(f"  resp.choices[0].index       = {resp.choices[0].index}")
    print(f"  resp.choices[0].finish_reason = {resp.choices[0].finish_reason!r}   "
          f"<- 'tool_calls' = ขอเรียก tool, 'stop' = ตอบจบแล้ว")
    print(f"  resp.choices[0].message     = <msg ด้านล่าง>")

    # ---------- (2) msg บรรจุอะไร ----------
    msg = resp.choices[0].message
    show("(2) msg = resp.choices[0].message — สิ่งที่ AI 'พูด' ในรอบนี้", msg)
    print("\nอ่านค่า:")
    print(f"  msg.role       = {msg.role!r}   <- เป็น 'assistant' เสมอ")
    print(f"  msg.content    = {msg.content!r}")
    if msg.tool_calls:
        print(f"  msg.tool_calls = list ยาว {len(msg.tool_calls)} -> AI ขอให้เราเรียก tool แทนที่จะตอบ")
        for i, tc in enumerate(msg.tool_calls):
            print(f"    [{i}] tc.id                 = {tc.id}   <- ต้องส่งคืนใน tool_call_id ตอนป้อนผลกลับ")
            print(f"        tc.type               = {tc.type}")
            print(f"        tc.function.name      = {tc.function.name}")
            print(f"        tc.function.arguments = {tc.function.arguments!r}   "
                  f"<- เป็น 'ข้อความ' JSON ไม่ใช่ dict จึงต้อง json.loads() ก่อน (agent_loop.py บรรทัด 79)")
            print(f"        json.loads(...)       = {json.loads(tc.function.arguments or '{}')}")
    else:
        print(f"  msg.tool_calls = {msg.tool_calls}   <- ไม่ขอ tool = รอบนี้คือคำตอบสุดท้าย (END_TURN)")


if __name__ == "__main__":
    inspect_one("ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร")   # รอบที่ AI ขอเรียก tool
    inspect_one("ตอบว่า สวัสดี คำเดียว")                 # รอบที่ AI ตอบเป็นข้อความ

    print(f"""

{'=' * 70}
สรุป
{'=' * 70}
(1) resp คือ "ซอง" ทั้งใบที่ API ส่งกลับ — นอกจาก resp.choices ยังมี
    resp.id / resp.model / resp.created / resp.object / resp.usage (นับ token)
    ใน resp.choices[0] ก็มี .index / .finish_reason / .message
    OpenRouter แถม field ที่ OpenAI ไม่มีมาด้วย: resp.provider, choices[0].native_finish_reason,
    msg.reasoning และ resp.usage.cost (เงินที่หักจริง — Lab 2 ใช้ตัวนี้พิมพ์ [cost])
(2) msg คือข้อความ 1 ก้อนจาก AI มี field หลัก 3 ตัวที่ Lab 3 ใช้:
    .role = 'assistant' เสมอ
    .content = ข้อความตอบ — ตอนขอเรียก tool อาจเป็น None/ว่าง หรือมีข้อความสั้นๆ ประกอบก็ได้
               (agent_loop.py บรรทัด 75 จึงเขียน msg.content or "" กันค่า None)
    .tool_calls = รายการ tool ที่ AI ขอให้เรารัน (เป็น None ตอนตอบเป็นข้อความ)
    -> agent_loop.py บรรทัด 71 ดูแค่ว่า msg.tool_calls มีไหม: มี = TOOL_USE, ไม่มี = END_TURN
       (ไม่ได้ดู content เลย — ตัวชี้ขาดคือ tool_calls ไม่ใช่ content)
""")
