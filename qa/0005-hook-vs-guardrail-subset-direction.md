# Q&A Log — Entry 0005

**วันที่:** 2026-09-15
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

ผมคิดว่า hook อยู่ภายใต้ concept "guardrail" นะ

## คำตอบ (verbatim)

ทิศทางกลับกันครับ — **guardrail อยู่ภายใต้ concept hook มากกว่า** ไม่ใช่ hook อยู่ภายใต้ guardrail

### เหตุผล: hook คือ "กลไกทั่วไป" ส่วน guardrail คือ "จุดประสงค์เฉพาะ" ของสิ่งที่ใส่เข้าไปในกลไกนั้น

- **Hook** = จุดแทรก (interception point) ในวงจรการทำงาน ที่ยอมให้ใส่โค้ดอะไรก็ได้เข้าไปทำงานตรงนั้น — จะทำอะไรก็ได้ ไม่จำกัดแค่เรื่องความปลอดภัย/policy
- **Guardrail** = จุดประสงค์เฉพาะอย่างหนึ่งที่มักเอา hook ไปใช้ทำ คือ "ตรวจสอบ input/output แล้วบล็อกถ้าละเมิดนโยบาย" (ตามที่งานวิจัยของ OpenAI นิยามไว้ตรงๆ ด้วย `tripwire_triggered`)

### หลักฐานจากโค้ดของเราเอง — ไม่ใช่ทุก hook ที่เป็น guardrail

ดู 4 ตัวอย่างที่เขียนไว้ใน `agent_loop_hooks.py`:

| Hook | เป็น guardrail ไหม | เหตุผล |
| --- | --- | --- |
| `guard_calculate_hook` | ✅ ใช่ | ตรวจสอบ input แล้ว deny/modify ตาม policy — ตรงนิยาม guardrail เป๊ะ |
| `redact_secrets_hook` | ✅ ใช่ | ตรวจสอบ output แล้ว sanitize ตาม policy |
| `require_number_on_stop_hook` | ✅ ใช่ | ตรวจสอบ output แล้ว block การจบ turn ตาม policy |
| **`audit_log_hook`** | ❌ **ไม่ใช่** | แค่เขียน log อย่างเดียว **ไม่เคย deny หรือ modify อะไรเลย** ไม่เกี่ยวกับ policy/ความปลอดภัยแม้แต่น้อย |

`audit_log_hook` คือหลักฐานชัดเจนว่า **hook ทำอะไรที่ไม่ใช่ guardrail ได้** (เช่น logging/observability เฉยๆ) — ถ้า hook เป็น subset ของ guardrail จริง `audit_log_hook` จะไม่สามารถเป็น hook ได้เลยเพราะมันไม่ใช่ guardrail แต่ในทางปฏิบัติมันคือ hook ที่ใช้งานได้จริงและ register เข้ากับ `HookManager` เดียวกับตัวอื่น

### ยืนยันจากเอกสารต้นทางด้วย

แม้แต่ **OpenAI Agents SDK เอง** ก็แยก 2 อย่างนี้เป็นคนละกลไก: `RunHooks`/`AgentHooks` (เอาไว้สังเกตการณ์ lifecycle เฉยๆ, ไม่มีอำนาจบล็อก) กับ `input_guardrail`/`output_guardrail` (เอาไว้ตรวจสอบ+บล็อกด้วย tripwire) — เป็น 2 mechanism คนละตัวใน SDK เดียวกัน แต่แนวคิดกว้างๆ คือ **guardrail = การเอากลไกแบบ hook ไปใช้ทำหน้าที่เฉพาะด้าน policy enforcement**

พูดสั้นๆ: **hook คือเครื่องมือ (ใช้ทำอะไรก็ได้ที่จุดนั้น), guardrail คือหนึ่งในงานที่เอาเครื่องมือนั้นไปทำ (เฉพาะงานตรวจสอบ+บล็อก)** — ในระบบของเรา `core/hooks.py` เป็น**เครื่องมือ** (hook engine) ส่วน 3 ใน 4 ฟังก์ชันตัวอย่างเป็นการเอาเครื่องมือนั้นไปสร้าง**guardrail**ขึ้นมาใช้งาน
