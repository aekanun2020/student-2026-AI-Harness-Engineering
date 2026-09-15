"""
Lab 5 — Memory (Compaction + Notes) + Checkpoint สำหรับ Agent ที่รันยาวข้ามหลายรอบ

`ConversationMemory` (history/notes/context()/maybe_compact()) คัดลอกมาจาก
labs/lab7_memory/agent_memory.py ของ https://github.com/aekanun2020/Python-Agent-LangGraph
โดยคงไว้ใกล้เคียงต้นฉบับที่สุด — logic การจำ/การสรุปไม่เปลี่ยนแม้แต่บรรทัดเดียว

จุดที่ต้องปรับจากต้นฉบับ (เพราะรันแบบ standalone ในนี้ ไม่มี MCP MSSQL Server จริงให้ต่อ):
  - ต้นฉบับใช้ ToolRegistry ต่อ MCP server จริงผ่าน config.MCP_SERVER_URL (ไม่มีใน repo นี้)
    -> สลับไปใช้ local tools ของ Lab 3 (get_time/calculate) แทน
  - SYSTEM ต้นฉบับเป็น DB-analyst persona ที่อ้างอิง MCP tools ของฐานข้อมูลตรงๆ
    -> ปรับให้เข้ากับ local tools แต่คงประโยค "จำบริบทการสนทนาก่อนหน้าได้" ซึ่งเป็นหัวใจของบทเรียนไว้

ส่วนที่เพิ่มใหม่ (ไม่มีใน labs/lab7_memory/ ต้นฉบับ): CHECKPOINT — บันทึก mem.history/mem.notes
ลงไฟล์ JSON คีย์ด้วย thread_id ทุกครั้งที่จบ step/turn เพื่อให้ "external memory" ของ Lab 7 เดิม
(ซึ่งจริงๆ แล้วเป็นแค่ RAM ของ process เดียว หายหมดถ้า process ตาย) กลาย เป็น external จริง —
รอดได้แม้ process ถูกฆ่ากลางทาง และรอดข้าม "context reset" ทุกครั้งที่ script รันจบไปแล้วเปิดใหม่

รัน:  python labs/lab5_memory_checkpoint/agent_loop.py "<คำถาม>" [thread_id]
      รัน CLI ซ้ำหลายครั้งด้วย thread_id เดิม = เหมือนคุยต่อในบทสนทนาเดิม แม้ process ก่อนหน้าจะปิดไปแล้ว
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import llm

# ---- Local tools เดิมจาก Lab 3 (ไม่ sandbox — ดู Lab 6 สำหรับ sandbox) ----
def get_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
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


def dispatch(name: str, args: dict) -> str:
    fn = LOCAL_FUNCS.get(name)
    return fn(**args) if fn else f"error: ไม่พบ tool {name}"


SYSTEM = (
    "คุณเป็นผู้ช่วยที่ใช้ tool ได้และจำบริบทการสนทนาก่อนหน้าได้ ถ้าจำเป็นให้เรียก tool ก่อนตอบ "
    "ตอบเป็นภาษาไทย"
)

# เกณฑ์ compaction (ตั้งต่ำเพื่อให้เห็นผลในแล็บ เหมือนต้นฉบับ — ปรับได้)
COMPACT_AFTER_MESSAGES = 12


# ==== ConversationMemory — คัดลอกจาก labs/lab7_memory/agent_memory.py แทบทั้งหมด ====
class ConversationMemory:
    """หน่วยความจำการสนทนาแบบ in-memory + compaction + notes."""
    def __init__(self):
        self.history: list[dict] = []     # messages ข้ามรอบ
        self.notes: list[str] = []         # fact สำคัญที่คงอยู่แม้ compaction

    def add(self, message: dict):
        self.history.append(message)

    def add_note(self, fact: str):
        self.notes.append(fact)

    def context(self) -> list[dict]:
        """ประกอบ context: system + notes + history (ไว้ส่งเข้า LLM ทุกครั้ง)."""
        sys_msg = {"role": "system", "content": SYSTEM}
        if self.notes:
            sys_msg["content"] += "\n\n[บันทึกที่ต้องจำ]\n- " + "\n- ".join(self.notes)
        return [sys_msg] + self.history

    def maybe_compact(self):
        """ถ้า history ยาวเกินเกณฑ์ ให้ LLM สรุปของเก่าเป็นย่อหน้าเดียว (รักษา token budget)."""
        if len(self.history) < COMPACT_AFTER_MESSAGES:
            return
        # เก็บ 4 ข้อความล่าสุดไว้ดิบ ๆ, ที่เหลือเอาไปสรุป
        keep = self.history[-4:]
        old = self.history[:-4]
        transcript = "\n".join(
            f"{m['role']}: {m.get('content','')}" for m in old if m.get("content"))
        summary = llm.chat(messages=[
            {"role": "system", "content": "สรุปบทสนทนาต่อไปนี้เป็นย่อหน้าเดียว เก็บข้อเท็จจริงสำคัญไว้"},
            {"role": "user", "content": transcript},
        ], max_tokens=300).choices[0].message.content
        self.history = [{"role": "assistant", "content": f"[สรุปบทสนทนาก่อนหน้า] {summary}"}] + keep
        print(f"[compaction] ย่อ {len(old)} ข้อความเป็นสรุป 1 ก้อน (เหลือ {len(self.history)} ข้อความ)")


# ==== CHECKPOINT — ใหม่ ไม่มีในต้นฉบับ Lab 7 ====
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "checkpoints")


def _checkpoint_path(thread_id: str) -> str:
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    return os.path.join(CHECKPOINT_DIR, f"{thread_id}.json")


def save_checkpoint(thread_id: str, mem: ConversationMemory, pending: bool) -> None:
    """pending=True แปลว่า turn ยังทำไม่จบ (มี tool_calls ค้างอยู่) — ใช้บอกตอน resume ว่า
    ต้องวิ่งต่อจากตรงนี้เลยไหม หรือพร้อมรับคำถามใหม่ได้แล้ว"""
    with open(_checkpoint_path(thread_id), "w", encoding="utf-8") as f:
        json.dump({"history": mem.history, "notes": mem.notes, "pending": pending},
                   f, ensure_ascii=False, indent=2)


def load_checkpoint(thread_id: str):
    path = _checkpoint_path(thread_id)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ==== turn() — ปรับจาก Lab 7 ต้นฉบับ: ตัด ToolRegistry ออก ใช้ local tools + เพิ่ม checkpoint ====
def turn(question: str, mem: ConversationMemory, thread_id: str, max_steps: int = 8,
         resume: bool = False):
    if not resume:
        print(f"\n[user] {question}")
        mem.add({"role": "user", "content": question})

    for step in range(1, max_steps + 1):
        resp = llm.chat(messages=mem.context(), tools=TOOLS)
        msg = resp.choices[0].message
        if msg.tool_calls:
            print(f"[step {step}] THINK -> ขอเรียก {len(msg.tool_calls)} tool")
            mem.add({"role": "assistant", "content": msg.content or "",
                     "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
                print(f"           TOOL_USE {call.function.name}({args}) -> {result}")
                mem.add({"role": "tool", "tool_call_id": call.id, "content": result})
            save_checkpoint(thread_id, mem, pending=True)   # CHECKPOINT: อาจถูกฆ่ากลาง turn ได้
            continue
        mem.add({"role": "assistant", "content": msg.content})
        print(f"[answer] {msg.content}")
        mem.maybe_compact()
        save_checkpoint(thread_id, mem, pending=False)      # CHECKPOINT: turn จบสมบูรณ์แล้ว
        return msg.content

    save_checkpoint(thread_id, mem, pending=True)
    print("[!] ถึงขีดจำกัดจำนวนรอบแล้ว (checkpoint ไว้แล้ว รันซ้ำด้วย thread_id เดิมเพื่อวิ่งต่อได้)")
    return None


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง"
    thread_id = sys.argv[2] if len(sys.argv) > 2 else "default"

    checkpoint = load_checkpoint(thread_id)
    if checkpoint:
        mem = ConversationMemory()
        mem.history = checkpoint["history"]
        mem.notes = checkpoint["notes"]
        print(f"[resume] โหลด memory ของ thread '{thread_id}' -> "
              f"history {len(mem.history)} ข้อความ, notes {len(mem.notes)} รายการ")
        if checkpoint.get("pending"):
            print("[resume] turn ก่อนหน้าค้างกลางทาง (ถูกขัดจังหวะ) -> วิ่งต่อโดยไม่เพิ่มคำถามใหม่")
            turn(None, mem, thread_id, resume=True)
            return
    else:
        mem = ConversationMemory()
        mem.add_note("ผู้ใช้ชื่อผู้เรียนในหลักสูตร Agentic AI Development with Python")  # ตัวอย่าง note

    turn(question, mem, thread_id)


if __name__ == "__main__":
    main()
