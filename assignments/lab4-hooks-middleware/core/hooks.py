"""core.hooks — Hook / Middleware engine ขั้นต่ำสำหรับ agent loop (ต่อยอด Lab 3, Layer 4)

แนวคิดยืมมาจาก 2 แหล่ง:
  1) Claude Code Hooks (PreToolUse / PostToolUse / Stop / UserPromptSubmit)
     -> "แทรกจังหวะ" ของ agent loop เพื่อ allow/deny/modify แบบ deterministic
     ก่อนหรือหลังแต่ละ step จริง ๆ ของ loop
     อ้างอิง: https://code.claude.com/docs/en/hooks
  2) OpenAI Agents SDK Guardrails (input_guardrail / output_guardrail / tripwire_triggered)
     -> ตรวจ input/output แล้ว "trip" เพื่อหยุดหรือปฏิเสธ ถ้าละเมิดนโยบาย
     อ้างอิง: https://openai.github.io/openai-agents-python/guardrails/

โมดูลนี้รวม 2 แนวคิดเป็น engine เดียวที่ minimal พอจะเสียบเข้า agent loop ของ Lab 3
ได้โดยไม่ต้องใช้ framework ใด ๆ: register(event, fn) -> run(event, payload) -> HookResult
(เทียบกับ Claude Code ที่ hook เป็น subprocess คุยกันผ่าน JSON บน stdin/stdout —
ที่นี่ hook เป็นแค่ Python function เพราะ agent loop ทั้งหมดรันใน process เดียว)

Event ที่รองรับ (map กับจังหวะใน agent loop ของ Lab 3):
  pre_llm   : ก่อนเรียก LLM แต่ละรอบ                  (~ on_llm_start ของ OpenAI SDK)
  post_llm  : หลัง LLM ตอบ ก่อนตัดสิน tool/end_turn    (~ on_llm_end ของ OpenAI SDK)
  pre_tool  : ก่อนเรียก tool จริง                      (~ PreToolUse ของ Claude Code)
  post_tool : หลังได้ผลลัพธ์ tool ก่อนป้อนกลับเข้า LLM (~ PostToolUse ของ Claude Code)
  stop      : ก่อนจบ turn (end_turn)                   (~ Stop hook ของ Claude Code)

Decision ของแต่ละ hook (คล้าย permissionDecision ของ Claude Code + tripwire ของ OpenAI):
  "allow"  : ผ่าน ไม่เปลี่ยนอะไร
  "deny"   : บล็อก step นี้ทันที พร้อมเหตุผล (short-circuit — hook ถัดไปไม่ถูกเรียก)
  "modify" : ผ่าน แต่แก้ไขข้อมูล (data) ก่อนส่งต่อให้ hook ถัดไป/agent loop
"""
from collections import defaultdict
from dataclasses import dataclass
import re


VALID_EVENTS = {"pre_llm", "post_llm", "pre_tool", "post_tool", "stop"}


@dataclass
class HookResult:
    decision: str = "allow"                 # allow | deny | modify
    reason: str | None = None               # เหตุผลเวลา deny (โชว์ log / ป้อนกลับ context)
    data: dict | None = None                # ข้อมูลที่แก้ไข เวลา decision == "modify"
    additional_context: str | None = None   # ข้อความแทรกกลับเข้า messages (system/user เสริม)


class HookManager:
    """รวม hook function หลายตัว รันตามลำดับที่ register ต่อ 1 event (คล้าย middleware chain)."""

    def __init__(self):
        self._hooks: dict[str, list[tuple]] = defaultdict(list)

    def register(self, event: str, fn, matcher: str | None = None):
        """ลงทะเบียน hook function สำหรับ event หนึ่ง.

        matcher : regex กรองด้วยชื่อ tool (มีผลเฉพาะ pre_tool/post_tool,
                  None = fire ทุกครั้ง — เทียบกับ matcher: "*" ของ Claude Code)
        """
        if event not in VALID_EVENTS:
            raise ValueError(f"unknown hook event: {event!r} (ต้องเป็นหนึ่งใน {VALID_EVENTS})")
        self._hooks[event].append((fn, matcher))

    def run(self, event: str, payload: dict, tool_name: str | None = None) -> HookResult:
        """รัน hook ทั้งหมดของ event นี้ตามลำดับที่ register.

        - เจอ "deny" ตัวแรก -> หยุดทันที คืนผลนั้นเลย (short-circuit เหมือน exit code 2 ของ Claude Code)
        - เจอ "modify" -> merge data เข้า payload ที่สะสมมา แล้วส่งต่อให้ hook ถัดไปเห็นค่าใหม่
        - ไม่มี hook ใด deny -> คืน decision="allow" พร้อม payload ล่าสุดใน .data
        """
        data = dict(payload)
        contexts: list[str] = []
        for fn, matcher in self._hooks[event]:
            if matcher and tool_name and not re.search(matcher, tool_name):
                continue
            result = fn(data)
            if result is None:
                continue
            if result.decision == "deny":
                return result
            if result.additional_context:
                contexts.append(result.additional_context)
            if result.decision == "modify" and result.data:
                data.update(result.data)
        return HookResult(decision="allow", data=data,
                           additional_context="\n".join(contexts) or None)
