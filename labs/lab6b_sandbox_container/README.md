# Lab 6b — Sandbox แบบเต็ม: MCP server (filesystem + runtime) รันใน Docker container

> ต่อยอดจาก **[Lab 6 — Sandbox](../lab6_sandbox/README.md)** โดยไม่แก้ไฟล์ Lab 6 —
> Lab 6 กั้นได้แค่ process / CPU / ความลับ / การเขียนไฟล์ แต่ **ยังอ่านไฟล์นอกห้องได้และยังต่อ network ได้**
> (รัน `probe_sandbox.py` ของ Lab 6 จะเห็น `can_read_outside: true`) Lab นี้ปิดสองช่องนั้นด้วย container
> ตามหลักที่ Anthropic ระบุว่า sandbox ที่ได้ผลต้องมี **ทั้ง filesystem และ network isolation**

---

## จุดประสงค์การเรียนรู้

- แยกให้ออกว่า **MCP = ประตู** (ช่องทางที่ agent คุยกับ tool) กับ **container = ผนัง** (สิ่งที่ OS บังคับว่า tool
  เข้าถึงอะไรได้) เป็นคนละหน้าที่ — ย้าย tool ไปเป็น MCP server ไม่ได้ทำให้มันถูก sandbox โดยอัตโนมัติ
- เห็น isolation ครบ 2 ด้านจริง: `--network none` (network) + mount เฉพาะ workspace แบบ read-only (filesystem)
  + ไม่มี credential ใด ๆ ใน image
- เห็นว่า agent loop ของ Lab 3 **ไม่ต้องเปลี่ยนโครง** เมื่อ tool ย้ายไปอยู่ในห้อง — เปลี่ยนแค่ `TOOLS` มาจาก
  `list_tools()` และ `dispatch()` กลายเป็น `call_tool()` ข้ามผนัง

**ในภาษาคน:** Lab 6 คือให้ผู้ช่วยทำงานในห้องที่ "เขียนอะไรไม่ได้ ไม่มีกุญแจ" แต่ประตูยังเปิด เดินออกไปอ่านเอกสาร
ข้างนอกหรือโทรออกได้ · Lab 6b คือห้องที่ผนังทึบ ไม่มีสายโทรศัพท์ มีแค่ช่องส่งเอกสาร (MCP) ที่เราเป็นคนส่งเข้าไป
และรับผลออกมา — ห้องหายไปทันทีที่งานเสร็จ (`--rm`)

---

## รีเสิร์ช: อ้างอิงจากเอกสารจริง

| แหล่งอ้างอิง | แนวคิดที่ยืมมา |
| --- | --- |
| Anthropic — [Beyond permission prompts: making Claude Code more secure and autonomous](https://www.anthropic.com/engineering/claude-code-sandboxing) (20 ต.ค. 2025) | "effective sandboxing requires both filesystem and network isolation" · ขาด network isolation = ขโมย SSH key ส่งออกได้ · ขาด filesystem isolation = หลุดออกจาก sandbox ไปต่อ network ได้ · credential ต้องไม่อยู่ใน sandbox · ขอบเขตครอบ subprocess ที่คำสั่งเรียกต่อ |
| Claude Code docs — [Configure the sandboxed Bash tool](https://code.claude.com/docs/en/sandboxing) | permission rules ตัดสิน "ก่อน" tool รัน · sandbox บังคับ "ขณะ" รันในระดับ OS "regardless of what the model chose to run" · แนะนำ dev container / custom container / VM สำหรับงานที่ไม่มีคนเฝ้า |
| OpenAI — [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) (23 ม.ค. 2026) | sandbox ของ Codex "applies only to the Codex-provided shell tool" · tool จาก MCP server "are not sandboxed by Codex and are responsible for enforcing their own guardrails" → เหตุผลที่ `mcp_server.py` ยังต้องมี guardrail เองแม้อยู่ในห้อง |
| OpenAI — [Introducing Codex](https://openai.com/index/introducing-codex/) (16 พ.ค. 2025) | "The Codex agent operates entirely within a secure, isolated container in the cloud" — แบบ "ทั้งงานอยู่ในห้อง" (Lab นี้ใช้แบบ "เฉพาะมืออยู่ในห้อง" ดูหัวข้อสองแบบด้านล่าง) |
| Docker — [Docker Engine security](https://docs.docker.com/engine/security/) | namespaces / capabilities / `--read-only` / `--cap-drop` ที่ใช้เป็นผนัง |

---

## สถาปัตยกรรม: มืออยู่ในห้อง สมองอยู่นอกห้อง

```
host (เครื่องคุณ)                                   container (ห้อง)  ← docker run -i --rm --network none ...
┌──────────────────────────────┐   MCP ทาง stdin/stdout   ┌──────────────────────────────────────┐
│ agent_loop.py                │ ───── call_tool ──────▶ │ mcp_server.py  (user sandbox, ไม่ใช่ root)│
│  - ถือ OPENROUTER_API_KEY    │ ◀──── result ────────── │  tools: calculate / read_file / run_python│
│  - เรียก LLM ผ่าน OpenRouter  │                          │  เห็นแค่ /work (ro)  เขียนได้แค่ /tmp     │
│  - loop เหมือน Lab 3 ทุกอย่าง │                          │  ไม่มี network  ไม่มี .env  ไม่มี credential│
└──────────────────────────────┘                          └──────────────────────────────────────┘
```

- **ผนัง** = flag ของ `docker run` ใน `agent_loop.py` (`DOCKER_ARGS`) ทุกตัวคือสิ่งที่ OS บังคับ ไม่ใช่คำขอร้องถึงโมเดล
- **ประตู** = `mcp_server.py` ที่ประกาศ tool 3 ตัว — agent ไม่รู้เลยว่า tool อยู่ที่ไหน เห็นแค่ชื่อ/schema ผ่าน `list_tools()`
- **guardrail ที่ประตู** (ต้องมีแม้อยู่ในห้อง): `read_file` ห้ามออกนอก `/work` และห้ามไฟล์ที่ขึ้นต้นด้วยจุด
  (guard ชุดเดียวกับ `read_file` ของ Lab 5), ทุกโค้ดที่รันมี timeout + `RLIMIT_CPU` + `RLIMIT_AS` + จำกัด output

### สองแบบของ "ห้อง" ในโลกจริง

| แบบ | ใครอยู่ในห้อง | ตัวอย่างจริง | Lab นี้ |
| --- | --- | --- | --- |
| ทั้งงานอยู่ในห้อง | agent + tool + โค้ดทั้งหมด | Codex cloud, Anthropic Computer Use reference (Docker) | — |
| เฉพาะมืออยู่ในห้อง | tool เท่านั้น; agent/LLM client อยู่นอก | Claude Code sandbox (เฉพาะ Bash), Codex CLI (เฉพาะ shell tool) | ✅ |

แบบที่ 2 มีข้อควรระวังตรงที่ **สิ่งที่ agent ฝั่ง host ทำเอง** (tool อื่นที่ไม่ได้ผ่าน MCP นี้, MCP server ตัวอื่นบนเครื่อง)
ไม่ได้ถูกผนังนี้กั้น — เหมือนที่ Claude Code docs ระบุว่า Read/Edit/WebFetch ใช้ permission system ไม่ได้อยู่ใน Bash sandbox

---

## ห้องนี้กั้นอะไรบ้าง — เทียบ Lab 6 กับ Lab 6b

| ขอบเขต | Lab 6 (`subprocess` + `resource`) | Lab 6b (container) | ทำอย่างไรใน Lab 6b |
| --- | --- | --- | --- |
| ความลับ (env / API key) | ✅ env มีแค่ PATH | ✅ ไม่มี `.env` ใน image, env ของห้องเป็นของ container | Dockerfile ไม่ COPY อะไรนอกจาก `mcp_server.py` |
| เขียนไฟล์ | ✅ `RLIMIT_FSIZE=0` | ✅ เขียนได้แค่ `/tmp` (tmpfs 32 MB หายเมื่อปิดห้อง) | `--read-only --tmpfs /tmp` + mount `:ro` |
| **อ่านไฟล์นอกห้อง** | ❌ อ่านได้ทั่วเครื่อง | ✅ เห็นแค่ `/work` = workspace เดียวที่ host แบ่งให้ | `-v <workspace>:/work:ro` |
| **network** | ❌ ต่อได้ | ✅ `Network is unreachable` | `--network none` |
| CPU / memory | ✅ `RLIMIT_CPU` (memory ตั้งไม่ได้บน macOS) | ✅ `RLIMIT_CPU` + `RLIMIT_AS` ตั้งได้จริง (Linux) + `--memory --cpus --pids-limit` | `_set_limits()` + flag ของ docker |
| สิทธิ์ | ผู้ใช้เดียวกับคุณ | user `sandbox` (uid 10001) ไม่ใช่ root, ไม่มี capability | `useradd` + `--cap-drop ALL --security-opt no-new-privileges` |
| ต้องติดตั้งอะไรเพิ่ม | ไม่ต้อง | **Docker Desktop / Docker Engine** | — |

พิสูจน์ด้วยตา (ไม่เรียก LLM):

```bash
python labs/lab6b_sandbox_container/probe_sandbox.py
```

ผลที่ควรเห็น: `api_key_visible: false`, `uid: 10001`, `host_home_visible: false`, เขียนได้เฉพาะ `/tmp`,
`network: blocked (Network is unreachable)`, CPU bomb ได้ `exit code -24` แล้วข้อ 6 ยังได้ `60`
(server ในห้องไม่ล่มเพราะรันโค้ดใน process ลูกอีกชั้น)

---

## โค้ดที่ควรอ่าน (ไม่ต้องอ่านทุกบรรทัด)

**`agent_loop.py` (host)** — สิ่งที่เปลี่ยนจาก Lab 3 มีแค่ 3 จุด:

```python
SERVER = StdioServerParameters(command="docker", args=DOCKER_ARGS)   # ผนัง: flag ทั้งหมดอยู่ใน DOCKER_ARGS

async with stdio_client(SERVER) as (read, write):                    # = เปิดห้อง (docker run)
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = to_openai_tools((await session.list_tools()).tools)  # Lab 3 เขียน TOOLS เองกับมือ — ที่นี่ถามห้องว่ามีอะไร
        ...
        result = await dispatch(session, call.function.name, args)   # Lab 3 เรียก function ตรง — ที่นี่ส่งข้ามผนัง
```

**`mcp_server.py` (ในห้อง)** — ประตู 3 บาน + guardrail:

```python
@mcp.tool()
def read_file(path: str) -> str:            # guard เดียวกับ Lab 5: ห้ามออกนอก /work, ห้ามไฟล์ที่ขึ้นต้นด้วยจุด
@mcp.tool()
def run_python(code: str) -> str:           # รันในห้อง: timeout 5 วิ, RLIMIT_CPU 2 วิ, RLIMIT_AS 128 MB, ตัด output
@mcp.tool()
def calculate(expression: str) -> str:      # whitelist เดิมจาก Lab 3 แต่รันใน process ลูกของห้อง
```

ข้อควรรู้ของ stdio transport: **ห้าม `print()` ใน `mcp_server.py`** เพราะ stdout คือสายโปรโตคอล — ถ้าอยาก debug ให้ใช้ stderr

---

## วิธีรัน

```bash
docker build -t lab6b-sandbox labs/lab6b_sandbox_container      # สร้าง image ของห้อง (ครั้งแรกครั้งเดียว)
python labs/lab6b_sandbox_container/agent_loop.py "<คำถาม>"     # agent บน host, tool ในห้อง
python labs/lab6b_sandbox_container/probe_sandbox.py             # ดูว่าห้องกั้นอะไรได้บ้าง
```

ต้องมี Docker ทำงานอยู่ (`docker info` ไม่ error) และติดตั้ง `mcp<2` ฝั่ง host (`pip install -r requirements.txt`)
workspace ที่ห้องเห็นคือ `labs/lab6b_sandbox_container/workspace/` (เปลี่ยนได้ด้วย env `SANDBOX_WORKSPACE`)

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)

---

## ข้อจำกัดที่ยังเหลือ (ตั้งใจให้เห็น)

- **Docker daemon รันด้วยสิทธิ์สูง** — ใครที่สั่ง `docker run` ได้ก็เท่ากับมีสิทธิ์สูงบนเครื่อง Lab นี้จึงเหมาะกับเครื่อง dev
  ของตัวเอง ระบบจริงใช้ rootless container / gVisor / Firecracker (ตาราง Lab 6)
- **ผนังกั้นเฉพาะสิ่งที่ผ่าน MCP นี้** — hook/permission ฝั่ง host (Lab 4) ยังจำเป็น เพราะ container กันความเสียหายต่อเครื่อง
  แต่ไม่ได้กันการทำสิ่งที่ผู้ใช้ไม่ต้องการภายในขอบเขต (เช่น อ่านไฟล์ที่ไม่ควรอ่านใน workspace)
- **ไม่มี network เลย = tool ที่ต้องต่อเน็ตทำไม่ได้** — ของจริงใช้ allowlist domain ผ่าน proxy (แบบ Claude Code) ไม่ใช่ตัดขาด
- **ห้องถูกสร้างใหม่ทุกครั้งที่รัน** — ช้ากว่า Lab 6 ราว 1 วินาทีต่อการเปิดห้อง และ `/tmp` หายทุกครั้ง
- ยังไม่ทำ checkpoint (Lab 5) ร่วมกับห้อง — โจทย์ต่อยอดใน QUESTIONS.md
