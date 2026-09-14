# student-2026-AI-Harness-Engineering

Repo เก็บงาน/แบบฝึกหัดของหลักสูตร **Agentic AI Development with Python** ต่อยอดจาก
[Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph) — โครงสร้าง
โฟลเดอร์ `labs/` และชื่อไฟล์ **เหมือนกับ repo ต้นทางเป๊ะ** (`labs/core/`, `labs/lab3_agent_loop/`
ฯลฯ) เพื่อให้เอกสาร/สไลด์ที่อ้างอิง path และเลขบรรทัดของโค้ดยังใช้ได้ต่อเนื่อง

## รายการงาน

| Lab | โฟลเดอร์ | สรุป |
| --- | --- | --- |
| 3 | [labs/lab3_agent_loop](labs/lab3_agent_loop) | Agent loop แรกแบบ Pure Python (THINK → TOOL_USE → OBSERVE → END_TURN) — สำเนา byte-ต่อ-byte จาก [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph/tree/main/labs/lab3_agent_loop) |
| 4 | [labs/lab4_hooks_middleware](labs/lab4_hooks_middleware) | ต่อยอด Lab 3 ด้วย Hooks/Middleware engine — รีเสิร์ชและออกแบบจากเอกสารจริงของ Anthropic ([Claude Code Hooks](https://code.claude.com/docs/en/hooks)) และ OpenAI ([Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/)) |

## วิธีรัน (รันจาก root ของ repo เสมอ เพราะทุก Lab import ผ่าน `labs.core.*`)

```bash
pip install -r requirements.txt
cp .env.example .env   # ใส่ OPENROUTER_API_KEY จริงจาก https://openrouter.ai/keys

python labs/lab3_agent_loop/agent_loop.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab4_hooks_middleware/agent_loop_hooks.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
python labs/lab4_hooks_middleware/test_hooks.py   # เทสโดยไม่ต้องมี API key จริง
```

เข้าไปอ่าน README ของแต่ละ Lab เพื่อดูรายละเอียดเพิ่มเติม
