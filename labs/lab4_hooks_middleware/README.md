# Lab 4 — Hooks / Middleware ต่อยอด Agent Loop

> ต่อยอดจาก **[Lab 3 — Agent Loop](../lab3_agent_loop/README.md)** โดยไม่แก้ `agent_loop.py`
> เดิมเลยแม้แต่บรรทัดเดียว — เพิ่ม hook engine เข้าไปห่อ loop เดิมรอบนอกเท่านั้น
>
> ก่อนหน้านี้มี **[Lab 3a — Self-Correction ด้วย prompt](../lab3a_self_correction/README.md)**
> ที่ลองแก้ปัญหาเดียวกันด้วย `SYSTEM` prompt ล้วนๆ แล้วเจอข้อจำกัดว่าไม่การันตี — Lab 4 นี้แก้ปัญหา
> แบบเดียวกันให้ **deterministic จริง** ด้วยโค้ด ไม่ใช่แค่ขอร้องผ่าน prompt
>
> ต้นทาง Lab 3: `labs/lab3_agent_loop/` ของ repo ต้นทางของหลักสูตร **Agentic AI Development with Python**
> (สำเนาอยู่ใน repo นี้แล้ว ไม่ต้องเปิด repo ต้นทาง)
>
> ดูคำถามตัวอย่างและแบบฝึกหัดแยกไว้ที่ [QUESTIONS.md](QUESTIONS.md)

**hook คืออะไรในภาษาคน:** ผู้ช่วยที่ยืนข้าง AI คอยตรวจ**ทุกครั้ง**ก่อน AI จะกดปุ่มอะไร (เรียก tool)
และหลังได้ผลกลับมา — ถ้าผิดกติกาก็ห้ามกด หรือแก้ข้อมูลให้ก่อนส่งต่อ ต่างจาก Lab 3a ที่ "ขอร้อง" AI
ผ่าน system prompt ตรงนี้ "บังคับ" ด้วยโปรแกรม AI ไม่มีสิทธิ์เลือกว่าจะทำตามหรือไม่

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

> **ตารางด้านบนอธิบาย "ของจริง" ของ 2 บริษัทเท่านั้น** (Claude Code = โปรแกรม AI เขียนโค้ดของ Anthropic ·
> Agents SDK = ชุดเครื่องมือสร้าง agent ของ OpenAI) — hook ใน repo นี้ (`core/hooks.py`) เป็น Python
> function ธรรมดา **ไม่ใช้ subprocess / HTTP / JSON เลย** เราเอามาแค่แนวคิด ไม่ได้เอาโค้ดมา

**สรุปสิ่งที่ยืมมาออกแบบ `core/hooks.py`:**
- เอา **event/matcher ของ Claude Code** (จุดแทรกชัดเจน + กรองด้วยชื่อ tool) มาเป็นโครง
- เอา **แนวคิด tripwire ของ OpenAI** มาเป็น decision `"deny"` (แทนที่จะ raise exception เพราะ
  agent loop ของเรารันใน process เดียว ไม่ต้องข้าม process แบบ Claude Code hook)
- เพิ่ม decision `"modify"` เอง (ไม่มีในทั้งสองระบบตรง ๆ) เพื่อให้ hook แก้ไขข้อมูลแล้วส่งต่อ
  hook ถัดไปได้ เหมือน middleware chain ทั่วไป — ใกล้เคียงกับ `updatedInput` ของ Claude Code
  แต่ทำเป็น chain ได้มากกว่า 1 hook

---

## `HookResult` คืออะไร

เวลาเราเขียนฟังก์ชัน hook สักตัวขึ้นมา (เช่น "เช็คว่านิพจน์ที่จะคำนวณยาวเกินไปไหม") ฟังก์ชันนั้น
ต้องมีวิธี "บอกผลการเช็ค" กลับไปให้ระบบรู้ว่า:

- ควรปล่อยผ่านไปตามปกติไหม
- ควรบล็อกไม่ให้ทำขั้นต่อไปไหม (ถ้าบล็อก เพราะอะไร)
- ควรแก้ไขข้อมูลก่อนส่งต่อไหม (ถ้าแก้ แก้เป็นอะไร)

`HookResult` คือรูปแบบผลลัพธ์ที่ตายตัว ให้ hook function **ทุกตัว** คืนกลับมาแบบเดียวกันหมด
เพื่อให้ส่วนอื่นของระบบอ่านและเข้าใจตรงกัน — คล้ายการกรอกแบบฟอร์มมาตรฐาน คนอ่านไม่ต้องเดาว่า
แต่ละคนจะเขียนคำตอบมาในรูปแบบไหน:

ไม่ต้องอ่าน syntax Python ออกก็ได้ — 4 บรรทัดในกล่องคือ "ช่อง" 4 ช่องของแบบฟอร์ม ดูตารางถัดไปพอ:

```python
@dataclass
class HookResult:
    decision: str = "allow"                 # allow | deny | modify
    reason: str | None = None               # เหตุผล (ใช้ตอน deny)
    data: dict | None = None                # ข้อมูลที่แก้ไขแล้ว (ใช้ตอน modify)
    additional_context: str | None = None   # ข้อความเสริมที่จะแทรกกลับเข้าไป
```

แต่ละ field มีหน้าที่ต่างกัน และมีคนเขียน/คนอ่านคนละฝั่ง:

| Field | มีไว้ทำอะไร | ใครเขียนค่านี้ | ใครอ่านค่านี้ไปใช้ |
| --- | --- | --- | --- |
| `decision` | บอกว่า "ปล่อยผ่าน" (`allow`), "บล็อก" (`deny`), หรือ "แก้ไขแล้วปล่อยผ่าน" (`modify`) | hook function ที่เราเขียน | `HookManager` — ใช้ตัดสินใจว่าจะทำอะไรต่อ |
| `reason` | ข้อความอธิบายเหตุผล ใช้ตอน `deny` | hook function | โค้ดที่เรียกใช้ — เอาไป log หรือแสดงข้อความปฏิเสธ |
| `data` | ข้อมูลฉบับแก้ไขแล้ว ใช้ตอน `modify` | hook function | `HookManager` — เอาไปอัปเดตข้อมูลก่อนส่งต่อ |
| `additional_context` | ข้อความเสริมที่อยากแทรกเข้าไปในบทสนทนา | hook function | โค้ดที่เรียกใช้ — เอาไปต่อท้ายข้อความ |

พูดสั้นๆ: **`HookResult` ไม่มี logic การตัดสินใจอะไรอยู่ในตัวมันเองเลย มันแค่เป็นที่เก็บผลลัพธ์**
ตัวที่เอาผลลัพธ์นี้ไปใช้ตัดสินใจ/ทำงานต่อจริงๆ คือ `HookManager` (อธิบายต่อด้านล่าง)

---

## `HookManager` คืออะไร

ถ้า `HookResult` คือที่เก็บผลลัพธ์จาก hook function 1 ตัว `HookManager` คือ**ตัวที่รวบรวม hook
function หลายตัวไว้ด้วยกัน แล้วเรียกให้ทำงานตามลำดับ**:

```python
class HookManager:
    def register(self, event, fn, matcher=None): ...
    def run(self, event, payload, tool_name=None) -> HookResult: ...
```

- **`register(event, fn, matcher)`** — ลงทะเบียนว่า function ตัวนี้ (`fn`) ให้ทำงานตอน event ไหน
  (เช่น `"pre_tool"`) ถ้าใส่ `matcher` ไว้ด้วย จะทำงานเฉพาะตอนชื่อ tool ตรงกับที่ระบุเท่านั้น
- **`run(event, payload, tool_name)`** — เรียก hook function ทุกตัวที่ลงทะเบียนไว้กับ event นั้น
  **ตามลำดับที่ลงทะเบียน** แล้วอ่านค่า `.decision` ใน `HookResult` ที่แต่ละตัวคืนมา เพื่อตัดสินใจ
  ว่าจะทำอะไรต่อ

5 event ที่ `HookManager` รองรับ map ตรงกับจังหวะจริงของ `run_agent()` ใน Lab 3:

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

**พฤติกรรมของ `run()` ตอนเจอแต่ละ `decision`:**
- เจอ `HookResult` ที่ `decision == "deny"` ตัวแรก → **หยุดทันที** คืน `HookResult` ตัวนั้นกลับไป
  เลยทั้งก้อน ไม่เรียก hook ที่เหลือต่อ (เหมือน exit code 2 ของ Claude Code หรือ exception ของ
  OpenAI Guardrails)
- ถ้าไม่มีตัวไหน `deny` เลย → เอา `.data` จากทุก `HookResult` ที่เป็น `modify` มารวมกัน แล้ว
  **สร้าง `HookResult` ใหม่**ที่มี `decision == "allow"` ส่งกลับไป — สังเกตว่า `"modify"` ที่ hook
  function คืนมา จะไม่ใช่ค่าสุดท้ายที่ผู้เรียกเห็น มันถูกแปลงเป็น `"allow"` เสมอตอนจบ

---

## Hook ตัวอย่าง 4 ตัวใน `agent_loop_hooks.py`

1. **`audit_log_hook`** — เขียนทุก `pre_tool`/`post_tool`/`stop` เป็น audit trail ลง `agent_audit.log`
   (audit trail = สมุดบันทึกว่า AI ทำอะไร ตอนไหน เอาไว้ตรวจย้อนหลัง — ไฟล์ `.log` เปิดด้วย text editor
   ธรรมดาได้ 1 บรรทัด = 1 เหตุการณ์)
2. **`guard_calculate_hook`** (matcher `"calculate"`) — `deny` ถ้านิพจน์ยาวผิดปกติ (>40 ตัวอักษร),
   `modify` (ตัดช่องว่างหน้า-หลัง) ถ้าจำเป็น — defense-in-depth เพิ่มจาก whitelist ที่ `calculate()`
   ใน Lab 3 มีอยู่แล้ว
3. **`redact_secrets_hook`** — เจอข้อความหน้าตาเหมือน API key (`sk-...`, ตามตัวอย่างจริงในเอกสาร
   OpenAI Guardrails) ใน tool output ให้ **redact** (แทนที่ข้อความลับด้วย `[REDACTED]` ก่อนส่งต่อ
   เหมือนเอกสารที่มีข้อความบางส่วนถูกปิดทับไม่ให้อ่านออก) **ก่อน** ป้อนกลับเข้า context ของ LLM
4. **`require_number_on_stop_hook`** — ถ้าคำถามดูเหมือนโจทย์คำนวณแต่คำตอบไม่มีตัวเลขเลย ให้
   `deny` การจบ turn 1 ครั้ง แล้วบังคับให้ LLM ตอบใหม่

> จุดที่ควรสังเกต: ใน `build_default_hooks()` ลำดับ `register()` มีผลจริง — ต้อง
> `redact_secrets_hook` ก่อน `audit_log_hook` เสมอ ไม่งั้น secret ดิบจะหลุดเข้าไปอยู่ใน audit log
> แทนที่จะถูก redact ก่อน (เทสยืนยันเรื่องนี้ไว้ใน `test_hooks.py`)

---

## จากทฤษฎีสู่ของจริง: จุดที่ engine กับ hook ทั้ง 4 ตัวมาเจอกัน

`build_default_hooks()` คือจุดที่เอา hook function ทั้ง 4 ตัวด้านบนไป `register()` เข้ากับ `HookManager`:

```python
def build_default_hooks() -> HookManager:
    hooks = HookManager()
    hooks.register("pre_tool", audit_log_hook)
    hooks.register("pre_tool", guard_calculate_hook, matcher="calculate")
    hooks.register("post_tool", redact_secrets_hook)
    hooks.register("post_tool", audit_log_hook)
    hooks.register("stop", require_number_on_stop_hook)
    hooks.register("stop", audit_log_hook)
    return hooks
```

จากนั้น `run_agent()` เป็นตัวเรียก `hooks.run(event, payload, ...)` จริงที่ 5 จุดในวง loop — ตรงนั้นแหละที่
function ที่ `register()` ไว้ถูกเรียกทำงานจริง แล้ว `HookResult` ที่แต่ละ function คืนมาก็เดินทางกลับไป
ให้ `run_agent()` อ่านต่อ ลอง trace เคส "นิพจน์ยาวเกิน 40 ตัวอักษร" ดูทีละขั้น:

1. `run_agent()` เจอ tool call `calculate` → เรียก `hooks.run("pre_tool", {...}, tool_name="calculate")`
2. `HookManager` ไล่ hook ที่ register กับ `pre_tool` ตามลำดับ:
   - `audit_log_hook` ทำงาน → เขียน log → คืน `HookResult(decision="allow")`
   - `guard_calculate_hook` ทำงาน (matcher ตรงกับ `"calculate"`) → เช็คความยาว → คืน
     `HookResult(decision="deny", reason="นิพจน์ยาวเกินไป...")`
3. `HookManager` เจอ `decision == "deny"` → หยุดทันที ส่ง `HookResult` ตัวนี้ (ตัวเดิมจาก
   `guard_calculate_hook` เป๊ะๆ ไม่ได้สร้างใหม่) กลับไปให้ `run_agent()`
4. `run_agent()` รับ `HookResult` มา อ่าน `.decision` เจอว่าเป็น `"deny"` → **ไม่เรียก `dispatch()`
   เลย** (`calculate()` จริงจาก Lab 3 ไม่ถูกรัน) แล้วอ่าน `.reason` ไปพิมพ์เป็นข้อความปฏิเสธแทน

เส้นทางเต็ม: **`HookResult` (รูปแบบผลลัพธ์) → `HookManager` (ตัวรวบรวม+ตัดสินใจ) → Hook ตัวอย่าง
(ฟังก์ชันที่คืน `HookResult`) → `build_default_hooks()` (จุดเสียบทุกอย่างเข้าด้วยกัน) →
`run_agent()` (จุดที่ทุกอย่างถูกเรียกใช้งานจริง)**

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
OpenRouter จริง — monkeypatch/stub = สลับตัวเรียก AI จริงเป็นตัวปลอมที่ตอบตามบท เพื่อทดสอบได้โดยไม่เสียเงิน
และไม่ต้องมี API key) แล้วรัน `run_agent()` เต็มวงจริง ยืนยัน 3 เคส:

1. `pre_tool` modify (ตัดช่องว่าง) + deny (นิพจน์ยาวเกิน) + `stop` บังคับ retry จนกว่าคำตอบจะมีตัวเลข
2. `post_tool` redact secret ก่อนที่จะหลุดเข้า audit log (เช็คว่า log ไม่มี secret ดิบเลย)
3. เมื่อ `pre_tool` deny แล้ว `dispatch()` จริงต้อง**ไม่ถูกเรียก**เลย

รันแล้วต้องเห็น `ALL TESTS PASSED` ที่บรรทัดสุดท้าย
