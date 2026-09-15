# student-2026-AI-Harness-Engineering

Repo เก็บงาน/แบบฝึกหัดของหลักสูตร **Agentic AI Development with Python** ต่อยอดจาก
[Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph) — โครงสร้าง
โฟลเดอร์ `labs/` และชื่อไฟล์ **เหมือนกับ repo ต้นทางเป๊ะ** (`labs/core/`, `labs/lab3_agent_loop/`
ฯลฯ) เพื่อให้เอกสาร/สไลด์ที่อ้างอิง path และเลขบรรทัดของโค้ดยังใช้ได้ต่อเนื่อง

## รายการงาน

| Lab | โฟลเดอร์ | สรุป |
| --- | --- | --- |
| 1 | [labs/lab1_setup](labs/lab1_setup) | ตรวจสภาพแวดล้อม — ดัดแปลงจาก [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph/tree/main/labs/lab1_setup) โดยตัดส่วนตรวจ MCP MSSQL Server ออก (ไม่มี server ให้ต่อใน repo นี้) เหลือแค่ตรวจ OpenRouter (LLM) — ไฟล์นี้**ไม่ byte-identical** กับต้นฉบับ (ต่างจาก Lab 3 ที่ต้องคงไว้เพราะสไลด์อ้างอิงเลขบรรทัด) |
| 2 | [labs/lab2_llm](labs/lab2_llm) | เรียก LLM ครั้งแรก + เทียบหลายโมเดลบน OpenRouter — สำเนา byte-ต่อ-byte จาก [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph/tree/main/labs/lab2_llm) |
| 3 | [labs/lab3_agent_loop](labs/lab3_agent_loop) | Agent loop แรกแบบ Pure Python (THINK → TOOL_USE → OBSERVE → END_TURN) — สำเนา byte-ต่อ-byte จาก [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph/tree/main/labs/lab3_agent_loop) |
| 3a | [labs/lab3a_self_correction](labs/lab3a_self_correction) | เติม self-correction ให้ Agent Loop ด้วยการแก้ `SYSTEM` prompt เพียงจุดเดียว (ไม่ใช้ hook) — ต่อยอดจาก Lab 3 โดยไม่แก้ไฟล์ Lab 3 เลย พร้อมโชว์ข้อจำกัดที่ prompt-only แก้ไม่ได้ ซึ่งเป็นเหตุผลที่ต้องมี Lab 4 |
| 4 | [labs/lab4_hooks_middleware](labs/lab4_hooks_middleware) | ต่อยอด Lab 3 ด้วย Hooks/Middleware engine — รีเสิร์ชและออกแบบจากเอกสารจริงของ Anthropic ([Claude Code Hooks](https://code.claude.com/docs/en/hooks)) และ OpenAI ([Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/)) |
| 5 | [labs/lab5_memory_checkpoint](labs/lab5_memory_checkpoint) | Memory (Compaction + Notes ดัดแปลงจาก [lab7_memory/agent_memory.py](https://github.com/aekanun2020/Python-Agent-LangGraph/blob/main/labs/lab7_memory/agent_memory.py)) + Checkpoint (external memory ที่รอดข้าม process จริง ต่างจากต้นฉบับที่เป็นแค่ RAM) — ทดสอบจริงทั้ง compaction, cross-process memory, และ resume หลัง `SIGKILL` กลาง turn |
| 6 | [labs/lab6_sandbox](labs/lab6_sandbox) | เติม Sandbox (แยก `eval()` ไปรันใน subprocess + `RLIMIT_CPU`) — ทดสอบจริงด้วยการบังคับ resource exhaustion (`9999**99999999`) แล้วยืนยันว่า agent loop หลักไม่กระทบ พร้อมบันทึกบั๊กจริงเรื่อง `RLIMIT_AS` ใช้ไม่ได้บน macOS |

## วิธีรัน (รันจาก root ของ repo เสมอ เพราะทุก Lab import ผ่าน `labs.core.*`)

```bash
pip install -r requirements.txt
cp .env.example .env   # ใส่ OPENROUTER_API_KEY จริงจาก https://openrouter.ai/keys

python labs/lab1_setup/check_env.py            # ตรวจ OpenRouter (LLM) เท่านั้น — ควรผ่าน
python labs/lab2_llm/first_llm.py "อธิบาย Agent Loop ใน 1 ประโยค"
python labs/lab3_agent_loop/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab3a_self_correction/agent_loop.py "กรุณาคำนวณนิพจน์นี้เป๊ะๆ ตามที่เขียน อย่าปรับรูปแบบ: 5,000+3,000"
python labs/lab4_hooks_middleware/agent_loop_hooks.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab4_hooks_middleware/test_hooks.py   # เทสโดยไม่ต้องมี API key จริง
python labs/lab5_memory_checkpoint/agent_loop.py "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง" my-thread
python labs/lab6_sandbox/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
```

เข้าไปอ่าน README ของแต่ละ Lab เพื่อดูรายละเอียดเพิ่มเติม

---

## สถาปัตยกรรม Agent: App → Agent → LLM + 8 Layers

> อ้างอิงมาจาก root README.md ของ [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph#สถาปัตยกรรม-agent-app--agent--llm--8-layers)
> ใส่ไว้ที่นี่ด้วยเพื่อให้ลิงก์ "ตำแหน่งใน 8 Layer ของ repo" ที่ README ของแต่ละ Lab อ้างถึง
> (เช่น [Lab 3](labs/lab3_agent_loop/README.md)) resolve ได้จริงในบริบท repo นี้

เพื่อให้เข้าใจว่าแต่ละ Lab "กำลังสร้างชิ้นส่วนไหนของ Agent" หลักสูตรนี้ยึดภาพสถาปัตยกรรมเดียวกันทั้งหมด
หัวใจคือ **LLM ทำหน้าที่ reasoning/decision** แต่สิ่งที่ทำให้มันเป็น "Agent" และประกอบขึ้นเป็น "App" จริง
คือ layer ที่ห่อรอบ LLM ต่างหาก

```
┌──────────────────────────────────────────────┐
│                    APP                         │
│  + UI, Auth, DB, Business Logic, Infra         │
│  ┌──────────────────────────────────────────┐ │
│  │              AGENT                        │ │
│  │  + Memory, Tools, Hooks, State            │ │
│  │   ┌────────────────────────────────┐      │ │
│  │   │           LLM                  │      │ │
│  │   │  (reasoning / decision)        │      │ │
│  │   └────────────────────────────────┘      │ │
│  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

กางภาพข้างบนออกเป็น **8 layer** ของ Agent harness — แต่ละ layer มีคำอธิบายและ **แหล่งอ้างอิงต้นทาง**
(origin paper / เอกสารทางการของบริษัทเทคโนโลยี) ที่เข้าดูได้จริง:

| # | Layer | ทำหน้าที่อะไร | แหล่งอ้างอิงต้นทาง (เปิดดูได้จริง) |
| :-: | --- | --- | --- |
| 1 | **Instructions / Bootstrap** | คำสั่งระบบ/บุคลิก/ขอบเขตที่โหลดตอนเริ่ม (เช่น `SOUL.md`, `AGENTS.md`) — กำหนดพฤติกรรมก่อนโมเดลเห็นงาน | Anthropic — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 2 | **Memory** | ความจำสั้น/ยาว/procedural + compaction + note-taking | CoALA: [Cognitive Architectures for Language Agents](https://arxiv.org/abs/2309.02427) (Sumers et al., 2024) · Anthropic — [context engineering: compaction & note-taking](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 3 | **Tools + Skills** | ความสามารถภายนอก (MCP) + procedure ที่นำกลับมาใช้ซ้ำ (Skills) โหลดตามความจำเป็น | Anthropic — [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) · [Agent Skills (Claude Docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) |
| 4 | **Hooks** | callback ที่ดักจังหวะ lifecycle ของ agent (เช่น `PreToolUse`/`PostToolUse`/`Stop`) เพื่อ log/บล็อก/แทรก context แบบ deterministic | Anthropic — [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks) |
| 5 | **Reasoning Loop (Agent Loop)** | วงคิด-ทำ-สังเกต (reason → act → observe → วน) แกนของ agent | ReAct: [Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) (Yao et al., ICLR 2023) |
| 6 | **Sandbox + Execution** | ที่รันโค้ด/คำสั่งที่โมเดลสร้างขึ้นแบบแยกขอบเขต (Docker/VM/Computer Use) | Anthropic — [Computer use tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool) · [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) |
| 7 | **Gateway + Scheduler** | ช่องทางเข้า-ออกประตูเดียว (HTTP/Telegram/Slack) + ตัวกระตุ้นตามเวลา/เหตุการณ์ (Cron/Webhook) | **Gateway:** AWS — [Amazon Bedrock AgentCore Gateway: single secure entry point for agents](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html) · วิชาการ: Nowaczyk — [Architectures for Building Agentic AI](https://arxiv.org/abs/2512.09458) (แนวคิด Execution Gateway) · **Scheduler:** Dust — [Introducing Triggers (Schedule + Webhook)](https://dust.tt/blog/introducing-triggers-your-agents-working-while-you-sleep) |
| 8 | **Safety Layer** | permission gating, audit trail, self-check + containment ที่ environment layer | Anthropic — [How we contain Claude across products](https://www.anthropic.com/engineering/how-we-contain-claude) |

> หมายเหตุ: CoALA (layer 2), ReAct (layer 5) และ Architectures for Building Agentic AI (layer 7) เป็น academic paper · MCP/Skills/Hooks/Computer Use/Containment เป็นเอกสารทางการของ Anthropic · AgentCore Gateway (layer 7) เป็นเอกสาร AWS · Triggers (layer 7) เป็นเอกสาร Dust

### แต่ละ Lab ใน repo นี้อยู่ตรงไหนของ 8 Layer นี้

สัญลักษณ์: ● = เป็นแกนหลักของ Lab นั้น · ◐ = แตะ/มีบางส่วน · (ว่าง) = ไม่มี — ตารางนี้เป็นของ repo นี้
เอง (Lab 1/2/3/3a/4/5/6) ไม่ใช่ตาราง 9 lab ของ repo ต้นทาง เพราะ repo นี้ยังไม่มี Lab 7-9 · คอลัมน์
L1/L2 คงค่าตามที่ root README ของ repo ต้นทางให้ไว้ (ไฟล์เหมือนกันเป๊ะ ไม่ได้ประเมินใหม่)

| Layer | Lab 1 | Lab 2 | Lab 3 | Lab 3a | Lab 4 | Lab 5 | Lab 6 |
| --- | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 1. Instructions / Bootstrap | | | | ◐ | ◐ | | |
| 2. Memory | | | | | | ● | |
| 3. Tools + Skills | ◐ | | ● | ● | ● | ● | ● |
| 4. Hooks | | | | | ● | | |
| 5. Reasoning Loop (Agent Loop) | | | ● | ● | ● | ● | ● |
| 6. Sandbox + Execution | | | ◐* | ◐* | ◐* | | ● |
| 7. Gateway + Scheduler | | | | | | | |
| 8. Safety Layer | | | ◐* | ◐* | ◐ | | ◐ |

> `◐*` = มีร่องรอย/พฤติกรรมคล้าย แต่ยังไม่ใช่ระบบจริงตามนิยาม layer (เช่น `calculate()`'s whitelist
> eval เป็นการป้องกันแบบพื้นฐาน ไม่ใช่ sandbox จริงแบบ Docker/VM) · Lab 3a แตะ Layer 1 เพิ่มจาก Lab 3
> เพราะแก้ `SYSTEM` prompt (Instructions) เพื่อสั่ง self-correction
>
> **Layer 3 (Tools):** "Tools" ในตารางนี้หมายถึง function ใดๆ ที่ LLM เรียกใช้ได้จริง ไม่ว่าจะผ่าน
> MCP หรือเป็น local function ก็นับ — ทุก Lab มี `get_time`/`calculate` เป็น function-calling tool
> ที่โมเดลเรียกได้จริงจึงเป็น `●` เต็ม (ไม่รวมส่วน "Skills" ซึ่งยังไม่มี Lab ไหนทำ)
>
> **Lab 5** เป็น `●` จริงใน Layer 2 (checkpoint ทำให้ memory รอดข้าม process จริง ต่างจาก
> `lab7_memory` ต้นฉบับที่เป็นแค่ RAM) — ดู [Lab 5](labs/lab5_memory_checkpoint/README.md)
>
> **Lab 6** เป็น `●` จริงใน Layer 6 (subprocess + `RLIMIT_CPU` แยก process จริง ไม่ใช่แค่ whitelist
> ตัวอักษร) ทดสอบแล้วด้วยการบังคับ resource exhaustion จริง — แต่**ยังไม่ครอบคลุม filesystem/network
> isolation** เหมือน Docker ตัวเต็ม (ดูตารางเทียบ framework ใน [Lab 6](labs/lab6_sandbox/README.md))
>
> **ช่องว่างที่ยังไม่มี Lab ไหนครอบคลุมเลย:** Layer 1 (เป็น core ล้วน, ยังไม่มี Lab ไหนทำเป็นแกนหลัก),
> Layer 7 (Gateway/Scheduler), Layer 8 (Safety Layer เต็มรูปแบบ — มีแค่ audit trail บางส่วนจาก Lab 4),
> filesystem/network sandboxing (ดูช่องว่างของ Lab 6 ด้านบน), tool-result clearing และ idempotent
> retry (ยังไม่มี Lab ไหนทำ — ดูรายละเอียดใน [Lab 5 QUESTIONS.md](labs/lab5_memory_checkpoint/QUESTIONS.md))
