"""
Scripted test สำหรับ agent_loop_hooks.py — ไม่ต้องมี OPENROUTER_API_KEY จริง
เพราะ monkeypatch core.llm.chat ให้คืนคำตอบตามสคริปต์ที่กำหนดไว้ล่วงหน้า
เพื่อยืนยันว่า hook ทั้ง 4 ตัวทำงานถูกจุดจริงในวง run_agent (ไม่ใช่แค่ unit test แยก)

รัน:  cd assignments/lab4-hooks-middleware && python test_hooks.py
"""
import os, json

import core.llm as llm_module


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = FakeFunction(name, arguments)

    def model_dump(self):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResp:
    def __init__(self, message):
        self.choices = [FakeChoice(message)]


# ---- สคริปต์คำตอบจำลอง 3 รอบ ----
call_count = {"n": 0}

def fake_chat(messages, model=None, tools=None, **kwargs):
    call_count["n"] += 1
    n = call_count["n"]
    if n == 1:
        # รอบ 1: ขอเรียก 3 tools -> get_time (ปกติ), calculate มีช่องว่างเกิน (ต้อง modify),
        # calculate นิพจน์ยาวเกิน 40 ตัว (ต้อง deny)
        return FakeResp(FakeMessage(content=None, tool_calls=[
            FakeToolCall("call_1", "get_time", "{}"),
            FakeToolCall("call_2", "calculate", json.dumps({"expression": " 15*4 "})),
            FakeToolCall("call_3", "calculate", json.dumps({"expression": "1+" * 25 + "1"})),
        ]))
    if n == 2:
        # รอบ 2: LLM ตอบแบบไม่มีตัวเลขเลย ทั้งที่คำถามมีการคำนวณ -> stop hook ต้อง deny 1 ครั้ง
        return FakeResp(FakeMessage(content="ไม่ทราบครับ ขอโทษที", tool_calls=None))
    # รอบ 3: ตอบใหม่แบบมีตัวเลข -> stop hook ต้อง allow -> END_TURN
    return FakeResp(FakeMessage(content="ตอนนี้เวลาก็ไม่รู้ แต่ 15*4 เท่ากับ 60 ครับ", tool_calls=None))


llm_module.chat = fake_chat

import agent_loop_hooks as aloop

# ล้าง audit log เก่า (ถ้ามี) ให้เทสอ่านง่าย
if os.path.exists(aloop.AUDIT_LOG_PATH):
    os.remove(aloop.AUDIT_LOG_PATH)

# แทรก fake dispatch ที่ tool_3 (จำลองว่ามี tool หลุด secret ออกมา) — เพิ่มเข้าไปทดสอบ redact
_orig_dispatch = aloop.dispatch
def fake_dispatch(name, args):
    if args.get("expression") == "SECRET_TEST":
        return "here is the key: sk-ABCDEFGHIJ1234567890"
    return _orig_dispatch(name, args)
aloop.dispatch = fake_dispatch

print("=" * 70)
print("TEST RUN 1: full scripted run_agent (deny / modify / stop-retry)")
print("=" * 70)
answer = aloop.run_agent("ตอนนี้กี่โมง แล้ว 15*4 เท่ากับเท่าไร", aloop.build_default_hooks())
assert answer is not None and "60" in answer, f"unexpected final answer: {answer}"
print("\n[PASS] run_agent ได้คำตอบสุดท้ายที่มีตัวเลขถูกต้อง:", answer)

print("\n" + "=" * 70)
print("TEST RUN 2: redact_secrets_hook ผ่าน post_tool")
print("=" * 70)
call_count["n"] = 0
def fake_chat_secret(messages, model=None, tools=None, **kwargs):
    call_count["n"] += 1
    if call_count["n"] == 1:
        return FakeResp(FakeMessage(content=None, tool_calls=[
            FakeToolCall("call_s1", "calculate", json.dumps({"expression": "SECRET_TEST"})),
        ]))
    return FakeResp(FakeMessage(content="จบแล้วครับ ไม่มีตัวเลข", tool_calls=None))
llm_module.chat = fake_chat_secret

aloop.run_agent("ขอ secret หน่อย", aloop.build_default_hooks())

with open(aloop.AUDIT_LOG_PATH, encoding="utf-8") as f:
    log_lines = f.readlines()

secret_leaked = any("sk-ABCDEFGHIJ1234567890" in line for line in log_lines)
redacted_present = any("[REDACTED]" in line for line in log_lines)
assert not secret_leaked, "FAIL: ข้อความ secret ดิบหลุดเข้า audit log!"
assert redacted_present, "FAIL: ไม่เห็น [REDACTED] ใน audit log เลย"
print("[PASS] audit log ไม่มี secret ดิบหลุดเข้าไป, มีการ redact ก่อน log จริง")

print("\n" + "=" * 70)
print("TEST RUN 3: guard_calculate_hook deny เมื่อ dispatch จริงไม่ควรถูกเรียก")
print("=" * 70)
dispatch_calls = []
def counting_dispatch(name, args):
    dispatch_calls.append((name, args))
    return _orig_dispatch(name, args)
aloop.dispatch = counting_dispatch

call_count["n"] = 0
def fake_chat_deny(messages, model=None, tools=None, **kwargs):
    call_count["n"] += 1
    if call_count["n"] == 1:
        return FakeResp(FakeMessage(content=None, tool_calls=[
            FakeToolCall("call_d1", "calculate", json.dumps({"expression": "1+" * 25 + "1"})),
        ]))
    return FakeResp(FakeMessage(content="โอเคครับ", tool_calls=None))
llm_module.chat = fake_chat_deny

aloop.run_agent("นิพจน์ยาวมาก", aloop.build_default_hooks())
assert len(dispatch_calls) == 0, f"FAIL: dispatch ถูกเรียกทั้งที่ควรถูก deny: {dispatch_calls}"
print("[PASS] guard_calculate_hook บล็อกก่อนถึง dispatch จริง — dispatch ไม่ถูกเรียกเลย")

print("\nALL TESTS PASSED")
