# student-2026-AI-Harness-Engineering

Repo เก็บงาน/แบบฝึกหัดของหลักสูตร **Agentic AI Development with Python** — แต่ละงานแยกโฟลเดอร์ใน
[`assignments/`](assignments) ต่อยอดกันเป็นลำดับ (Lab N ใช้โค้ดจาก Lab N-1 เป็นฐาน)

## รายการงาน

| Lab | โฟลเดอร์ | สรุป |
| --- | --- | --- |
| 3 | [assignments/lab3-agent-loop](assignments/lab3-agent-loop) | Agent loop แรกแบบ Pure Python (THINK → TOOL_USE → OBSERVE → END_TURN) คัดลอกจาก [Python-Agent-LangGraph](https://github.com/aekanun2020/Python-Agent-LangGraph) |
| 4 | [assignments/lab4-hooks-middleware](assignments/lab4-hooks-middleware) | ต่อยอด Lab 3 ด้วย Hooks/Middleware engine — รีเสิร์ชและออกแบบจากเอกสารจริงของ Anthropic ([Claude Code Hooks](https://code.claude.com/docs/en/hooks)) และ OpenAI ([Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/)) |

แต่ละโฟลเดอร์ self-contained (มี `requirements.txt`, `.env.example`, และไฟล์ dependency ที่จำเป็น
คัดลอกมาเอง) — เข้าไปอ่าน README ของแต่ละโฟลเดอร์เพื่อดูวิธีรัน
