"""
Lab 6 — เติม Sandbox ให้ Agent Loop (Layer 6: Sandbox + Execution)

ต่อยอดจาก labs/lab3_agent_loop/agent_loop.py (ไม่แก้ไฟล์นั้นเลย — คัดลอกโครงมาที่นี่) เพื่อปิดช่องว่าง
Layer 6 ที่ root README ของ repo ระบุไว้ว่ายังไม่มี Lab ไหนทำจริง

รีเสิร์ชจาก:
  1) Anthropic — Computer Use Tool: Docker container, minimal privilege, resource limit,
     validate ก่อน execute, หยุดทันทีเมื่อเจอ error ตัวแรก
     https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool
  2) Anthropic — Code execution with MCP: sandbox โค้ดที่โมเดลสร้าง ลด token/ป้องกันข้อมูลหลุด
     https://www.anthropic.com/engineering/code-execution-with-mcp

SANDBOX — sandboxed_calculate()
  Lab 3 เดิมรัน eval() ตรงใน process หลักของ agent loop เลย ไม่มีขอบเขตป้องกันอะไรเลย — ถ้า
  expression ทำให้ CPU/memory พุ่ง (เช่น เลขยกกำลังมหาศาล) จะฉุด agent loop หลักไปด้วย
  ที่นี่ห่อ eval() ด้วย subprocess แยก process จริง + จำกัด CPU time ด้วย resource.setrlimit
  (แนวคิดเดียวกับ "minimal privilege + resource limit" ของ Computer Use Tool) ถ้า subprocess
  ถูกฆ่าเพราะเกิน limit หรือ timeout, agent loop หลักไม่กระทบเลย ได้ error กลับมาแทน

  ขอบเขตที่กั้นให้ process ลูก (หลัก isolation: เข้าถึงได้เฉพาะที่อนุญาต)
    - env      : ส่งเข้าไปแค่ PATH — ไม่มี OPENROUTER_API_KEY หรือความลับอื่นจาก .env (credential อยู่นอก sandbox)
    - cwd      : โฟลเดอร์ว่างชั่วคราว ไม่ใช่โฟลเดอร์ repo
    - เขียนไฟล์ : RLIMIT_FSIZE = 0 → เขียนไฟล์ไม่ได้เลยในระดับ OS (macOS/Linux) ได้ OSError: File too large
    - CPU      : RLIMIT_CPU + timeout ของ subprocess.run() ฝั่งแม่
    - python -I: isolated mode ไม่อ่านตัวแปร PYTHON* และไม่เอา cwd เข้า sys.path

  หมายเหตุขอบเขต: ยัง "อ่าน" ไฟล์ทั่วเครื่องได้ และยัง "ต่อ network" ได้ — สองอย่างนี้ subprocess + resource
  ทำไม่ได้ ต้องใช้ container/VM (ดู README สำหรับตารางเทียบ framework จริง)
  บน Windows โมดูล resource ไม่มี จึงเหลือแค่ env/cwd + timeout (ยังกัน process หลักได้ แต่ช้ากว่า)

รัน:  python labs/lab6_sandbox/agent_loop.py "<คำถาม>"
"""
import sys, os, json, datetime, subprocess, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import llm

# ---- Local tools เดิมจาก Lab 3 (get_time ไม่เปลี่ยน, calculate ถูกแทนที่ด้วย sandboxed_calculate) ----
def get_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---- SANDBOX: รัน eval() ใน subprocess แยก + จำกัด CPU/memory ----
SANDBOX_CPU_SEC = 2          # จำกัดเวลา CPU ของ subprocess (วินาที)
SANDBOX_MEMORY_MB = 64       # จำกัด memory ของ subprocess (MB) — ใช้ได้เฉพาะแพลตฟอร์มที่รองรับ RLIMIT_AS
SANDBOX_TIMEOUT_SEC = 4      # เพดานเวลารอผลจริง (กันเผื่อ subprocess ค้างไม่ยอมตาย)
SANDBOX_ENV = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT") if k in os.environ}
# ↑ environment ที่ส่งให้ process ลูก มีแค่นี้ — ไม่ส่ง os.environ ทั้งก้อน เพราะ core/config.py โหลด .env
#   (OPENROUTER_API_KEY) เข้า os.environ ไว้แล้ว ถ้าส่งต่อ ความลับจะไปอยู่ "ในห้อง" ที่เราเรียกว่า sandbox

_WORKER_CODE = """
import sys, json
cpu_sec = {cpu_sec}
mem_bytes = {mem_bytes}
try:
    import resource   # มีเฉพาะ Unix (macOS/Linux) — Windows ไม่มีโมดูลนี้
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))   # ห้ามเขียนไฟล์: เขียนไบต์แรกก็ได้ OSError: File too large
    try:
        # RLIMIT_AS ไม่รองรับบน macOS (Darwin kernel ปฏิเสธเสมอ) แต่รองรับบน Linux —
        # ใส่ไว้เมื่อแพลตฟอร์มรองรับ ถ้าไม่รองรับก็ข้ามไป
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except (ValueError, OSError):
        pass
except ImportError:
    # Windows: ไม่มี resource limit ระดับ OS ให้ใช้ — เหลือ timeout ของ subprocess.run() ฝั่ง parent
    # เป็นตาข่ายเดียว (ยังฆ่า process ลูกที่ค้างได้ แค่ช้ากว่า RLIMIT_CPU และไม่จำกัด memory)
    pass

expression = sys.argv[1]
allowed = set("0123456789+-*/(). ")
if not set(expression) <= allowed:
    print(json.dumps({{"ok": False, "error": "อนุญาตเฉพาะตัวเลขและ + - * / ( )"}}))
else:
    try:
        result = eval(expression, {{"__builtins__": {{}}}}, {{}})
        print(json.dumps({{"ok": True, "result": str(result)}}))
    except Exception as e:
        print(json.dumps({{"ok": False, "error": str(e)}}))
"""


def _run_in_sandbox(code: str, arg: str):
    """รันสคริปต์ python ใน process ลูกที่ถูกกั้นขอบเขต: env มีแค่ PATH, cwd = โฟลเดอร์ว่างชั่วคราว, python -I
    คืน CompletedProcess หรือ None ถ้าเกิน timeout (probe_sandbox.py ใช้ helper ตัวนี้พิสูจน์ขอบเขตจริง)"""
    with tempfile.TemporaryDirectory() as empty_dir:
        try:
            return subprocess.run(
                [sys.executable, "-I", "-c", code, arg],
                capture_output=True, text=True, timeout=SANDBOX_TIMEOUT_SEC,
                cwd=empty_dir, env=SANDBOX_ENV,
            )
        except subprocess.TimeoutExpired:
            return None


def sandboxed_calculate(expression: str) -> str:
    code = _WORKER_CODE.format(cpu_sec=SANDBOX_CPU_SEC, mem_bytes=SANDBOX_MEMORY_MB * 1024 * 1024)
    proc = _run_in_sandbox(code, expression)
    if proc is None:
        return f"error: sandbox timeout — คำนวณนานเกิน {SANDBOX_TIMEOUT_SEC} วินาที (agent loop หลักไม่กระทบ)"

    if proc.returncode != 0:
        # ถูกฆ่าโดย RLIMIT (เช่น เกิน CPU time) หรือ subprocess ล่มด้วยเหตุอื่น
        return f"error: sandbox process ถูกยุติ (exit code {proc.returncode}, เกิน CPU/memory limit ที่ตั้งไว้)"

    try:
        payload = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return "error: sandbox คืนผลลัพธ์ที่อ่านไม่ได้"

    return payload["result"] if payload["ok"] else f"error: {payload['error']}"


LOCAL_FUNCS = {"get_time": lambda **_: get_time(),
               "calculate": lambda expression, **_: sandboxed_calculate(expression)}

TOOLS = [
    {"type": "function", "function": {
        "name": "get_time", "description": "คืนวันเวลาปัจจุบัน",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "calculate", "description": "คำนวณนิพจน์เลขคณิต เช่น 15*4 (รันใน sandbox แยก process)",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "นิพจน์ เช่น (15+5)*2"}},
            "required": ["expression"]},
    }},
]

SYSTEM = "คุณเป็นผู้ช่วยที่ใช้ tool ได้ ถ้าจำเป็นให้เรียก tool ก่อนตอบ ตอบเป็นภาษาไทย"


def dispatch(name: str, args: dict) -> str:
    fn = LOCAL_FUNCS.get(name)
    return fn(**args) if fn else f"error: ไม่พบ tool {name}"


# ---- Agent loop : เหมือน Lab 3 ทุกบรรทัด (ไม่มี checkpoint — ดู Lab 5 สำหรับ checkpoint) ----
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
