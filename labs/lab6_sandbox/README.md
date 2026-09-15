# Lab 6 — Sandbox สำหรับ Tool ที่รันโค้ด

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** โดยไม่แก้ไฟล์ Lab 3 เลย —
> ปิดช่องว่าง **Layer 6 (Sandbox + Execution)** ที่ root README ระบุไว้ว่ายังไม่มี Lab ไหนทำจริง
> ดูตาราง coverage ที่ [README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers](../../README.md#สถาปัตยกรรม-agent-app--agent--llm--8-layers)
>
> เดิมอยู่รวมกับ checkpoint ใน `lab5_sandbox_checkpoint` — แยกออกมาเป็น Lab เดี่ยว เพราะ sandbox
> (Layer 6) กับ checkpoint (Layer 2) เป็นคนละเรื่องกัน — checkpoint ย้ายไปรวมกับ compaction/memory
> ที่ **[Lab 5 — Memory + Checkpoint](../lab5_memory_checkpoint/README.md)** แทน

---

## จุดประสงค์การเรียนรู้

- เข้าใจว่าทำไม tool ที่รันโค้ดของโมเดล (เช่น `eval()`) ต้องถูก **แยกขอบเขต (sandbox)** ออกจาก
  agent loop หลัก ไม่ให้ resource exhaustion ของ tool กระทบ process หลัก
- เห็นข้อจำกัดจริงของการทำ sandbox แบบง่ายๆ (process + resource limit) เทียบกับ sandbox ระดับ
  production (Docker/VM ที่จำกัด filesystem/network ด้วย)
- เจอปัญหา cross-platform จริง (macOS vs Linux) ที่ทำให้การออกแบบ sandbox portable ยากกว่าที่คิด

**ในภาษาคน:** `eval()` คือการสั่งให้ Python คำนวณสูตรจากข้อความ เช่น `'15*4'` — อันตรายเพราะถ้าสูตรใหญ่มาก
(เลขยกกำลังมหาศาล) เครื่องอาจค้าง · **sandbox** = ห้องแล็บที่มีผนังกันระเบิด — ทดลองพลาด ห้องนั้นพัง
แต่ตึกไม่พัง (โปรแกรมหลักไม่กระทบ)

---

## รีเสิร์ช: อ้างอิงจากเอกสารจริง

| แหล่งอ้างอิง | แนวคิดที่ยืมมา |
| --- | --- |
| Anthropic — [Computer Use Tool](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/computer-use-tool) | Sandbox = container/process แยกขอบเขต + **minimal privilege** + **resource limit** + validate ก่อน execute + หยุดทันทีเมื่อเจอ error ตัวแรกใน batch |
| Anthropic — [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | เหตุผลที่ต้อง sandbox โค้ดที่โมเดลสร้าง: ลด token เข้า context ได้มหาศาล + กันข้อมูลลับหลุดเข้า context โดยไม่จำเป็น |

---

## `sandboxed_calculate()`: แยก `eval()` ไปรันใน subprocess + จำกัด CPU

Lab 3 เดิมรัน `eval()` **ตรงใน process หลักของ agent loop เลย** ไม่มีขอบเขตป้องกันอะไรทั้งสิ้น —
ถ้า expression ทำให้ CPU/memory พุ่ง (เช่น เลขยกกำลังมหาศาล `9999**99999999`) จะฉุด agent loop
หลักไปด้วย หรือแย่กว่านั้นคือทำให้ทั้ง process ค้าง/ตาย

สาระของโค้ดด้านล่าง (ไม่ต้องอ่านออกทุกบรรทัด): แทนที่จะคำนวณในโปรแกรมหลัก เราเปิด "โปรแกรมลูก"
แยกออกมาคำนวณ ตั้งเวลาไว้ ถ้าเกินเวลาก็ฆ่าโปรแกรมลูกทิ้ง โปรแกรมหลักไม่เป็นไร:

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

`_WORKER_CODE` คือสคริปต์เล็กๆ ที่รันใน **subprocess แยกจริง**: ตั้ง `resource.setrlimit(RLIMIT_CPU, ...)`
ก่อน `eval()` แล้วค่อยประเมิน expression — ถ้าเกิน CPU limit, OS จะส่ง signal ฆ่า subprocess ทิ้งเอง
โดย process หลักไม่กระทบ

### หมายเหตุข้ามแพลตฟอร์ม (บทเรียนจริงจากการ dev)

**สรุปสั้น:** บน Mac จำกัด memory ของโปรแกรมลูกไม่ได้ จำกัดได้แค่เวลา CPU — โค้ดเลยเขียนให้ทำงานได้
ทั้ง Mac และ Linux โดยไม่พัง รายละเอียดเชิงเทคนิคด้านล่างข้ามได้ถ้ายังไม่เขียนโค้ด

ตอน dev บน macOS พบว่า **`resource.RLIMIT_AS` (จำกัด memory) ตั้งค่าไม่ได้เลย** บน Darwin kernel —
`resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024,)*2)` ได้ `ValueError: current limit exceeds
maximum limit` เสมอไม่ว่าจะตั้งค่าเท่าไหร่ (macOS ไม่รองรับการบังคับ RLIMIT_AS จริงจัง ต่างจาก Linux)
แต่ `RLIMIT_CPU` ใช้ได้ปกติทั้ง 2 แพลตฟอร์ม — โค้ดเลย wrap `RLIMIT_AS` ด้วย `try/except` ให้ใช้เมื่อ
แพลตฟอร์มรองรับ (Linux) แต่ไม่ crash เมื่อไม่รองรับ (macOS) เหลือ `RLIMIT_CPU` + `timeout` ของ
`subprocess.run()` เป็นตาข่ายความปลอดภัยที่พกพาข้ามแพลตฟอร์มได้จริง

**บทเรียน:** กลไก isolation ไม่ portable เท่ากันทุกแพลตฟอร์ม การออกแบบ sandbox ต้องมี fallback
เผื่อกลไกบางตัวใช้ไม่ได้ ไม่ใช่ตั้งสมมติฐานว่า OS ไหนก็รองรับเหมือนกันหมด

### ทดสอบจริง (ยืนยันแล้ว ไม่ใช่แค่ทฤษฎี)

```
[user] ห้ามคำนวณเองหรือประมาณเองเด็ดขาด บังคับให้เรียก tool calculate ด้วย expression '9999**99999999' ตรงๆ ...
[step 1] THINK -> ขอเรียก 1 tool
           TOOL_USE calculate({'expression': '9999**99999999'}) -> error: sandbox process ถูกยุติ (exit code -24, เกิน CPU/memory limit ที่ตั้งไว้)
[step 2] END_TURN
```

`exit code -24` = process ถูกฆ่าด้วย signal `SIGXCPU` (ตรงตามที่ `RLIMIT_CPU` ควรทำ — ตัวเลขติดลบ
แปลว่าโปรแกรมลูกถูกระบบฆ่า ไม่ใช่จบเอง) — **agent loop
หลักไม่กระทบเลย** ได้ error string กลับมาให้ LLM อ่านต่อได้ปกติ ต่างจาก Lab 3 เดิมที่ `eval()` ตัวนี้
จะรันค้างอยู่ใน process หลักโดยตรง

---

## ข้อจำกัดของ sandbox นี้ (ยังไม่ใช่ของจริงระดับ production)

sandbox นี้จำกัดแค่ **process + CPU time** เท่านั้น — ยัง**ไม่ได้จำกัด filesystem** (subprocess
ยังอ่าน/เขียนไฟล์บนเครื่องได้เต็มที่ ถ้ามีใครแอบใส่โค้ดที่ทำแบบนั้นเข้ามาได้) และ**ไม่ได้จำกัด network**
เลย (ไม่มี allowlist domain เหมือนที่ Computer Use Tool ทำ) — เพราะ `calculate()` ของเราจำกัดด้วย
whitelist อักขระอยู่แล้วจนไม่มีทางเรียก I/O ได้ตั้งแต่แรก แต่ถ้าเป็น tool ที่รันโค้ดทั่วไป (ไม่ใช่แค่
เลขคณิต) ข้อจำกัดนี้จะสำคัญมาก — ดูตารางเทียบ framework ด้านล่าง

## เทียบกับ framework จริงในระบบนิเวศ

ไม่ต้องรู้จักทุกชื่อในตาราง — แค่รู้ว่าของจริงในอุตสาหกรรมกันหนากว่าที่เราทำใน Lab นี้มาก:

| Framework | ระดับ isolation | ครอบคลุม filesystem/network ไหม |
| --- | --- | --- |
| **`subprocess` + `resource` (ที่นี่)** | Process-level, CPU time เท่านั้น | ❌ ไม่ครอบคลุม |
| **Docker** | Container-level | ✅ (ref implementation ของ Anthropic Computer Use เอง — isolated filesystem + network allowlist) |
| **E2B** | Managed sandbox-as-a-service | ✅ ออกแบบมาเฉพาะสำหรับรันโค้ดที่ AI agent สร้าง |
| **gVisor / Firecracker** | VM-level (microVM) | ✅ isolation แน่นกว่า Docker — ที่ AWS Lambda/Fly.io ใช้จริง |

---

## วิธีรัน

```bash
python labs/lab6_sandbox/agent_loop.py "<คำถาม>"
```

ดูแบบฝึกหัดเพิ่มเติมที่ [QUESTIONS.md](QUESTIONS.md)
