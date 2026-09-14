# Lab 4 — Hooks / Middleware ต่อยอด Agent Loop

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** โดยไม่แก้ `agent_loop.py`
> เดิมเลยแม้แต่บรรทัดเดียว — เพิ่ม hook engine เข้าไปห่อ loop เดิมรอบนอกเท่านั้น
>
> ต้นทาง Lab 3: [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph)
> (`labs/lab3_agent_loop/`) — repo หลักสูตร **Agentic AI Development with Python**
>
> ดูคำถามตัวอย่างและแบบฝึกหัดแยกไว้ที่ [QUESTIONS.md](QUESTIONS.md)

---

## จุดประสงค์การเรียนรู้

- เข้าใจว่า **Hooks** (Anthropic) และ **Middleware/Guardrails** (OpenAI) แก้ปัญหาเดียวกัน
  ด้วยกลไกต่างกัน แล้วออกแบบ engine กลางที่รวม 2 แนวคิดเข้าด้วยกันได้
- เห็นว่า agent loop ที่ "เปลือย" (Lab 3) เพิ่ม safety/observability layer เข้าไปได้โดยไม่ต้อง
  แก้ core logic
- ฝึกเขียน test ที่ยืนยัน behavior ของ middleware โดยไม่ต้องพึ่ง LLM จริง (stub การเรียก API)

---

## รีเสิร์ช: Hooks (Anthropic) vs Guardrails (OpenAI)

อ่านจากเอกสารทางการ 2 แหล่ง:

| แหล่งอ้างอิง | กลไก | จุดเด่น |
| --- | --- | --- |
| Anthropic — [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks) | Event-based: `PreToolUse`/`PostToolUse`/`Stop`/`UserPromptSubmit` ฯลฯ ยิงเป็น subprocess/HTTP คุยกันผ่าน JSON บน stdin/stdout, ตัดสินด้วย exit code + `permissionDecision: allow\|deny` + `updatedInput` (แก้ input ก่อนส่งต่อ) | กำหนดจังหวะ (event) ได้ละเอียดมาก, `matcher` กรองด้วยชื่อ tool แบบ regex, รองรับ deterministic policy enforcement |
| OpenAI — [Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/) | Function-based: hook function คืน `GuardrailFunctionOutput(output_info, tripwire_triggered)` — ถ้า `tripwire_triggered=True` ระบบโยน exception (`InputGuardrailTripwireTriggered` ฯลฯ) หยุดทันที | เขียนเป็น Python function ธรรมดา, มี input/output/tool guardrail แยกชัดเจน, ตัวอย่างจริงในเอกสารคือการ block ข้อความที่มี `"sk-"` (secret) ใน tool arguments |

**สรุปสิ่งที่ยืมมาออกแบบ `core/hooks.py`:**
- เอา **event/matcher ของ Claude Code** (จุดแทรกชัดเจน + กรองด้วยชื่อ tool) มาเป็นโครง
- เอา **แนวคิด tripwire ของ OpenAI** มาเป็น decision `"deny"` (แทนที่จะ raise exception เพราะ
  agent loop ของเรารันใน process เดียว ไม่ต้องข้าม process แบบ Claude Code hook)
- เพิ่ม decision `"modify"` เอง (ไม่มีในทั้งสองระบบตรง ๆ) เพื่อให้ hook แก้ไขข้อมูลแล้วส่งต่อ
  hook ถัดไปได้ เหมือน middleware chain ทั่วไป — ใกล้เคียงกับ `updatedInput` ของ Claude Code
  แต่ทำเป็น chain ได้มากกว่า 1 hook

---

## ออกแบบ: `labs/core/hooks.py`

```python
@dataclass
class HookResult:
    decision: str = "allow"                 # allow | deny | modify
    reason: str | None = None
    data: dict | None = None
    additional_context: str | None = None

class HookManager:
    def register(self, event, fn, matcher=None): ...
    def run(self, event, payload, tool_name=None) -> HookResult: ...
```

5 event ที่รองรับ map ตรงกับจังหวะจริงของ `run_agent()` ใน Lab 3:

```
pre_llm -> [LLM] -> post_llm -> (tool_calls?)
    -> pre_tool -> [dispatch จริง] -> post_tool -> วนกลับ pre_llm
    -> (ไม่มี tool_calls) -> stop -> END_TURN
```

| Event | ยิงตอนไหน | เทียบกับ |
| --- | --- | --- |
| `pre_llm` / `post_llm` | ก่อน/หลังเรียก LLM แต่ละรอบ | `on_llm_start`/`on_llm_end` (OpenAI SDK) |
| `pre_tool` | ก่อนเรียก tool จริง | `PreToolUse` (Claude Code) |
| `post_tool` | หลังได้ผล tool ก่อนป้อนกลับ LLM | `PostToolUse` (Claude Code) |
| `stop` | ก่อนจบ turn (`END_TURN`) | `Stop` hook (Claude Code) / output guardrail (OpenAI) |

`HookManager.run()` เจอ `"deny"` ตัวแรกจะ short-circuit ทันที (เหมือน exit code 2 ของ Claude Code /
exception ของ OpenAI) ส่วน `"modify"` จะ merge `data` เข้า payload แล้วส่งต่อให้ hook ถัดไปเห็นค่าใหม่

---

## Hook ตัวอย่าง 4 ตัวใน `agent_loop_hooks.py`

1. **`audit_log_hook`** — เขียนทุก `pre_tool`/`post_tool`/`stop` เป็น audit trail ลง `agent_audit.log`
2. **`guard_calculate_hook`** (matcher `"calculate"`) — `deny` ถ้านิพจน์ยาวผิดปกติ (>40 ตัวอักษร),
   `modify` (ตัดช่องว่างหน้า-หลัง) ถ้าจำเป็น — defense-in-depth เพิ่มจาก whitelist ที่ `calculate()`
   ใน Lab 3 มีอยู่แล้ว
3. **`redact_secrets_hook`** — เจอข้อความหน้าตาเหมือน API key (`sk-...`, ตามตัวอย่างจริงในเอกสาร
   OpenAI Guardrails) ใน tool output ให้ redact **ก่อน** ป้อนกลับเข้า context ของ LLM
4. **`require_number_on_stop_hook`** — ถ้าคำถามดูเหมือนโจทย์คำนวณแต่คำตอบไม่มีตัวเลขเลย ให้
   `deny` การจบ turn 1 ครั้ง แล้วบังคับให้ LLM ตอบใหม่

> จุดที่ควรสังเกต: ใน `build_default_hooks()` ลำดับ `register()` มีผลจริง — ต้อง
> `redact_secrets_hook` ก่อน `audit_log_hook` เสมอ ไม่งั้น secret ดิบจะหลุดเข้าไปอยู่ใน audit log
> แทนที่จะถูก redact ก่อน (เทสยืนยันเรื่องนี้ไว้ใน `test_hooks.py`)

---

## วิธีรัน

รันจาก **root ของ repo** เสมอ (เพราะ import `labs.core.*` แบบเดียวกับ Lab 3):

```bash
pip install -r requirements.txt
cp .env.example .env   # ใส่ OPENROUTER_API_KEY จริงจาก https://openrouter.ai/keys

python labs/lab4_hooks_middleware/agent_loop_hooks.py "<คำถาม>"
```

ผลลัพธ์จะเหมือน Lab 3 เดิม บวกบรรทัด `HOOK ...` เวลามี hook ตัวไหน deny/modify และไฟล์
`labs/lab4_hooks_middleware/agent_audit.log` จะถูกสร้าง/เพิ่มบรรทัดใหม่ทุกครั้งที่รัน — ดูคำถาม
ตัวอย่างและแบบฝึกหัดที่ทำให้ hook แต่ละตัว trigger จริงได้ที่ [QUESTIONS.md](QUESTIONS.md)

### รัน test โดยไม่ต้องมี API key จริง

```bash
python labs/lab4_hooks_middleware/test_hooks.py
```

`test_hooks.py` monkeypatch `labs.core.llm.chat` ให้คืนคำตอบตามสคริปต์ที่กำหนดไว้ล่วงหน้า (ไม่เรียก
OpenRouter จริง) แล้วรัน `run_agent()` เต็มวงจริง ยืนยัน 3 เคส:

1. `pre_tool` modify (ตัดช่องว่าง) + deny (นิพจน์ยาวเกิน) + `stop` บังคับ retry จนกว่าคำตอบจะมีตัวเลข
2. `post_tool` redact secret ก่อนที่จะหลุดเข้า audit log (เช็คว่า log ไม่มี secret ดิบเลย)
3. เมื่อ `pre_tool` deny แล้ว `dispatch()` จริงต้อง**ไม่ถูกเรียก**เลย

รันแล้วต้องเห็น `ALL TESTS PASSED` ที่บรรทัดสุดท้าย
