# Q&A Log — Entry 0009

**วันที่:** 2026-09-16
**Project:** student-2026-AI-Harness-Engineering

## คำถาม (verbatim)

https://github.com/aekanun2020/2026-Business-Analytics-AI/tree/codex/hq-hard-questions-fixes

อันนี้จะใช้ เป็น capstone project แต่ไม่ต้องการให้อยู่ในสไลด์เลย อย่างไรก็ตามขอทราบว่า ในนี้มีอะไรที่ตรงกับในสไลด์ PART 1, 2 ในโค้ดบรรทัดไหนบ้าง

## คำตอบ (verbatim)

สรุปการจับคู่แล้วครับ อ้างอิงจาก branch `codex/hq-hard-questions-fixes` ที่ HEAD `d46a1af` (clone มาอ่านในเครื่อง) โค้ดหลักมี 3 ไฟล์: `src/dfai_harness/runtime.py` (905 บรรทัด), `harnesses/bps39/hooks/bps.py` (252), `harnesses/bps39/hooks/verify.py` (58) บวก `run.py` และ policy JSON ใน `harnesses/bps39/policies/` เลขบรรทัดด้านล่างเป็นของไฟล์เหล่านี้ (ไม่ได้ใส่อะไรในสไลด์ตามที่สั่ง)

## PART 1 — Harness & Agent Loop

| สไลด์ | แนวคิด | ที่อยู่ในโค้ด capstone |
|---|---|---|
| p.7, 10, 11 | resp object, finish_reason, usage, endpoint กำหนด schema | `runtime.py` 36–54 `response_message()` ตรวจ envelope แบบ OpenAI: choices 41–43, finish_reason `length`/`stop`/`tool_calls` 46–49; เก็บ usage 315; endpoint ถูกล็อกเป็น OpenRouter 293; โมเดลเป็น Qwen แต่ schema เป็น OpenAI = ประเด็น p.11 ตรงตัว |
| p.13, 14, 18 | Harness = loop + tools + context + policy | `class Harness` 319; `run()` 797–852 เรียงเฟส preflight โมเดล 799 → เชื่อม MCP 801 → compile contract 811 → tool loop 813 → verifier 818 → synthesis 821 → publish 822–828 |
| p.19, 24, 25 | Agent Loop (Lab 3 บรรทัด 67/68/71/80/89) | `run_tool_loop()` 568–721: while 586 = วนรอบ, `self.model.complete` 603–606 = ถามโมเดล, `tool_calls` 611/616 = ขอใช้ tool ไหม, `self.mcp.call` 683 = เรียก tool จริง, ป้อนผลกลับเป็น role tool 686–696, ไม่ขอ tool = จบ 709–712 (โหมด legacy) หรือเรียก `FinalizeReport` 631–647 (โหมด bound-report) |
| p.20–23 | นิยาม tool + input schema (Lab 3 = static define) | **ต่างจาก Lab 3**: tool ไม่ได้เขียนตายตัว แต่ discover สดจาก MCP `initialize_mcp()` 429–443 (`list_tools` 437, กรองด้วย allowlist 436–438, เก็บ inputSchema 439–442) แล้วแปลงเป็น function schema `model_tools()` 481–493 ส่งไปกับ request 276–281 ส่วนที่ static คือ allowlist ใน `tool-permissions.json` 10–13 |
| p.26 | Budget และเงื่อนไขหยุด (Lab 3 มีแค่ max_steps) | งบ model call 18 (`model-policy.json` 19) บังคับที่ 267; งบ tool call 24 (`execution-budgets.json` 4) บังคับ 470, 663; งบ tool ถูกปฏิเสธ 8 (บรรทัด 5) บังคับ 551; reserved/compose calls 2 (บรรทัด 6, 13) → 586–592 บังคับให้เขียนคำตอบก่อนงบหมด = "ตรวจงบคงเหลือและเผื่อ output"; เพดานขนาด response 183–187, 307–308; usage บันทึกทุก call 315 และลง receipt 836–837 แต่**ยังไม่ใช้ token เป็นเกณฑ์หยุด** และ**ไม่มีตัวตรวจ tool ซ้ำ** เหมือนที่สไลด์บอกว่า Lab 3 ยังไม่มี |
| p.27 | Trace: run_id, step, tool, status, usage, ไม่บันทึก secret | evidence event `record_tool()` 445–467 (evidence_id, tool, arguments, result, sha256) → `evidence/*.json`; request/response ทุก call 294, 314; transcript 720/898; receipt 830–851 (model_calls, tool_calls, tool_counts, hook_rejections, hashes); failure.json ระบุ phase 881–893; API key อ่านจาก env เท่านั้น 421–422 และถูกถอดออกก่อนรัน verifier (`hook-policy.json` 18–23, runtime 735–737); "สำเร็จ ≠ ถูก" = receipt 846 `semantic_assessment: not_assessed` และ flag `admitted` 462 |
| p.28 | arguments ผิดรูปแบบ / error ที่โมเดลแก้ได้ vs ต้องหยุด | JSON พัง 666–671 และ schema ผิด 676 → `reject_tool_call()` 549–566 ส่ง repair_instruction กลับให้โมเดลแก้เอง (แก้ได้) vs `require()` 57–59 โยน HarnessError หยุดทันที เช่น 551, 717–719 (ต้องหยุด) |
| p.30–32 | Hooks ห่อ loop โดยไม่แก้ loop; จุด pre_tool/post_tool/stop | hook module โหลดแบบถอดได้ `load_hooks()` 403–409 จาก `hook-policy.json` 2; **pre_tool** runtime 473, 677 → `bps.py` 134–142; **post_tool** runtime 476, 684 → `bps.py` 145–157; **stop** = `completion_errors` runtime 639, 710–719 → `bps.py` 178–215 (บังคับโมเดลทำต่อถ้า binding ไม่ครบ เหมือน require_number_on_stop); เพิ่มจุดที่ Lab 4 ไม่มี: ตรวจ contract หลัง compile 533 → `bps.py` 103–131 และตรวจ synthesis 786 → `bps.py` 218–228 |
| p.33 | Anthropic = subprocess + exit code, OpenAI = exception | subprocess hook `run_external_hook()` 723–758 ตัดสินด้วย exit code 750 (`hook-policy.json` 25–27) = แบบ Anthropic; `require()` 57–59 โยน exception = แบบ tripwire |
| p.35 | HookResult allow/deny/modify | ที่นี่ hook คืน list ของ error (ว่าง = allow, มี = deny) ไม่มี modify; `post_tool_use` คืน `(admitted, errors)` 155–157 |
| p.36 | audit log, guard, redact, ลำดับ register | audit = `evidence/*.json` 466 + `hook-rejections/*.json` 557–560; guard = SQL AST guard `read_query_errors()` `bps.py` 26–64 (ห้าม DDL/DML 37, TOP ไม่มี ORDER BY 40–41, cross-db 53–54, remote server 57–58); redact ไม่มี hook ตรงตัว ใกล้สุดคือถอด key ออกจาก env ของ verifier 735–737 |
| p.37 | deterministic ผ่านโค้ด ไม่ผ่าน prompt | deny ที่ 677–682 เกิด**ก่อน** `self.mcp.call` 683 → query ต้องห้ามไม่ถึงฐานข้อมูลแน่นอน; ตรวจผลลัพธ์ตัดทอน `bps.py` 21–22 และ scientific notation 152–154 ก็เป็น regex ล้วน |

## PART 2 — Context Engineering และ Recovery

| สไลด์ | แนวคิด | ที่อยู่ในโค้ด capstone |
|---|---|---|
| p.3, 5 | history ยาวขึ้นทุก tool call และถูกส่งให้โมเดลทุกครั้ง | transcript เริ่ม 570–583, ทุกผล tool ถูก append 686–696, ทุก call ส่งทั้ง transcript 603–604; เก็บ field `reasoning` ไว้ใน context ด้วย 613–615 (`model-policy.json` 27–30) |
| p.6–10 | Compaction / Tool-result clearing | **ไม่มีทั้งสองอย่าง** ใช้วิธีอื่นแทน: คุมด้วยงบ 18 calls, ปฏิเสธผลลัพธ์ที่ถูกตัดทอน `bps.py` 21–22, prompt สั่งให้ query แบบสรุปแทนตารางดิบ (`skill.md` 3), เพดาน MCP response 4 MB (`tool-permissions.json` 14); โหมด bound-report ยังจงใจ**คงตารางดิบไว้ verbatim** `finalization_draft()` 237–252 ซึ่งตรงข้ามกับ clearing |
| p.11 | tool call กับ result ต้องเป็นคู่ | assistant พร้อม tool_calls 616–618 ตามด้วย tool message ต่อ call 686–696; แม้ call ถูกปฏิเสธก็ยังคืน tool message 561–566 เพื่อไม่ให้คู่ขาด |
| p.11 | summary schema (บังคับหัวข้อครบ) | แนวคิดเดียวกันแต่ใช้กับ contract: TaskContract schema `task-contract.schema.json` 1–78 (R1.. + grain/filters/required_outputs) บังคับผ่าน `response_format: json_schema` strict 503–506 ใน `compile_contract()` 495–547 |
| p.12 | pointer ไปยังหลักฐานแทนเนื้อหาทั้งก้อน | evidence ID `E0001…` สร้างที่ 454; โมเดลอ้าง E-id ใน draft/bindings และถูกตรวจ 210–212 ของ `bps.py`; synthesizer ต้องอ้าง id ชุดเดียวกันเป๊ะ 218–228 — pointer ถูกใช้เพื่อ citation ไม่ใช่เพื่อล้าง context |
| p.13 | External memory / persistence | ทุกอย่างลงดิสก์ใน run_dir: evidence 466, request/response 294/314, contract 543–547, transcript 720, receipt 851, usage 900 แต่**ไม่มี load กลับ**: run_dir ต้องเป็นโฟลเดอร์ใหม่เสมอ 360 (`exist_ok=False`) = persist เพื่อ audit ไม่ใช่เพื่อ resume |
| p.15 | Subagent, context isolation, return contract, ส่งสรุปพร้อม pointer | 4 บทบาทแยก context กันจริง: compiler 507–514, investigator 570–583 (ได้เฉพาะ contract + discovery evidence ที่ admitted), verifier เป็น subprocess ไม่มี API key 723–758 + `verify.py`, synthesizer 768–778 ได้แค่ contract + draft + verified_report **ไม่ได้ transcript ทั้งก้อน** = "ส่งสรุปพร้อม pointer กลับ" ตรงตัว; return contract = schema ของ `FinalizeReport` (`bps.py` 231–234: answer + bindings) และรูปแบบ draft JSON (`investigator.md` 2–4) |
| p.16–17 | Sandbox | เป็น sandbox ระดับนโยบาย ไม่ใช่ process/CPU แบบ Lab 6: ห้ามอ่านไฟล์ golden/evaluation ด้วย audit hook `run.py` 15–23 และ runtime 339–346; SQL read-only ผ่าน AST `bps.py` 26–64; allowlist tool 436–438; ห้าม redirect 130–132; ล็อก endpoint 293; verifier รันแยก process พร้อม timeout 745 (`hook-policy.json` 24) และถอด secret 735–737 |
| p.18 | Checkpoint & Recovery | **ไม่มี resume** (ไม่มี load_checkpoint); ที่มีคือ failure.json บันทึก phase ที่ล้ม 889 (รู้ตำแหน่งแต่ทำต่อไม่ได้) และ verifier อ่าน query ซ้ำเทียบ hash `verify.py` 17–24 พร้อมตรวจว่า server/database ยังเหมือนเดิม 38, 43 = "ตรวจว่าสภาพแวดล้อมยังตรงกับที่บันทึก"; งานเป็น read-only จึงไม่ต้องมี operation ID; open item ข้อ 4 ใน `RESULTS.md` 209–212 (repair call สำรอง) คือปัญหา recovery ที่ยังค้าง |
| p.19 | ขอบเขต SDK | repo นี้ไม่ใช้ SDK เลย: เรียก OpenRouter ด้วย urllib ดิบ 295–316, เขียน MCP client เอง 135–247 (JSON-RPC, SSE 145–163, pagination 218–230) |
| p.20 | ระบุส่วนที่ยังไม่ได้ implement | `evaluation/2026-09-15-full-suite-regrade/RESULTS.md` 188–240 เป็นตัวอย่างจริงของกิจกรรมนี้ (8 open items พร้อมเหตุผลว่าทำไมสำคัญ) |

## ข้อสังเกตรวม

- **ตรงกับ PART 1 เกือบทั้งหมด** โดยเฉพาะ loop, budget, trace, hooks และ deterministic policy — แต่ซับซ้อนกว่า Lab 3–4 ตรงที่มี 4 บทบาท, contract แบบ schema และ verifier แยก process
- **PART 2 ตรงเฉพาะครึ่งเดียว**: isolation/return contract (p.15), pointer ด้วย evidence ID (p.12), persistence เพื่อ audit (p.13) และ sandbox เชิงนโยบาย (p.16–17) มีจริง ส่วน compaction, clearing และ checkpoint/resume (p.6–10, 18) ไม่มี ซึ่งเป็นช่องว่างที่นำมาใช้เป็นโจทย์ capstone ได้ตรงกับที่สอนใน Lab 5 พอดี
- จุดที่ต่างจากสไลด์แบบน่าเอาไปอภิปราย: tool schema ไม่ static (discover จาก MCP), hook คืน error list แทน HookResult 3 ค่า, และ bound-report จงใจเก็บผลดิบ verbatim เพื่อ verifiability แทนที่จะล้าง
