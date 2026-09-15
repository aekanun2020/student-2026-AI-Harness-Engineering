# student-2026-AI-Harness-Engineering

Repo เก็บงาน/แบบฝึกหัดของหลักสูตร **Agentic AI Development with Python** ต่อยอดจาก repo ต้นทางของ
หลักสูตร (Python-Agent-LangGraph) — โครงสร้างโฟลเดอร์ `labs/` และชื่อไฟล์ **เหมือนกับ repo ต้นทางเป๊ะ**
(`labs/core/`, `labs/lab3_agent_loop/` ฯลฯ) เพื่อให้เอกสาร/สไลด์ที่อ้างอิง path และเลขบรรทัดของโค้ดยังใช้ได้
ต่อเนื่อง — **ผู้เรียนทำทุกอย่างใน repo นี้ที่เดียว ไม่ต้องเปิด repo ต้นทาง** (ลิงก์สำหรับผู้ตรวจอยู่ท้ายหน้า)

## รายการงาน

| Lab | โฟลเดอร์ | สรุป |
| --- | --- | --- |
| 1 | [labs/lab1_setup](labs/lab1_setup) | ตรวจสภาพแวดล้อม — ดัดแปลงจาก Lab 1 ของ repo ต้นทาง โดยตัดส่วนตรวจ MCP MSSQL Server ออก (ไม่มี server ให้ต่อใน repo นี้) เหลือแค่ตรวจ OpenRouter (LLM) — ไฟล์นี้**ไม่ byte-identical** กับต้นฉบับ (ต่างจาก Lab 3 ที่ต้องคงไว้เพราะสไลด์อ้างอิงเลขบรรทัด) |
| 2 | [labs/lab2_llm](labs/lab2_llm) | เรียก LLM ครั้งแรก + เทียบหลายโมเดลบน OpenRouter — ดัดแปลงจาก Lab 2 ของ repo ต้นทาง โดยเพิ่มการแสดง**ค่าใช้จ่ายจริงเป็นเงิน** (`usage.cost` ที่ OpenRouter หักจริง) ของทุกครั้งที่เรียก |
| 3 | [labs/lab3_agent_loop](labs/lab3_agent_loop) | Agent loop แรกแบบ Pure Python (THINK → TOOL_USE → OBSERVE → END_TURN) — สำเนา byte-ต่อ-byte จาก Lab 3 ของ repo ต้นทาง |
| 3a | [labs/lab3a_self_correction](labs/lab3a_self_correction) | เติม self-correction ให้ Agent Loop ด้วยการแก้ `SYSTEM` prompt เพียงจุดเดียว (ไม่ใช้ hook) — ต่อยอดจาก Lab 3 โดยไม่แก้ไฟล์ Lab 3 เลย พร้อมโชว์ข้อจำกัดที่ prompt-only แก้ไม่ได้ ซึ่งเป็นเหตุผลที่ต้องมี Lab 4 |
| 4 | [labs/lab4_hooks_middleware](labs/lab4_hooks_middleware) | ต่อยอด Lab 3 ด้วย Hooks/Middleware engine — รีเสิร์ชและออกแบบจากเอกสารจริงของ Anthropic ([Claude Code Hooks](https://code.claude.com/docs/en/hooks)) และ OpenAI ([Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/)) |
| 5 | [labs/lab5_memory_checkpoint](labs/lab5_memory_checkpoint) | Memory (Compaction ดัดแปลงจาก `lab7_memory/agent_memory.py` ของ repo ต้นทาง) + Checkpoint (external memory ที่รอดข้าม process จริง ต่างจากต้นฉบับที่เป็นแค่ RAM) — ทดสอบจริงทั้ง compaction, cross-process memory, และ resume หลัง `SIGKILL` กลาง turn |
| 6 | [labs/lab6_sandbox](labs/lab6_sandbox) | เติม Sandbox (แยก `eval()` ไปรันใน subprocess + `RLIMIT_CPU`) — ทดสอบจริงด้วยการบังคับ resource exhaustion (`9999**99999999`) แล้วยืนยันว่า agent loop หลักไม่กระทบ พร้อมบันทึกบั๊กจริงเรื่อง `RLIMIT_AS` ใช้ไม่ได้บน macOS |

## สำหรับผู้เรียนที่เคยใช้แค่หน้าแชท (ChatGPT / Claude) — อ่านตรงนี้ก่อน

### terminal คืออะไร

ทุก Lab รันจาก **terminal** (หน้าต่างพิมพ์คำสั่งเป็นข้อความ ไม่มีปุ่มให้กด):
- **Mac:** กด ⌘ + Space พิมพ์ `Terminal` แล้ว Enter
- **Windows:** กดปุ่ม Windows พิมพ์ `PowerShell` แล้ว Enter

ตลอดหลักสูตรนี้ใช้คำสั่งหลักแค่ 3 ตัว: `cd` (เข้าโฟลเดอร์), `python3` (รันโปรแกรม — **Windows พิมพ์ `python`**
แทน เพราะ `python3` บน Windows มักไม่มีหรือเด้งไปเปิด Microsoft Store), `pip` (ติดตั้งไลบรารี)
ทุกคำสั่งพิมพ์แล้วกด Enter — ถ้าเห็นข้อความ error สีแดงยาวๆ ไม่ต้องตกใจ อ่านบรรทัดสุดท้ายก่อน มักบอกสาเหตุ

### ศัพท์ที่จะเจอตั้งแต่บรรทัดแรก

| คำ | ความหมายในหลักสูตรนี้ |
| --- | --- |
| **repo** | โฟลเดอร์โปรเจกต์ที่เก็บโค้ดทั้งหมด ฝากไว้บน GitHub — "root ของ repo" = โฟลเดอร์บนสุดที่มีไฟล์ README.md นี้อยู่ |
| **system prompt** | ข้อความตั้งต้นที่บอกบุคลิก/กติกาให้ AI ก่อนเริ่มคุย — สิ่งเดียวกับ Custom Instructions ที่คุณเคยตั้งในหน้าแชท |
| **tool** | ปุ่มที่ AI กดเองได้ เช่น เครื่องคิดเลข, นาฬิกา — เหมือนตอน ChatGPT ขึ้นว่า "กำลังค้นหาเว็บ…" นั่นคือมันกำลังใช้ tool |
| **agent loop** | AI ทำงานหลายขั้นต่อเนื่องเอง (คิด → ใช้ tool → ดูผล → คิดต่อ) จนเสร็จ แทนที่จะตอบทีเดียวแล้วจบ |
| **token** | ชิ้นส่วนของคำ (ภาษาไทย 1 คำอาจเป็นหลาย token) — ค่าใช้จ่ายและขีดจำกัดความยาวของ AI นับเป็น token ไม่ใช่ตัวอักษร |
| **API key** | รหัสสำหรับให้โปรแกรมเรียกใช้ AI แทนเรา (เหมือน login ให้โค้ด) — **ห้ามแชร์ให้ใคร** |
| **process** | โปรแกรมที่รันอยู่ 1 ครั้ง — ปิดแล้วเปิดใหม่ = process ใหม่ ความจำที่อยู่ใน RAM หายหมด |
| **argument** | ค่าที่ส่งให้ tool หรือส่งต่อท้ายคำสั่ง (ไม่ใช่ "การเถียง") |
| **deterministic** | ทำเหมือนเดิม 100% ทุกครั้ง ไม่ขึ้นกับการสุ่มของ AI |
| **byte-identical** | ไฟล์เหมือนต้นฉบับทุกตัวอักษร — ใช้กับไฟล์ที่สไลด์ของหลักสูตรอ้างอิงเลขบรรทัดไว้ จึงห้ามแก้ |

### อ่านผลลัพธ์บนหน้าจอยังไง

ทุก Lab ตั้งแต่ Lab 3 พิมพ์ผลออกมาแบบนี้:

| บรรทัดที่เห็น | แปลว่า |
| --- | --- |
| `[user] …` | คำถามที่คุณส่งเข้าไป |
| `[step N] THINK -> ขอเรียก K tool` | รอบคิดที่ N — AI ตัดสินใจว่าจะใช้ tool K ตัว |
| `TOOL_USE calculate({...}) -> 60` | โปรแกรมเรียก tool ให้ AI แล้ว ได้ผลลัพธ์ `60` กลับมา |
| `[step N] END_TURN` | AI พอใจแล้ว ไม่ขอใช้ tool อีก กำลังจะตอบ |
| `[answer] …` | คำตอบสุดท้าย — สิ่งที่คุณจะเห็นถ้านี่เป็นหน้าแชท |
| `HOOK …` (Lab 4) | ระบบตรวจ (hook) ดักไว้ — บล็อกหรือแก้ไขบางอย่างก่อน AI ทำต่อ |
| `[resume] …` / `[compaction] …` (Lab 5) | โหลดความจำเก่ากลับมา / สรุปบทสนทนาเก่าเพื่อประหยัดที่ |

### ค่าใช้จ่าย

ทุกครั้งที่รัน = เรียก AI จริงผ่าน **OpenRouter** ซึ่ง**คิดเงินตามการใช้จริง** (ไม่ใช่เหมาจ่ายรายเดือนแบบ
ChatGPT Plus) — ต้องสมัครและเติมเงินก่อน ส่วนใหญ่ครั้งละไม่กี่สตางค์ถึงไม่กี่บาท ยกเว้น
`compare_models.py` (Lab 2) ที่เรียก 3 โมเดลในครั้งเดียว และ Lab 5 ที่รันวนหลายรอบ —
**Lab 2 แสดงบรรทัด `[cost]` เงินที่ถูกหักจริงของทุกครั้งที่เรียก** ทำ Lab 2 ให้จบก่อนจะได้รู้ว่าแต่ละครั้งเสียเท่าไร

## วิธีรัน (รันจาก root ของ repo เสมอ เพราะทุก Lab import ผ่าน `labs.core.*`)

> ทำ [Lab 1](labs/lab1_setup/README.md) ให้จบก่อน (ติดตั้ง Python, สร้าง venv, ใส่ API key) —
> และ **ทุกครั้งที่เปิด terminal ใหม่** ต้อง `cd` เข้า root ของ repo แล้ว `source .venv/bin/activate`
> (Windows: `.venv\Scripts\activate`) ก่อนเสมอ — คำสั่งด้านล่างเขียนแบบ Mac/Linux, Windows ใช้ `python`
> แทน `python3` และ `copy` แทน `cp`

```bash
pip install -r requirements.txt
cp .env.example .env   # ใส่ OPENROUTER_API_KEY จริงจาก https://openrouter.ai/keys (ดูวิธีขอคีย์ใน Lab 1)
                       # Windows: copy .env.example .env

# ข้อความใน "..." ต่อท้ายคำสั่ง = คำถามที่จะส่งให้ AI — เปลี่ยนเป็นอะไรก็ได้
python labs/lab1_setup/check_env.py            # ตรวจ OpenRouter (LLM) เท่านั้น — ควรผ่าน
python labs/lab2_llm/first_llm.py "อธิบาย Agent Loop ใน 1 ประโยค"
python labs/lab3_agent_loop/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab3a_self_correction/agent_loop.py "กรุณาคำนวณนิพจน์นี้เป๊ะๆ ตามที่เขียน อย่าปรับรูปแบบ: 5,000+3,000"
python labs/lab4_hooks_middleware/agent_loop_hooks.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab4_hooks_middleware/test_hooks.py   # เทสโดยไม่ต้องมี API key จริง
python labs/lab5_memory_checkpoint/agent_loop.py "แนะนำตัวหน่อยว่าคุณจำอะไรได้บ้าง" my-thread
python labs/lab6_sandbox/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
```

> **⚠️ ข้อความตกค้างจาก repo ต้นทางที่จะเจอใน README ของ Lab 3** (ไฟล์นี้เป็นสำเนา byte-identical
> จึงแก้ไม่ได้ เพราะสไลด์ของหลักสูตรอ้างอิงเลขบรรทัดไว้):
> - เห็น `conda activate agentic-ai` → ให้ใช้ `source .venv/bin/activate` แทน (Windows: `.venv\Scripts\activate`)
> - เห็น `cd Python-Agent-LangGraph` → ให้ใช้ `cd student-2026-AI-Harness-Engineering` แทน
> - เห็นการอ้างถึง **Lab 7-9**, **LangGraph**, หรือโฟลเดอร์ `screenshots/` → ของเหล่านั้นอยู่ใน repo
>   ต้นทางเท่านั้น ไม่มีใน repo นี้ ข้ามได้ ไม่ใช่คุณทำอะไรพลาด

เข้าไปอ่าน README ของแต่ละ Lab เพื่อดูรายละเอียดเพิ่มเติม — และทุก Lab มี `QUESTIONS.md` เป็นแบบฝึกหัด
ที่ติดป้ายไว้ว่าข้อไหน 🟢 แค่พิมพ์คำสั่ง · 🟡 ต้องเปิดแก้ไฟล์ · 🔴 ต้องเขียน Python

---

> **ส่วนที่เหลือของหน้านี้สำหรับผู้สอน/ผู้ตรวจ** — ผู้เรียนข้ามไปอ่าน README ของแต่ละ Lab ได้เลย
> ไม่ต้องเข้าใจตารางด้านล่างก่อนเริ่มทำ Lab

## สถาปัตยกรรม Agent: App → Agent → LLM + 8 Layers

> อ้างอิงมาจาก root README.md ของ [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph#สถาปัตยกรรม-agent-app--agent--llm--8-layers)
> — **นี่คือลิงก์เดียวไป repo ต้นทางในเอกสารชุดนี้** เก็บไว้สำหรับผู้ตรวจที่ต้องการยืนยันว่าไฟล์ที่ระบุ
> byte-identical ตรงกับต้นฉบับจริง (ผู้เรียนไม่ต้องเปิด — repo นั้นมี 9 Lab, ใช้ conda และต่อ MCP server
> ซึ่งต่างจาก repo นี้ เปิดไปอาจสับสน)
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
L1/L2 ประเมินใหม่จากไฟล์ที่ดัดแปลงแล้ว (L1 ตัด `check_mcp()` ออก, L2 เพิ่มการแสดงค่าใช้จ่าย — ทั้งคู่
ไม่ byte-identical กับต้นฉบับอีกต่อไป แต่การเพิ่ม/ตัดนั้นไม่กระทบว่า Lab แตะ layer ไหน ค่าจึงเท่าต้นฉบับ)

| Layer | Lab 1 | Lab 2 | Lab 3 | Lab 3a | Lab 4 | Lab 5 | Lab 6 |
| --- | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 1. Instructions / Bootstrap | | | | ◐ | ◐ | | |
| 2. Memory | | | | | | ● | |
| 3. Tools + Skills | | | ● | ● | ● | ● | ● |
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
