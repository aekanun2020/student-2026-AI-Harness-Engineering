"""
Lab 6 — probe_sandbox.py: พิสูจน์ด้วยตาว่า "ห้อง" ที่ sandboxed_calculate() ใช้ กั้นอะไรได้บ้าง และอะไรยังไม่กั้น

รัน:  python labs/lab6_sandbox/probe_sandbox.py
ไม่เรียก LLM ไม่ใช้ API key — แค่ส่งสคริปต์ตรวจสอบ 3 ชิ้นเข้าไปรันใน process ลูกผ่าน _run_in_sandbox()
ตัวเดียวกับที่ calculate ใช้ แล้วดูว่าข้างในมองเห็นอะไร
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from labs.core import config          # noqa: F401 — โหลด .env เข้า os.environ เหมือนตอนรัน agent จริง
from labs.lab6_sandbox.agent_loop import _run_in_sandbox, SANDBOX_ENV

REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 1) ข้างในเห็น environment / cwd อะไร  (ไม่มี resource limit ในสคริปต์นี้ — ดูแค่ขอบเขต env/cwd)
PROBE_ENV = """
import os, sys, json
print(json.dumps({
    "api_key_visible": "OPENROUTER_API_KEY" in os.environ,
    "env_var_count": len(os.environ),
    "cwd": os.getcwd(),
    "cwd_is_empty": os.listdir(os.getcwd()) == [],
    "sys_path_has_cwd": "" in sys.path or os.getcwd() in sys.path,
}))
"""

# 2) อ่านไฟล์นอกห้องได้ไหม (คาดว่า "ได้" — subprocess ไม่กัน filesystem read)
PROBE_READ = """
import sys, json
try:
    open(sys.argv[1], encoding="utf-8").read(1)
    print(json.dumps({"can_read_outside": True}))
except Exception as e:
    print(json.dumps({"can_read_outside": False, "error": str(e)}))
"""

# 3) เขียนไฟล์ได้ไหม (คาดว่า "ไม่ได้" บน macOS/Linux — RLIMIT_FSIZE=0 ทำให้เขียนไบต์แรกก็ได้ OSError: File too large)
PROBE_WRITE = """
import json
try:
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
except ImportError:
    pass
with open("escape.txt", "w") as f:
    f.write("x")
print(json.dumps({"can_write_file": True}))
"""


def show(title, proc):
    print(f"\n== {title}")
    if proc is None:
        print("   (timeout)")
        return
    print(f"   exit code = {proc.returncode}")
    if proc.stdout.strip():
        print(f"   stdout    = {proc.stdout.strip()}")
    if proc.stderr.strip():
        print(f"   stderr    = {proc.stderr.strip().splitlines()[-1]}")


if __name__ == "__main__":
    print(f"[แม่] OPENROUTER_API_KEY ใน os.environ ของ process แม่: {'มี' if os.environ.get('OPENROUTER_API_KEY') else 'ไม่มี'}")
    print(f"[แม่] env ที่จะส่งให้ลูก (SANDBOX_ENV) มีคีย์: {sorted(SANDBOX_ENV)}")
    show("1) env / cwd ที่ process ลูกมองเห็น", _run_in_sandbox(PROBE_ENV, ""))
    show("2) อ่านไฟล์นอกห้อง (README.md ของ repo)", _run_in_sandbox(PROBE_READ, os.path.join(REPO_ROOT, "README.md")))
    show("3) เขียนไฟล์ในห้อง (RLIMIT_FSIZE=0)", _run_in_sandbox(PROBE_WRITE, ""))
    print("\nอ่านผล: 1) api_key_visible ต้องเป็น false, cwd_is_empty true · 2) can_read_outside ยังเป็น true = ช่องว่างที่เหลือ"
          " · 3) บน macOS/Linux ต้องไม่เห็น can_write_file แต่เห็น OSError: File too large — Windows จะเขียนได้ (ไม่มี resource)")
