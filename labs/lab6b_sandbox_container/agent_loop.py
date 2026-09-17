"""
Lab 6b — Agent loop บน host + tool ทั้งหมดอยู่ใน Docker container (Layer 6: Sandbox + Execution แบบเต็ม)

ต่อยอดจาก Lab 6: Lab 6 กั้นได้แค่ process/CPU/ความลับ/การเขียนไฟล์ แต่ยัง "อ่านไฟล์นอกห้อง" และ "ต่อ network" ได้
Lab 6b ปิดสองช่องนั้นด้วย container:
  docker run -i --rm --network none --read-only --cap-drop ALL -v <workspace>:/work:ro lab6b-sandbox

  - --network none   : ไม่มี network interface เลย → network isolation ระดับ OS
  - -v ...:/work:ro   : host แบ่งให้เห็นแค่ workspace เดียว แบบอ่านอย่างเดียว → filesystem isolation
  - --read-only       : filesystem ของ container เองก็เขียนไม่ได้ (ยกเว้น /tmp ที่เป็น tmpfs)
  - ไม่มี .env ใน image : credential ไม่เคยเข้าไปในห้อง (agent ฝั่ง host เท่านั้นที่ถือ API key)

agent loop (Lab 3 เดิม) ไม่ต้องรู้ว่า tool อยู่ที่ไหน — มันคุยกับ tool ผ่าน MCP (stdio) แล้ว docker เป็นคนสร้างผนังให้
MCP = ประตู (interface) · container = ผนัง (isolation) — สองอย่างนี้คนละหน้าที่ (ดู README)

รัน:  docker build -t lab6b-sandbox labs/lab6b_sandbox_container
      python labs/lab6b_sandbox_container/agent_loop.py "<คำถาม>"
"""
import sys, os, json, asyncio
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from labs.core import llm

IMAGE = os.environ.get("SANDBOX_IMAGE", "lab6b-sandbox")
WORKSPACE = os.path.realpath(os.environ.get(
    "SANDBOX_WORKSPACE", os.path.join(os.path.dirname(__file__), "workspace")))
TOOL_TIMEOUT = timedelta(seconds=20)   # เพดานรอผลจาก container ฝั่ง host (server ในห้องมี timeout ของตัวเองที่ 5 วิ)

# ---- "ผนัง": ทุก flag ตรงนี้คือขอบเขตที่ OS/docker บังคับ ไม่ใช่คำขอร้องในคำสั่งถึงโมเดล ----
DOCKER_ARGS = [
    "run", "-i", "--rm",
    "--network", "none",                     # network isolation
    "--read-only", "--tmpfs", "/tmp:rw,size=32m",
    "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
    "--memory", "256m", "--pids-limit", "64", "--cpus", "1",
    "-v", f"{WORKSPACE}:/work:ro",           # filesystem isolation: เห็นแค่ workspace แบบอ่านอย่างเดียว
    IMAGE,
]
SERVER = StdioServerParameters(command="docker", args=DOCKER_ARGS)

SYSTEM = ("คุณเป็นผู้ช่วยที่ใช้ tool ได้ ถ้าจำเป็นให้เรียก tool ก่อนตอบ ตอบเป็นภาษาไทย "
          "tool ทั้งหมดรันอยู่ใน sandbox ที่ไม่มี network และเห็นไฟล์เฉพาะใน workspace")


def to_openai_tools(mcp_tools) -> list:
    """แปลง tool ที่ MCP server ประกาศ → รูปแบบ OpenAI function-calling ที่ llm.chat() ใช้ (Lab 3 เขียน TOOLS นี้เองกับมือ)"""
    return [{"type": "function", "function": {
        "name": t.name, "description": t.description or "", "parameters": t.inputSchema,
    }} for t in mcp_tools]


async def dispatch(session: ClientSession, name: str, args: dict) -> str:
    """Lab 3: dispatch() เรียก python function ในโปรแกรมเดียวกัน — ที่นี่ส่งคำขอข้ามผนังไปให้ server ในห้องทำแทน"""
    try:
        res = await session.call_tool(name, args, read_timeout_seconds=TOOL_TIMEOUT)
    except Exception as e:                     # container ตาย/หมดเวลา → agent loop หลักไม่กระทบ
        return f"error: sandbox ไม่ตอบ ({type(e).__name__}: {e})"
    text = "\n".join(c.text for c in res.content if getattr(c, "text", None)) or "(ไม่มี output)"
    return f"error: {text}" if res.isError and not text.startswith("error") else text


async def run_agent(question: str, max_steps: int = 6):
    async with stdio_client(SERVER) as (read, write):          # = docker run ... (เปิดห้อง)
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_openai_tools((await session.list_tools()).tools)
            print(f"[sandbox] container พร้อม — tools ที่ประกาศจากในห้อง: {[t['function']['name'] for t in tools]}")

            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ]
            for step in range(1, max_steps + 1):
                resp = llm.chat(messages=messages, tools=tools)
                msg = resp.choices[0].message

                if msg.tool_calls:
                    print(f"[step {step}] THINK -> ขอเรียก {len(msg.tool_calls)} tool")
                    messages.append({
                        "role": "assistant", "content": msg.content or "",
                        "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                    })
                    for call in msg.tool_calls:
                        args = json.loads(call.function.arguments or "{}")
                        result = await dispatch(session, call.function.name, args)
                        shown = result if len(result) <= 200 else result[:200] + f"...[{len(result)} chars]"
                        print(f"           TOOL_USE {call.function.name}({args}) -> {shown}")
                        messages.append({
                            "role": "tool", "tool_call_id": call.id,
                            "content": result,   # OBSERVE: ป้อนผล tool กลับเข้า context
                        })
                    continue   # วนกลับให้ LLM อ่านผล tool

                print(f"[step {step}] END_TURN")
                print("-" * 60)
                print(f"[answer] {msg.content}")
                return msg.content

            print("[!] ถึงขีดจำกัดจำนวนรอบแล้ว")
            return None
    # ออกจาก with = container ถูกปิดและลบทิ้ง (--rm) — ห้องหายไปพร้อมงาน


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "อ่านไฟล์ hello.txt แล้วบอกว่า repo นี้มีกี่ Lab แล้ว 15*4 เท่ากับเท่าไร"
    print(f"[user] {q}")
    asyncio.run(run_agent(q))
