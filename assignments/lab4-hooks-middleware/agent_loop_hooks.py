"""
Lab 4 — ต่อยอด Lab 3 (agent_loop.py) ด้วย Hooks / Middleware (Layer 4)
อ้างอิงแนวคิด: Claude Code Hooks (PreToolUse/PostToolUse/Stop) + OpenAI Agents SDK
Guardrails (tripwire) — รายละเอียด engine อยู่ที่ core/hooks.py

Lab 3 เดิม (agent_loop.py) คือ THINK -> TOOL_USE -> OBSERVE -> END_TURN แบบเปลือย (Layer 5 ล้วน)
ไฟล์นี้แทรก hook 5 จังหวะเข้าไปในวงเดิม โดย "ไม่แก้ agent_loop.py เลยสักบรรทัด"
(import TOOLS/SYSTEM/dispatch ของเดิมมาใช้ซ้ำ) แล้วห่อ loop ใหม่รอบนอก:

    pre_llm -> [LLM] -> post_llm -> (tool_calls?)
        -> pre_tool -> [dispatch จริง] -> post_tool -> วนกลับ pre_llm
        -> (ไม่มี tool_calls) -> stop -> END_TURN

hook ตัวอย่าง 4 ตัวในไฟล์นี้ตั้งใจให้ตรงกับช่องว่างที่ root README ของ repo ระบุไว้ว่า
Layer 4 (Hooks) และ Layer 8 (Safety: audit trail) ยังไม่มีระบบจริงใน Lab ไหนเลย:

  1) audit_log_hook          : เขียน audit trail ทุก pre_tool/post_tool/stop ลง agent_audit.log
  2) guard_calculate_hook    : PreToolUse บน `calculate` — deny ถ้านิพจน์ยาวผิดปกติ,
                                modify (trim ช่องว่าง) ถ้าจำเป็น — defense-in-depth เพิ่มจาก
                                whitelist ที่ agent_loop.py มีอยู่แล้ว
  3) redact_secrets_hook     : PostToolUse — redact ข้อความหน้าตาเหมือน API key (เช่น "sk-...")
                                ก่อนป้อนผล tool กลับเข้า context ของ LLM (ต้องรันก่อน audit เสมอ
                                ไม่งั้น secret จะหลุดเข้าไปอยู่ใน audit log แทน)
  4) require_number_on_stop_hook : Stop hook — ถ้าคำถามหน้าตาเหมือนโจทย์คำนวณแต่คำตอบ
                                ไม่มีตัวเลขเลย ให้ deny การจบ turn 1 ครั้ง แล้วบังคับให้ LLM ตอบใหม่
                                (เทียบกับ Stop hook ของ Claude Code ที่ "บล็อกไม่ให้จบ" ได้)

รัน:  cd assignments/lab4-hooks-middleware && python agent_loop_hooks.py "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
"""
import sys, os, json, re, datetime

from core import llm
from core.hooks import HookManager, HookResult
from agent_loop import TOOLS, SYSTEM, dispatch

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "agent_audit.log")


# ---- (1) audit trail — เทียบ Layer 8 Safety: "audit trail" ----
def audit_log_hook(payload: dict) -> HookResult:
    entry = {"ts": datetime.datetime.now().isoformat(), **payload}
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return HookResult(decision="allow")


# ---- (2) PreToolUse guard เฉพาะ tool "calculate" (matcher กรองให้) ----
def guard_calculate_hook(payload: dict) -> HookResult:
    expr = payload.get("args", {}).get("expression", "")
    if len(expr) > 40:
        return HookResult(decision="deny",
                           reason=f"นิพจน์ยาวเกินไป ({len(expr)} ตัวอักษร) — บล็อกเพื่อความปลอดภัย")
    stripped = expr.strip()
    if stripped != expr:
        return HookResult(decision="modify",
                           data={"args": {**payload["args"], "expression": stripped}})
    return HookResult(decision="allow")


# ---- (3) PostToolUse — redact ข้อความหน้าตาเหมือน API key ก่อนเข้า context ----
SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{10,}")


def redact_secrets_hook(payload: dict) -> HookResult:
    result = payload.get("result", "")
    if SECRET_PATTERN.search(result):
        redacted = SECRET_PATTERN.sub("[REDACTED]", result)
        return HookResult(decision="modify", data={"result": redacted},
                           additional_context="[hook] พบ pattern คล้าย secret ใน tool output — redact แล้ว")
    return HookResult(decision="allow")


# ---- (4) Stop hook — บังคับให้ตอบมีตัวเลข ถ้าคำถามดูเหมือนโจทย์คำนวณ ----
def require_number_on_stop_hook(payload: dict) -> HookResult:
    question = payload.get("question", "")
    answer = payload.get("answer") or ""
    looks_like_calc = bool(re.search(r"\d+\s*[*+/x-]\s*\d+", question))
    has_digit = bool(re.search(r"\d", answer))
    if looks_like_calc and not has_digit:
        return HookResult(decision="deny",
                           reason="คำถามดูเหมือนมีการคำนวณ แต่คำตอบไม่มีตัวเลขเลย",
                           additional_context="กรุณาตรวจสอบและตอบให้มีผลลัพธ์ตัวเลขที่คำนวณได้ด้วย")
    return HookResult(decision="allow")


def build_default_hooks() -> HookManager:
    hooks = HookManager()
    # pre_tool: log ทุกความพยายามเรียก tool ก่อนเสมอ (แม้จะถูก guard deny ทีหลัง)
    hooks.register("pre_tool", audit_log_hook)
    hooks.register("pre_tool", guard_calculate_hook, matcher="calculate")
    # post_tool: ต้อง redact ก่อน แล้วค่อย log — ห้าม secret หลุดเข้า audit log
    hooks.register("post_tool", redact_secrets_hook)
    hooks.register("post_tool", audit_log_hook)
    # stop: ตรวจคำตอบก่อน แล้วค่อย log ผลตัดสินสุดท้าย
    hooks.register("stop", require_number_on_stop_hook)
    hooks.register("stop", audit_log_hook)
    return hooks


# ---- (5) Agent loop เดิมของ Lab 3 ห่อด้วย hook ทั้ง 5 จังหวะ ----
def run_agent(question: str, hooks: HookManager, max_steps: int = 6):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    stop_retry_used = False   # กันไม่ให้ stop hook บังคับวนซ้ำไม่รู้จบ

    for step in range(1, max_steps + 1):
        pre_llm = hooks.run("pre_llm", {"messages": messages, "step": step})
        if pre_llm.additional_context:
            messages.append({"role": "system", "content": pre_llm.additional_context})

        resp = llm.chat(messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        hooks.run("post_llm", {"message": msg.content, "step": step})

        if msg.tool_calls:
            print(f"[step {step}] THINK -> ขอเรียก {len(msg.tool_calls)} tool")
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")

                pre = hooks.run("pre_tool", {"tool": call.function.name, "args": args, "step": step},
                                 tool_name=call.function.name)
                if pre.decision == "deny":
                    print(f"           HOOK pre_tool DENY {call.function.name}: {pre.reason}")
                    result = f"[hook denied] {pre.reason}"
                else:
                    args = pre.data.get("args", args) if pre.data else args
                    result = dispatch(call.function.name, args)

                    post = hooks.run("post_tool",
                                      {"tool": call.function.name, "args": args, "result": result, "step": step},
                                      tool_name=call.function.name)
                    if post.decision == "deny":
                        result = f"[hook denied] {post.reason}"
                    elif post.data and "result" in post.data:
                        result = post.data["result"]
                    if post.additional_context:
                        print(f"           HOOK post_tool: {post.additional_context}")

                print(f"           TOOL_USE {call.function.name}({args}) -> {result}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            continue   # วนกลับให้ LLM อ่านผล tool

        # ไม่มี tool_calls = ผู้ช่วยขอจบ turn -> เช็ค stop hook ก่อน
        stop = hooks.run("stop", {"question": question, "answer": msg.content, "step": step})
        if stop.decision == "deny" and not stop_retry_used:
            stop_retry_used = True
            print(f"[step {step}] HOOK stop DENY: {stop.reason}")
            messages.append({"role": "assistant", "content": msg.content or ""})
            messages.append({"role": "user", "content": stop.additional_context or "กรุณาตอบใหม่"})
            continue

        print(f"[step {step}] END_TURN")
        print("-" * 60)
        print(f"[answer] {msg.content}")
        return msg.content

    print("[!] ถึงขีดจำกัดจำนวนรอบแล้ว")
    return None


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร"
    print(f"[user] {q}")
    run_agent(q, build_default_hooks())
