# Q&A Log — Entry 0011

**วันที่:** 2026-09-17
**Project:** student-2026-AI-Harness-Engineering

---

## คำถาม (verbatim)

lab 6 กับ 6a ต่างกันอย่างไร ยกประเด็นด้าน Isolation และ Compartment มาพูดก่อน

## คำตอบ (verbatim)

ก่อนอื่น ใน repo ไม่มี Lab 6a ครับ — มี **Lab 6** กับ **Lab 6b** เข้าใจว่าคุณหมายถึง 6b

**Isolation (กั้นไม่ให้เข้าถึงสิ่งที่ไม่อนุญาต)** — ต่างกันที่ "ผนังหนาแค่ไหน"

| ด้าน | Lab 6 (subprocess + rlimit) | Lab 6b (Docker container) |
|---|---|---|
| ความลับ (env) | ส่ง env แค่ `PATH` ไม่ให้เห็น API key | เหมือนกัน และ image ไม่มี `.env` อยู่ในตัวตั้งแต่แรก |
| อ่านไฟล์ | **กั้นไม่ได้** อ่านทั้งเครื่องได้ (`can_read_outside: true`) | เห็นเฉพาะ `/work` ที่ mount มาแบบอ่านอย่างเดียว (`host_home_visible: false`) |
| เขียนไฟล์ | `RLIMIT_FSIZE = 0` เขียนไม่ได้เลย | `--read-only` ทั้ง filesystem เขียนได้แค่ `/tmp` ที่เป็น tmpfs |
| network | **ไม่ได้กั้นเลย** | `--network none` ไม่มี interface ให้ต่อออก |
| สิทธิ์ | เป็น user เดียวกับคุณ | uid 10001 ไม่ใช่ root, `--cap-drop ALL`, `no-new-privileges` |
| ทรัพยากร | `RLIMIT_CPU` + timeout (Mac ตั้ง memory ไม่ได้, Windows ตั้งอะไรไม่ได้เลย) | `--memory 256m --pids-limit 64 --cpus 1` บังคับได้จริงทุก host ที่มี Docker |

จุดสำคัญ: Lab 6 พึ่งกลไกของ **OS ที่แตกต่างกันในแต่ละแพลตฟอร์ม** จึงกั้นได้ไม่ครบและไม่เท่ากัน ส่วน Lab 6b ย้ายผนังไปอยู่ที่ **container runtime** ซึ่งให้ผลเหมือนกันทุกเครื่องที่รัน Docker ได้ และปิดสองช่องที่ Lab 6 ปิดไม่ได้เลยคือ **การอ่านไฟล์นอกขอบเขต** กับ **network**

**Compartment (แบ่งส่วนว่าอะไรอยู่ข้างใน อะไรอยู่ข้างนอก)** — ต่างกันที่ "ขีดเส้นแบ่งตรงไหน"

- **Lab 6 แบ่งที่ระดับคำสั่งเดียว** — `get_time` กับตัวจัดการ tool ทั้งหมดยังอยู่ใน process ของ agent มีแค่ `eval()` ของ `calculate` ที่ถูกโยนออกไปรันในลูก พูดอีกแบบคือ **โยนงานอันตรายออกไป แต่ตัวห้องไม่มีอยู่จริง** ห้องเกิดชั่วคราวแล้วดับทันทีที่คำนวณเสร็จ
- **Lab 6b แบ่งที่ระดับความสามารถทั้งชุด** — tool ทั้งสามตัว (`calculate`, `read_file`, `run_python`) **อยู่ในห้องทั้งหมด** เป็น MCP server ที่มีชีวิตอยู่ตลอด session ฝั่ง agent บน host ไม่มีโค้ด tool เหลืออยู่เลย มันถามห้องว่า "มีอะไรให้ใช้บ้าง" (`list_tools`) แล้วแปลงเป็น schema ส่งให้ LLM

ผลของการขีดเส้นต่างกันนี้:
- Lab 6 ยัง**ต้องเขียน `TOOLS` schema เองด้วยมือ**ฝั่ง host เพราะ host เป็นเจ้าของ tool
- Lab 6b host ไม่รู้จัก tool ล่วงหน้าเลย เพิ่ม tool ใหม่ในห้องได้โดยไม่ต้องแตะโค้ด agent — และถ้าจะให้มี tool อันตรายอย่าง `run_python` (รันโค้ดที่โมเดลเขียนเอง) ก็ทำได้อย่างสบายใจ เพราะมันเกิดในห้องที่ไม่มีทั้งเน็ต ไฟล์นอกขอบเขต และ credential

**สองคำนี้ทำงานคนละหน้าที่และต้องมีคู่กัน:** MCP คือ **ประตู** (สัญญาว่าจะคุยกันยังไง) ส่วน container คือ **ผนัง** (บังคับว่าเข้าถึงอะไรได้บ้าง) — Lab 6b มีทั้งสองอย่าง จึงมี guardrail 2 ชั้น: โค้ดใน `mcp_server.py` ปฏิเสธ path ที่มี `..` ตั้งแต่ที่ประตู และต่อให้เขียนโค้ดเลี่ยงประตูได้ ผนังก็ยังไม่ให้เห็นอะไรนอก `/work` อยู่ดี ส่วน Lab 6 มีแค่ whitelist อักขระใน `calculate()` เป็นด่านเดียว

---

## หลักฐานในโค้ด (อ้างอิงตอนตอบ)

| ข้อความในคำตอบ | ที่มาในโค้ด |
| --- | --- |
| Lab 6 ส่ง env แค่ `PATH` | `labs/lab6_sandbox/agent_loop.py:49` `SANDBOX_ENV = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT") if k in os.environ}` |
| Lab 6 ห้ามเขียนไฟล์ / จำกัด CPU | `labs/lab6_sandbox/agent_loop.py:59-60` `setrlimit(RLIMIT_CPU, ...)`, `setrlimit(RLIMIT_FSIZE, (0, 0))` |
| Lab 6 cwd ว่าง + `python -I` | `labs/lab6_sandbox/agent_loop.py:88-93` `TemporaryDirectory()`, `[sys.executable, "-I", "-c", code, arg]` |
| Lab 6 tool อยู่ฝั่ง host | `labs/lab6_sandbox/agent_loop.py:117` `LOCAL_FUNCS = {"get_time": ..., ...}` และ `TOOLS` เขียนมือที่บรรทัด 120 |
| Lab 6b flags ของผนัง | `labs/lab6b_sandbox_container/agent_loop.py:35-41` `--network none`, `--read-only`, `--tmpfs /tmp`, `--cap-drop ALL`, `no-new-privileges`, `--memory 256m --pids-limit 64 --cpus 1`, `-v <workspace>:/work:ro` |
| Lab 6b tool อยู่ในห้อง | `labs/lab6b_sandbox_container/mcp_server.py:67,73,94` `calculate` / `read_file` / `run_python` |
| Lab 6b host ถามห้องว่ามี tool อะไร | `labs/lab6b_sandbox_container/agent_loop.py:71` `(await session.list_tools()).tools` แล้วแปลงด้วย `to_openai_tools()` บรรทัด 50 |
| Lab 6b ไม่ใช่ root | `labs/lab6b_sandbox_container/Dockerfile` `useradd --uid 10001 sandbox` + `USER sandbox` |

ค่า `host_home_visible: false` ของ Lab 6b มาจากการรัน `probe_sandbox.py` ก่อน merge — ผลเต็มอยู่ใน
[0010](0010-merge-decision-and-lab6b-verification.md) · ส่วนค่าของ Lab 6 ตอนตอบคำถามอ้างจากเอกสารของ Lab 6
แล้ว**รันยืนยันซ้ำตอนบันทึก qa นี้** ผลตรงกับคำตอบทุกแถว:

```
$ python labs/lab6_sandbox/probe_sandbox.py
[แม่] OPENROUTER_API_KEY ใน os.environ ของ process แม่: มี
[แม่] env ที่จะส่งให้ลูก (SANDBOX_ENV) มีคีย์: ['PATH']

== 1) env / cwd ที่ process ลูกมองเห็น
   exit code = 0
   stdout    = {"api_key_visible": false, "env_var_count": 2, "cwd": "/private/var/folders/.../T/tmp4wapqs2y", "cwd_is_empty": true, "sys_path_has_cwd": false}

== 2) อ่านไฟล์นอกห้อง (README.md ของ repo)
   exit code = 0
   stdout    = {"can_read_outside": true}

== 3) เขียนไฟล์ในห้อง (RLIMIT_FSIZE=0)
   exit code = 1
   stderr    = OSError: [Errno 27] File too large
```
