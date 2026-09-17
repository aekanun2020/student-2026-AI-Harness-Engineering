"""
Lab 6b — MCP server ที่รันอยู่ "ในห้อง" (Docker container): tool ด้าน filesystem + runtime

ไฟล์นี้ไม่ได้รันบนเครื่องคุณโดยตรง — Dockerfile คัดลอกมันเข้า image แล้ว agent_loop.py (บน host)
สั่ง `docker run -i --network none ...` เปิด container แล้วคุยกับ server นี้ผ่าน MCP ทาง stdin/stdout

หลักคิด (ดู README): container คือ "ผนัง" (OS บังคับ: ไม่มี network, filesystem read-only, ไม่มี credential)
ส่วน MCP server คือ "ประตู" — ประตูยังต้องมี guardrail ของตัวเอง (read_file ห้ามออกนอก /work, timeout, จำกัด output)
เพราะตามที่ OpenAI ระบุ tool จาก MCP "are responsible for enforcing their own guardrails"

ห้าม print() ลง stdout ในไฟล์นี้ — stdout คือช่องทางโปรโตคอล MCP (stdio transport) ใช้ stderr แทนถ้าจะ debug
"""
import os, sys, subprocess, tempfile

from mcp.server.fastmcp import FastMCP

WORK_DIR = os.path.realpath(os.environ.get("SANDBOX_WORK_DIR", "/work"))   # workspace ที่ host mount มาให้แบบ read-only
MAX_READ_CHARS = 40_000
RUN_TIMEOUT_SEC = 5          # เพดานเวลาของโค้ดที่ tool รันให้ (ฝั่ง server ในห้อง)
RUN_CPU_SEC = 2              # RLIMIT_CPU ของ process ลูกในห้อง — Linux ใน container ตั้งได้จริงทั้ง CPU และ memory
RUN_MEMORY_MB = 128          # RLIMIT_AS (ต่างจาก Lab 6 บน macOS ที่ตั้ง RLIMIT_AS ไม่ได้)
MAX_OUTPUT_CHARS = 4_000

mcp = FastMCP("lab6b-sandbox", log_level="WARNING")   # เงียบ log "Processing request..." ให้ผู้เรียนเห็นแต่ผลจริง


def _set_limits():
    """เรียกใน process ลูกก่อนรันโค้ด (preexec_fn) — ชั้นป้องกันซ้ำในห้อง นอกเหนือจาก --memory/--pids-limit ของ docker"""
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (RUN_CPU_SEC, RUN_CPU_SEC + 1))   # soft < hard → ได้ SIGXCPU (exit -24) เหมือน Lab 6
    resource.setrlimit(resource.RLIMIT_AS, (RUN_MEMORY_MB * 1024 * 1024,) * 2)


def _run_limited(code: str, arg: str = "") -> str:
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", code, arg],
            capture_output=True, text=True, timeout=RUN_TIMEOUT_SEC,
            cwd=tempfile.gettempdir(), preexec_fn=_set_limits,
        )
    except subprocess.TimeoutExpired:
        return f"error: timeout — รันนานเกิน {RUN_TIMEOUT_SEC} วินาที (server ในห้องยังรับงานต่อได้)"
    out = proc.stdout.strip()
    if proc.stderr.strip():
        out = (out + "\n[stderr] " + proc.stderr.strip().splitlines()[-1]).strip()
    if len(out) > MAX_OUTPUT_CHARS:
        out = out[:MAX_OUTPUT_CHARS] + "\n...[ตัดที่ 4000 ตัวอักษร]"
    if proc.returncode != 0:
        return f"error: process ถูกยุติ (exit code {proc.returncode}, เกิน CPU/memory limit หรือโค้ดพัง)\n{out}".strip()
    return out or "(ไม่มี output)"


_CALC_CODE = """
import sys
expression = sys.argv[1]
if not set(expression) <= set("0123456789+-*/(). "):
    print("error: อนุญาตเฉพาะตัวเลขและ + - * / ( )")
else:
    try:
        print(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        print(f"error: {e}")
"""


@mcp.tool()
def calculate(expression: str) -> str:
    """คำนวณนิพจน์เลขคณิต เช่น 15*4 (รันใน process ลูกในห้อง มี CPU/memory limit)"""
    return _run_limited(_CALC_CODE, expression)


@mcp.tool()
def read_file(path: str) -> str:
    """อ่านไฟล์ข้อความใน workspace (/work) เท่านั้น — path เป็น relative จาก workspace เช่น hello.txt"""
    full = os.path.realpath(os.path.join(WORK_DIR, path))
    if full != WORK_DIR and not full.startswith(WORK_DIR + os.sep):
        return "error: อ่านได้เฉพาะไฟล์ใน workspace (/work) เท่านั้น (ห้ามใช้ .. หรือ path เต็ม)"
    rel = os.path.relpath(full, WORK_DIR)
    if any(part.startswith(".") for part in rel.split(os.sep)):
        return "error: ไม่อนุญาตให้อ่านไฟล์หรือโฟลเดอร์ที่ขึ้นต้นด้วยจุด"
    if not os.path.isfile(full):
        return f"error: ไม่พบไฟล์ {path} ใน workspace"
    try:
        with open(full, encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        return "error: อ่านได้เฉพาะไฟล์ข้อความ (UTF-8)"
    if len(text) > MAX_READ_CHARS:
        text = text[:MAX_READ_CHARS] + f"\n...[ตัดที่ {MAX_READ_CHARS} ตัวอักษร]"
    return text


@mcp.tool()
def run_python(code: str) -> str:
    """รันโค้ด Python สั้น ๆ แล้วคืน stdout — รันในห้อง: ไม่มี network, เขียนได้เฉพาะ /tmp, ไม่มี credential ใด ๆ"""
    return _run_limited(code)


if __name__ == "__main__":
    mcp.run(transport="stdio")
