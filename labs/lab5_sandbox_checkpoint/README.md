# Lab 5 — Sandbox + Checkpoint สำหรับ Agent ที่รันยาว

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** โดยไม่แก้ไฟล์ Lab 3 เลย —
> คัดลอกโครงมาที่นี่แล้วเพิ่ม 2 ความสามารถที่ root README ระบุไว้ว่ายังไม่มี Lab ไหนทำจริงเลย:
> **Layer 6 (Sandbox + Execution)** และ **Layer 2 (Memory/checkpoint)** — ดูตาราง coverage ที่
> [README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers](../../README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers)

---

## จุดประสงค์การเรียนรู้

- เข้าใจว่าทำไม tool ที่รันโค้ดของโมเดล (เช่น `eval()`) ต้องถูก **แยกขอบเขต (sandbox)** ออกจาก
  agent loop หลัก ไม่ให้ resource exhaustion ของ tool กระทบ process หลัก
- เข้าใจว่า **checkpoint** คือการบันทึก state เป็นระยะ เพื่อให้ agent ที่รันยาว **กู้คืนได้จริง**
  เมื่อ process ถูกฆ่ากลางทาง (crash, kill, restart) โดยไม่ต้องเริ่มงานใหม่ตั้งแต่ต้น
- เห็นว่า 2 เรื่องนี้แก้ปัญหาคนละมิติกัน: sandbox = ป้องกัน "ทำอะไรพัง", checkpoint = ป้องกัน
  "เสียงานที่ทำไปแล้ว"

---

## รีเสิร์ช: อ้างอิงจากเอกสารจริง 3 แหล่ง

| แหล่งอ้างอิง | แนวคิดที่ยืมมา |
| --- | --- |
| Anthropic — [Computer Use Tool](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool) | Sandbox = container/process แยกขอบเขต + **minimal privilege** + **resource limit** + validate ก่อน execute + หยุดทันทีเมื่อเจอ error ตัวแรกใน batch |
| Anthropic — [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | เหตุผลที่ต้อง sandbox โค้ดที่โมเดลสร้าง: ลด token เข้า context ได้มหาศาล + กันข้อมูลลับหลุดเข้า context โดยไม่จำเป็น |
| LangGraph — [Persistence / Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | Checkpoint = บันทึก state **หลังจบทุก node/step** คีย์ด้วย **`thread_id`** — resume คือเรียกซ้ำด้วย `thread_id` เดิม ระบบโหลด checkpoint ล่าสุดแล้ววิ่งต่อจากจุดนั้น |

---

## (1) Sandbox: `sandboxed_calculate()`

Lab 3 เดิมรัน `eval()` **ตรงใน process หลักของ agent loop เลย** ไม่มีขอบเขตป้องกันอะไรทั้งสิ้น —
ถ้า expression ทำให้ CPU/memory พุ่ง (เช่น เลขยกกำลังมหาศาล `9999**99999999`) จะฉุด agent loop
หลักไปด้วย หรือแย่กว่านั้นคือทำให้ทั้ง process ค้าง/ตาย

ที่นี่ห่อ `eval()` ด้วย **subprocess แยก process จริง** + จำกัด CPU time ด้วย `resource.setrlimit`
(แนวคิดเดียวกับ "minimal privilege + resource limit" ของ Computer Use Tool):

```python
def sandboxed_calculate(expression: str) -> str:
    code = _WORKER_CODE.format(cpu_sec=SANDBOX_CPU_SEC, mem_bytes=SANDBOX_MEMORY_MB * 1024 * 1024)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code, expression],
            capture_output=True, text=True, timeout=SANDBOX_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return f"error: sandbox timeout — คำนวณนานเกิน {SANDBOX_TIMEOUT_SEC} วินาที (agent loop หลักไม่กระทบ)"
    if proc.returncode != 0:
        return f"error: sandbox process ถูกยุติ (exit code {proc.returncode}, เกิน CPU/memory limit)"
    ...
```

> **หมายเหตุข้ามแพลตฟอร์ม:** ตอน dev บน macOS พบว่า `resource.RLIMIT_AS` (จำกัด memory) **ตั้งค่าไม่ได้เลย**
> บน Darwin kernel (ได้ `ValueError: current limit exceeds maximum limit` เสมอไม่ว่าจะตั้งค่าเท่าไหร่)
> แต่ `RLIMIT_CPU` ใช้ได้ปกติทั้ง macOS และ Linux — โค้ดเลย wrap `RLIMIT_AS` ด้วย `try/except` ให้ใช้
> เมื่อแพลตฟอร์มรองรับ (Linux) แต่ไม่ crash เมื่อไม่รองรับ (macOS) เหลือ `RLIMIT_CPU` + `timeout`
> ที่ `subprocess.run()` เป็นตาข่ายความปลอดภัยที่พกพาข้ามแพลตฟอร์มได้จริง — **นี่คือบทเรียนจริงของ
> การทำ sandbox: กลไก isolation ไม่ portable เท่ากันทุกแพลตฟอร์ม ต้องออกแบบให้ fallback ได้**

### ทดสอบจริง (ยืนยันแล้ว ไม่ใช่แค่ทฤษฎี)

```
[user] ห้ามคำนวณเองหรือประมาณเองเด็ดขาด บังคับให้เรียก tool calculate ด้วย expression '9999**99999999' ตรงๆ ...
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE calculate({'expression': '9999**99999999'}) -> error: sandbox process ถูกยุติ (exit code -24, เกิน CPU/memory limit ที่ตั้งไว้)
[step 2] END_TURN
[answer] ... Tool `calculate` ถูก OS ยุติ process (exit code -24 = SIGXCPU) ...
```

`exit code -24` = process ถูกฆ่าด้วย signal `SIGXCPU` (ตรงตามที่ `RLIMIT_CPU` ควรทำ) — **agent loop
หลักไม่กระทบเลย** ได้ error string กลับมาให้ LLM อ่านต่อได้ปกติ ต่างจาก Lab 3 เดิมที่ `eval()` ตัวนี้
จะรันค้างอยู่ใน process หลักโดยตรง

---

## (2) Checkpoint: `save_checkpoint()` / `load_checkpoint()` / `thread_id`

เพิ่ม `thread_id` เข้า `run_agent()` แล้วบันทึก `messages` + `step` ลงไฟล์ JSON **หลังจบทุก step**
(เทียบกับ "บันทึกหลังจบทุก node" ของ LangGraph checkpointer) — ถ้าเรียก `run_agent()` ด้วย
`thread_id` เดิมที่มี checkpoint ค้างอยู่ จะโหลด state ล่าสุดมาวิ่งต่อ **ไม่เริ่มใหม่**

```python
def run_agent(question: str, thread_id: str = "default", max_steps: int = 6):
    checkpoint = load_checkpoint(thread_id)
    if checkpoint:
        messages = checkpoint["messages"]
        start_step = checkpoint["step"] + 1
        print(f"[resume] พบ checkpoint ... วิ่งต่อจาก step {start_step}")
    else:
        messages = [...]
        start_step = 1
    ...
    save_checkpoint(thread_id, messages, step)   # หลังจบทุก step ที่มี tool_calls
    ...
    clear_checkpoint(thread_id)   # ลบทิ้งเมื่องานเสร็จสมบูรณ์ (END_TURN)
```

### ทดสอบจริง — จำลอง crash จริงด้วย `SIGKILL` แล้ว resume (ยืนยันแล้ว)

ใช้คำถามที่บังคับให้เกิด 2 step จริง (ต้องรู้ผลจาก `get_time` ก่อนถึงจะคำนวณ step ถัดไปได้) รันเป็น
subprocess จริง แล้วส่ง `SIGKILL` **ทันทีที่เห็น step 2 เริ่ม** (จำลอง process ถูกฆ่ากลางทาง):

```
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE get_time({}) -> 2026-09-15 12:59:11
[step 2] THINK -> ขอเรียก 1 tool
>>> KILL -9 ทันที <<<
>>> returncode=-9 <<<
```

เช็ค checkpoint file บนดิสก์หลังถูกฆ่า — **ยังอยู่จริง** พร้อม state ของ step 1 ครบ (system/user/
assistant tool_calls/tool result) รันคำสั่งเดิมซ้ำด้วย `thread_id` เดิม:

```
[resume] พบ checkpoint ของ thread 'crash-demo2' ที่ step 1 -> วิ่งต่อจาก step 2
[step 2] THINK -> ขอเรียก 1 tool
           TOOL_USE calculate({'expression': '59*100'}) -> 5900
[step 3] END_TURN
[answer] ... นาที (MM): 59 ... 59 × 100 = 5900
```

สังเกตว่า **ไม่มีการเรียก `get_time` ซ้ำเลย** — เลข `59` ที่ใช้คำนวณคือค่าที่ได้จาก`get_time` ของ
รอบที่ถูกฆ่าไปแล้ว (ตรงกับนาทีของเวลา `12:59:11` ที่บันทึกไว้ใน checkpoint) พิสูจน์ว่า resume ใช้
state เดิมจริง ไม่ใช่เริ่มนับ 1 ใหม่ — และหลังจบสมบูรณ์ checkpoint file ก็ถูกลบทิ้งอัตโนมัติ

---

## เทียบกับ framework จริงในระบบนิเวศ

| ความสามารถ | Pure Python (Lab นี้) | Framework/บริการที่ทำเรื่องเดียวกัน |
| --- | --- | --- |
| **Sandbox + Execution** | `subprocess` + `resource.setrlimit` (CPU) + `timeout` | **Docker** (container-level, ref implementation ของ Anthropic Computer Use เอง) · **E2B** (managed sandbox-as-a-service เฉพาะทางสำหรับโค้ดที่ AI สร้าง) · **gVisor / Firecracker** (microVM-level, ที่ AWS Lambda/Fly.io ใช้จริง — isolation แน่นกว่า Docker) |
| **Checkpoint / Persistence** | ไฟล์ JSON ต่อ `thread_id` | **LangGraph checkpointer** (`InMemorySaver`/`SqliteSaver`/`PostgresSaver`) — ตัวที่ root README ของ repo ต้นทางอ้างถึงตรงๆ ว่า Lab 8 (LangGraph) จะได้ "ฟรี" เทียบกับที่ Lab 1-7 เขียนเอง · **Temporal** (workflow engine ระดับ production ที่ทำ durable execution ในตัว) · **Redis** (มักใช้เป็น storage backend ให้ checkpointer อื่นอีกที ไม่ใช่ตัว logic เอง) |

**จุดสังเกต:** repo ต้นทางมี pattern เดิมตลอดทั้งหลักสูตร (Lab 1-7 เขียน pure Python เอง → Lab 8 เทียบ
กับ LangGraph "ได้ฟรี") — **checkpoint มีของเทียบอยู่แล้วในหลักสูตรเดิม** (LangGraph checkpointer)
แต่ **sandbox ไม่มีของเทียบเลย** เพราะ Layer 6 เป็นช่องว่างที่ root README ของหลักสูตรเดิมยอมรับตรงๆ
ว่ายังไม่มี Lab ไหนทำจริง (`course2_outline-1.pdf` บอกว่าอยู่นอกขอบเขต)

---

## วิธีรัน

```bash
python labs/lab5_sandbox_checkpoint/agent_loop.py "<คำถาม>" [thread_id]
```

`thread_id` เป็น argument ที่สอง (ไม่ใส่จะใช้ `"default"`) — checkpoint ไฟล์จะถูกเก็บไว้ที่
`labs/lab5_sandbox_checkpoint/checkpoints/<thread_id>.json` (gitignored เพราะเป็น runtime state
ไม่ใช่ source code)

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)
