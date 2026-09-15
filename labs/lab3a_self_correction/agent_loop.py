"""
Lab 3a — เติม self-correction ให้ Agent Loop ด้วย instruction ล้วนๆ (ไม่ใช้ hook)

ต่อยอดจาก labs/lab3_agent_loop/agent_loop.py (ไม่แก้ไฟล์นั้นเลยแม้แต่บรรทัดเดียว — คัดลอกมาที่นี่
แล้วแก้แค่ตัวแปร SYSTEM ตัวเดียว) เพื่อตอบโจทย์ที่ Lab 3 เดิมยังไม่มี:

  "ออกแบบ tool interface และ error surface ที่ทำให้โมเดลใช้งานถูกต้องและแก้ตัวเองได้"

ทดสอบจริงกับ Lab 3 เดิมแล้วพบว่า: error message จาก calculate() ชัดเจนพอให้โมเดล "เข้าใจ" error
ได้ถูกต้อง แต่โมเดล "ไม่ retry เอง" — มันเลือกโยนกลับไปถามผู้ใช้แทน (ดูรายละเอียดที่
labs/lab3_agent_loop/QUESTIONS.md) สาเหตุคือ SYSTEM ของ Lab 3 ไม่มีคำสั่งบอกให้ retry เลย

Lab 3a นี้แก้เฉพาะจุดนั้น — เพิ่มประโยคเดียวใน SYSTEM สั่งให้โมเดลลองแก้ไข argument เองก่อนถามผู้ใช้
เมื่อเจอ tool result ที่ขึ้นต้นด้วย "error:" — เป็นการแก้ปัญหาด้วยเครื่องมือระดับเดียวกับ Lab 3
(prompt engineering ล้วนๆ) ยังไม่ใช้ hook/middleware (นั่นเป็นเรื่องของ Lab 4)

รัน:  python labs/lab3a_self_correction/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import llm

# ---- (1) Local tools : ฟังก์ชันจริง + schema แบบ OpenAI function (เหมือน Lab 3 ทุกตัวอักษร) ----
def get_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    # ประเมินเฉพาะนิพจน์เลขคณิตอย่างปลอดภัย (ตัวอย่างการเรียนรู้)
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "error: อนุญาตเฉพาะตัวเลขและ + - * / ( )"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"error: {e}"


LOCAL_FUNCS = {"get_time": lambda **_: get_time(),
               "calculate": lambda expression, **_: calculate(expression)}

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

# ---- (2) จุดที่ต่างจาก Lab 3: เพิ่มคำสั่งเดียวให้ SYSTEM สั่ง self-correction ----
SYSTEM = (
    "คุณเป็นผู้ช่วยที่ใช้ tool ได้ ถ้าจำเป็นให้เรียก tool ก่อนตอบ ตอบเป็นภาษาไทย "
    "หากผลลัพธ์จาก tool ขึ้นต้นด้วย 'error:' ให้อ่านข้อความ error แล้วพยายามแก้ไข argument "
    "ตามคำแนะนำนั้น แล้วเรียก tool ใหม่ทันที โดยไม่ต้องถามผู้ใช้ก่อน เว้นแต่ลองแก้แล้วยังไม่สำเร็จ"
)


def dispatch(name: str, args: dict) -> str:
    fn = LOCAL_FUNCS.get(name)
    return fn(**args) if fn else f"error: ไม่พบ tool {name}"


# ---- (3) Agent loop : เหมือน Lab 3 ทุกบรรทัด ไม่มีการเปลี่ยน logic การวน loop เลย ----
def run_agent(question: str, max_steps: int = 6):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for step in range(1, max_steps + 1):
        resp = llm.chat(messages=messages, tools=TOOLS)
        msg = resp.choices[0].message

        if msg.tool_calls:
            print(f"[step {step}] THINK -> ขอเรียก {len(msg.tool_calls)} tool")
            # ต้อง append assistant message ที่มี tool_calls ก่อน
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
                print(f"           TOOL_USE {call.function.name}({args}) -> {result}")
                messages.append({
                    "role": "tool", "tool_call_id": call.id,
                    "content": result,   # OBSERVE: ป้อนผล tool กลับเข้า context
                })
            continue   # วนกลับให้ LLM อ่านผล tool

        # ไม่มี tool_calls = end_turn
        print(f"[step {step}] END_TURN")
        print("-" * 60)
        print(f"[answer] {msg.content}")
        return msg.content

    print("[!] ถึงขีดจำกัดจำนวนรอบแล้ว")
    return None


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
    print(f"[user] {q}")
    run_agent(q)
