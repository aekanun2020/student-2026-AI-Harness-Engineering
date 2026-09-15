"""
Lab 5 — Memory (Tool-result clearing + Compaction) + Checkpoint สำหรับ Agent ที่รันยาวข้ามหลายรอบ

`ConversationMemory` (history/context()/maybe_compact()) ดัดแปลงจาก
labs/lab7_memory/agent_memory.py ของ https://github.com/aekanun2020/Python-Agent-LangGraph
  - ตัด notes ออก (ต้นฉบับมี fact list ที่ฝังใน system prompt ตายตัว agent ไม่ได้จดเอง — ไม่มีอะไรให้สังเกต)
  - maybe_compact(): เดิมตัด "4 ข้อความล่าสุด" ตายตัว ซึ่งอาจตัดกลางคู่ tool_calls/tool แล้ว API ปฏิเสธ
    -> ปรับให้ถอยไปตัดที่ต้น turn (ข้อความ role=user) เสมอ
  - เพิ่ม clear_old_tool_results(): "tool-result clearing" — ล้างเนื้อหา tool result ก้อนใหญ่ของ turn
    ที่จบไปแล้วออกจาก history (เหลือ placeholder) โดยไม่ต้องเรียก LLM — ถูกกว่า compaction

จุดที่ต้องปรับจากต้นฉบับ (เพราะรันแบบ standalone ในนี้ ไม่มี MCP MSSQL Server จริงให้ต่อ):
  - ต้นฉบับใช้ ToolRegistry ต่อ MCP server จริงผ่าน config.MCP_SERVER_URL (ไม่มีใน repo นี้)
    -> สลับไปใช้ local tools ของ Lab 3 (get_time/calculate) แทน
  - SYSTEM ต้นฉบับเป็น DB-analyst persona ที่อ้างอิง MCP tools ของฐานข้อมูลตรงๆ
    -> ปรับให้เข้ากับ local tools แต่คงประโยค "จำบริบทการสนทนาก่อนหน้าได้" ซึ่งเป็นหัวใจของบทเรียนไว้

เพิ่ม tool read_file (อ่านไฟล์ข้อความในโฟลเดอร์ repo) เพื่อให้มี tool result ก้อนใหญ่จริงๆ ให้ล้าง
(get_time/calculate คืนแค่ไม่กี่ตัวอักษร ไม่มีอะไรให้ล้าง)

ส่วนที่เพิ่มใหม่ (ไม่มีใน labs/lab7_memory/ ต้นฉบับ): CHECKPOINT — บันทึก mem.history
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


# ---- Tool ใหม่ของ Lab 5: read_file — คืนของก้อนใหญ่ (ทั้งไฟล์) จึงเป็นตัวอย่างที่เห็นผลของ tool-result clearing ----
REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAX_READ_CHARS = 40_000


def read_file(path: str) -> str:
    """อ่านไฟล์ข้อความ — จำกัดให้อยู่ในโฟลเดอร์ repo เท่านั้น และห้ามไฟล์/โฟลเดอร์ที่ขึ้นต้นด้วยจุด (เช่น .env)
    เพราะ tool ที่อ่านไฟล์ได้คือช่องทางรั่วของความลับถ้าไม่กำหนดขอบเขต (Layer 8 Safety)"""
    full = os.path.realpath(os.path.join(REPO_ROOT, path))
    if not full.startswith(REPO_ROOT + os.sep):
        return "error: อ่านได้เฉพาะไฟล์ในโฟลเดอร์ repo เท่านั้น (ห้ามใช้ .. หรือ path เต็ม)"
    rel = os.path.relpath(full, REPO_ROOT)
    if any(part.startswith(".") for part in rel.split(os.sep)):
        return "error: ไม่อนุญาตให้อ่านไฟล์หรือโฟลเดอร์ที่ขึ้นต้นด้วยจุด (เช่น .env, .git)"
    if not os.path.isfile(full):
        return f"error: ไม่พบไฟล์ {path}"
    try:
        with open(full, encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        return "error: อ่านได้เฉพาะไฟล์ข้อความ (UTF-8)"
    if len(text) > MAX_READ_CHARS:
        text = text[:MAX_READ_CHARS] + f"\n...[ตัดที่ {MAX_READ_CHARS} ตัวอักษร]"
    return text


LOCAL_FUNCS = {"get_time": lambda **_: get_time(),
               "calculate": lambda expression, **_: calculate(expression),
               "read_file": lambda path, **_: read_file(path)}

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
    {"type": "function", "function": {
        "name": "read_file",
        "description": "อ่านไฟล์ข้อความในโฟลเดอร์ repo (path สัมพัทธ์จาก root ของ repo เช่น README.md) คืนเนื้อหาทั้งไฟล์",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "path สัมพัทธ์ เช่น labs/lab5_memory_checkpoint/README.md"}},
            "required": ["path"]},
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
# tool result ที่ยาวเกินนี้ (ตัวอักษร) และอยู่ใน turn ที่จบไปแล้ว จะถูกล้างเหลือ placeholder
# (ของสั้นๆ อย่างผลของ calculate ไม่คุ้มล้าง เพราะ placeholder ยาวพอๆ กัน)
CLEAR_TOOL_RESULT_OVER_CHARS = 500
CLEARED_PLACEHOLDER = "[ผลลัพธ์ tool ถูกล้างออกจาก history แล้ว (เดิม {n} ตัวอักษร) — ถ้าต้องใช้ให้เรียก tool ใหม่]"


# ==== ConversationMemory — ดัดแปลงจาก labs/lab7_memory/agent_memory.py (ดู docstring ด้านบนว่าต่างตรงไหน) ====
class ConversationMemory:
    """หน่วยความจำการสนทนาแบบ in-memory + compaction."""
    def __init__(self):
        self.history: list[dict] = []     # messages ข้ามรอบ

    def add(self, message: dict):
        self.history.append(message)

    def context(self) -> list[dict]:
        """ประกอบ context: system + history (ไว้ส่งเข้า LLM ทุกครั้ง)."""
        return [{"role": "system", "content": SYSTEM}] + self.history

    def _turn_start(self, at: int) -> int | None:
        """หา index ของข้อความ role=user ที่เป็นต้น turn ซึ่งครอบตำแหน่ง `at` (ถอยหลังจาก at)
        ใช้กันไม่ให้ตัด history กลางคู่ tool_calls/tool — API จะปฏิเสธถ้า tool message ไม่มี tool_calls นำหน้า"""
        for i in range(min(at, len(self.history) - 1), -1, -1):
            if self.history[i].get("role") == "user":
                return i
        return None

    def clear_old_tool_results(self):
        """Tool-result clearing: tool result ก้อนใหญ่ของ turn ที่จบไปแล้ว ถูกแทนด้วย placeholder
        (assistant สรุปสิ่งที่ได้จาก tool ไว้ในคำตอบของ turn นั้นแล้ว จึงไม่จำเป็นต้องแบกของดิบต่อ)
        ต่างจาก compaction ตรงที่ไม่เรียก LLM เลย — ฟรี และไม่แตะข้อความอื่น"""
        cut = self._turn_start(len(self.history) - 1)   # ต้น turn ปัจจุบัน — ของ turn นี้ยังไม่ล้าง
        if not cut:
            return
        cleared = saved = 0
        for m in self.history[:cut]:
            content = m.get("content") or ""
            if m.get("role") == "tool" and len(content) > CLEAR_TOOL_RESULT_OVER_CHARS:
                m["content"] = CLEARED_PLACEHOLDER.format(n=len(content))
                cleared += 1
                saved += len(content)
        if cleared:
            print(f"[clear] ล้าง tool result เก่า {cleared} รายการ (ประหยัด {saved:,} ตัวอักษรใน history)")

    def maybe_compact(self):
        """ถ้า history ยาวเกินเกณฑ์ ให้ LLM สรุปของเก่าเป็นย่อหน้าเดียว (รักษา token budget)."""
        if len(self.history) < COMPACT_AFTER_MESSAGES:
            return
        # เก็บ 4 ข้อความล่าสุดไว้ดิบ ๆ (ปัดไปที่ต้น turn เพื่อไม่ตัดกลางคู่ tool_calls/tool), ที่เหลือเอาไปสรุป
        cut = self._turn_start(len(self.history) - 4)
        if not cut:
            return
        keep = self.history[cut:]
        old = self.history[:cut]
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
        json.dump({"history": mem.history, "pending": pending},
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
        usage = getattr(resp, "usage", None)
        if usage:   # ดูว่า history ที่ส่งไปใหญ่แค่ไหน — ตัวชี้วัดหลักว่า clearing/compaction ช่วยจริง
            print(f"[token] prompt={usage.prompt_tokens} completion={usage.completion_tokens}")
        msg = resp.choices[0].message
        if msg.tool_calls:
            print(f"[step {step}] THINK -> ขอเรียก {len(msg.tool_calls)} tool")
            mem.add({"role": "assistant", "content": msg.content or "",
                     "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
                shown = result if len(result) <= 80 else f"{result[:80]}... ({len(result):,} ตัวอักษร)"
                print(f"           TOOL_USE {call.function.name}({args}) -> {shown}")
                mem.add({"role": "tool", "tool_call_id": call.id, "content": result})
            save_checkpoint(thread_id, mem, pending=True)   # CHECKPOINT: อาจถูกฆ่ากลาง turn ได้
            continue
        mem.add({"role": "assistant", "content": msg.content})
        print(f"[answer] {msg.content}")
        mem.clear_old_tool_results()   # ขั้นเบา: ล้างของดิบก้อนใหญ่ของ turn ก่อนๆ (ไม่เรียก LLM)
        mem.maybe_compact()            # ขั้นหนัก: ถ้ายังยาวเกิน ค่อยให้ LLM สรุป
        save_checkpoint(thread_id, mem, pending=False)      # CHECKPOINT: turn จบสมบูรณ์แล้ว
        return msg.content

    save_checkpoint(thread_id, mem, pending=True)
    print("[!] ถึงขีดจำกัดจำนวนรอบแล้ว (checkpoint ไว้แล้ว รันซ้ำด้วย thread_id เดิมเพื่อวิ่งต่อได้)")
    return None


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง"
    thread_id = sys.argv[2] if len(sys.argv) > 2 else "default"

    mem = ConversationMemory()
    checkpoint = load_checkpoint(thread_id)
    if checkpoint:
        mem.history = checkpoint["history"]
        print(f"[resume] โหลด memory ของ thread '{thread_id}' -> history {len(mem.history)} ข้อความ")
        if checkpoint.get("pending"):
            print("[resume] turn ก่อนหน้าค้างกลางทาง (ถูกขัดจังหวะ) -> วิ่งต่อโดยไม่เพิ่มคำถามใหม่")
            turn(None, mem, thread_id, resume=True)
            return

    turn(question, mem, thread_id)


if __name__ == "__main__":
    main()
