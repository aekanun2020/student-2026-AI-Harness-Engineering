"""
Lab 6b — probe_sandbox.py: พิสูจน์ด้วยตาว่า "ห้อง" แบบ container กั้นอะไรได้บ้าง (เทียบกับ probe ของ Lab 6)

รัน:  python labs/lab6b_sandbox_container/probe_sandbox.py
ไม่เรียก LLM — เปิด container ตัวเดียวกับที่ agent ใช้ แล้วส่งโค้ดตรวจสอบเข้าไปทาง tool run_python
"""
import os, sys, asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import config                      # noqa: F401 — โหลด .env เข้า os.environ ฝั่ง host เหมือนตอนรัน agent จริง
from labs.lab6b_sandbox_container.agent_loop import SERVER, dispatch
from mcp import ClientSession
from mcp.client.stdio import stdio_client

PROBES = [
    ("1) env / user / cwd ที่เห็นในห้อง", "run_python", {"code": """
import os, json
print(json.dumps({"api_key_visible": "OPENROUTER_API_KEY" in os.environ, "env_var_count": len(os.environ),
                  "uid": os.getuid(), "cwd": os.getcwd()}))
"""}),
    ("2) อ่านไฟล์: ใน /work ได้ไหม / นอก /work (โฟลเดอร์บ้านของ host) มีไหม", "run_python", {"code": """
import os, json
print(json.dumps({"work_files": sorted(os.listdir("/work")), "host_home_visible": os.path.exists("/Users") or os.path.exists("/home/" + (os.environ.get("USER") or "x")),
                  "root_dirs": sorted(os.listdir("/"))[:8]}))
"""}),
    ("3) เขียนไฟล์: /work (ro mount), /app (read-only fs), /tmp (tmpfs)", "run_python", {"code": """
import json
out = {}
for p in ("/work/escape.txt", "/app/escape.txt", "/tmp/ok.txt"):
    try:
        open(p, "w").write("x"); out[p] = "WRITTEN"
    except Exception as e:
        out[p] = type(e).__name__
print(json.dumps(out))
"""}),
    ("4) network: ต่อออก 1.1.1.1:53 ได้ไหม", "run_python", {"code": """
import socket, json
try:
    socket.create_connection(("1.1.1.1", 53), timeout=2); print(json.dumps({"network": "CONNECTED"}))
except Exception as e:
    print(json.dumps({"network": "blocked", "error": type(e).__name__ + ": " + str(e)[:60]}))
"""}),
    ("5) CPU bomb ผ่าน calculate (RLIMIT_CPU ใน Linux container)", "calculate", {"expression": "9999**99999999"}),
    ("6) server ในห้องยังรับงานต่อได้ไหม หลังข้อ 5", "calculate", {"expression": "15*4"}),
]


async def main():
    print(f"[host] OPENROUTER_API_KEY ใน os.environ ของ host: {'มี' if os.environ.get('OPENROUTER_API_KEY') else 'ไม่มี'}")
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for title, tool, args in PROBES:
                print(f"\n== {title}")
                print("   " + (await dispatch(session, tool, args)).replace("\n", "\n   "))
    print("\nอ่านผล: 1) api_key_visible false, uid ไม่ใช่ 0 (ไม่ใช่ root) · 2) host_home_visible false = อ่านไฟล์นอกห้องไม่ได้แล้ว"
          " (ต่างจาก Lab 6) · 3) เขียนได้แค่ /tmp · 4) network blocked = ปิดช่องที่ Lab 6 ปิดไม่ได้ · 5) exit code ติดลบ/timeout · 6) ยังได้ 60")


if __name__ == "__main__":
    asyncio.run(main())
