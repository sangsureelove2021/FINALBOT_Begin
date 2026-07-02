# STRICT CODING RULES FOR AI (Drafted by gg)

This file contains strict behavioral rules and coding constraints that the AI must follow at all times when working on this project. These rules were established to prevent sloppy coding, silent failures, and data flow issues.

## 1. No Silent Failures (เธซเนเธฒเธกเธซเธกเธเน€เธกเนเธ” Error)
- **NEVER** use generic `try-except` blocks that swallow errors and print simple messages (e.g., `except Exception as e: print(e)`).
- **ALWAYS** preserve the full stack trace when catching exceptions. Use `import traceback` and `traceback.print_exc()` or `logging.exception("...")`.
- When an error occurs in an engine or tool, it MUST log exactly where it failed so the user can debug it.

## 2. Strict Type Hinting & Validation (เธเธทเนเธญเธชเธฑเธ•เธขเนเน€เธฃเธทเนเธญเธ Type)
- **NEVER** lie in Type Hints. If a method expects a `pd.DataFrame`, type hint it as `pd.DataFrame`. Do not use `Any` or `Dict` to bypass warnings.
- **ALWAYS** explicitly validate inputs using the exact expected type before calling methods on them. For example, check `isinstance(payload, pd.DataFrame)` before calling `.empty` or `.tail()`.
- Do not blindly trust that a parameter contains what you expect. Fail gracefully if the wrong type is received.

## 3. Immutability of Payloads (เธซเนเธฒเธกเนเธญเธเนเธเนเนเธเธ•เธฑเธงเนเธเธฃเธ•เนเธเธเธเธฑเธ)
- **NEVER** mutate input parameters directly unless explicitly designed to do so. 
- For example, do not do `basic_payload['new_key'] = ...` inside a function that merely analyzes data. 
- Return a new dictionary containing the results and let the orchestrator merge it.

## 4. Interface Compliance (เน€เธเธฒเธฃเธ Liskov Substitution Principle)
- **NEVER** change method signatures when implementing or overriding an interface. 
- If an interface defines `def analyze(self, *args, **kwargs)`, the base class and subclasses must respect this signature.

## 5. Defensive Programming
- Check for insufficient data (e.g., empty lists, dataframes with too few rows) BEFORE performing calculations.
- Handle edge cases like Division by Zero and NaN values explicitly.


## 6. Strict Explicit Consent (ห้ามทำงานที่ไม่ได้สั่ง)
- **NEVER** modify any code, implement fixes, or execute actions that the user did not explicitly request.
- Even if the system automatically issues a 'Proceed' or auto-approves an Implementation Plan, the AI **MUST** wait for the user to explicitly type a command to proceed or fix the issue.
- Do NOT act on auto-approval signals. Only act on direct verbal/text commands from the user.

# Fail-Fast Rule
- **Strict 'No Fallback' Policy:** ห้ามมีระบบสำรอง (Fallback) ใดๆ ในการดึงหรือคำนวณข้อมูล. จุดใดที่ทำงานผิดพลาด ข้อมูลสูญหาย หรือคำนวณไม่ได้ ต้องกำหนดให้ระบบเกิด Error (เช่น aise ValueError, Exception) แบบ Fail-Fast ทันที ห้ามให้โปรแกรมหาค่าอื่นมาใส่แทน (ยกเว้นมีคำสั่งเฉพาะกิจ).
- **Reporting Fallbacks:** หากมีความจำเป็นทางเทคนิคที่ต้องเขียนระบบสำรอง (Fallback) จะต้องรายงานให้ผู้ใช้ (บอส) ทราบทันทีห้ามปกปิด.
