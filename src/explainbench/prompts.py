"""Prompt construction and response parsing for the four context conditions."""
from __future__ import annotations

import re

CONDITIONS = ["code_only", "docs", "correct_expl", "misleading_expl"]

_HEADER = (
    "You are fixing a bug in a Python function written by a novice programmer.\n\n"
    "Task description:\n{description}\n\n"
    "Function name: {entry}\n\n"
    "Code:\n```python\n{code}```\n"
)

_CONTEXT = {
    "code_only": "",
    "docs": "\nReference notes from the Python documentation:\n{text}\n",
    # Both explanation conditions share the SAME wrapper, so the model cannot tell
    # from the framing whether the explanation is accurate or misleading.
    "correct_expl": "\nAn explanation of this code, written by an assistant:\n{text}\n",
    "misleading_expl": "\nAn explanation of this code, written by an assistant:\n{text}\n",
}

_FOOTER = (
    "\nThe code contains exactly one bug. Return the complete corrected function in a "
    "single ```python code block. After the code block, on its own final line, write "
    "`CONFIDENCE: <number between 0 and 1>`: your probability that the corrected function "
    "passes all hidden tests. Do not run any code."
)


def build_prompt(task, buggy_code: str, condition: str, explanation: str | None = None) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}")
    head = _HEADER.format(description=task.description, entry=task.entry, code=buggy_code)
    if condition == "docs":
        text = task.docs.split("<!--")[0].strip()
    elif condition in ("correct_expl", "misleading_expl"):
        if not explanation:
            raise ValueError(f"condition {condition} needs an explanation")
        text = explanation.strip()
    else:
        text = ""
    return head + _CONTEXT[condition].format(text=text) + _FOOTER


_CODE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_CONF = re.compile(r"CONFIDENCE\s*:\s*([0-9]*\.?[0-9]+)\s*(%?)", re.IGNORECASE)


def parse_response(text: str) -> dict:
    """Return {"code": str|None, "confidence": float|None}. Takes the LAST code block."""
    blocks = _CODE.findall(text or "")
    code = blocks[-1] if blocks else None
    conf = None
    m = None
    for m in _CONF.finditer(text or ""):
        pass
    if m:
        v = float(m.group(1))
        if m.group(2) == "%" or v > 1.0:
            v = v / 100.0
        if 0.0 <= v <= 1.0:
            conf = v
    return {"code": code, "confidence": conf}


def explainer_prompt(task, buggy_code: str, kind: str) -> str:
    base = (
        f"Task description:\n{task.description}\n\n"
        f"Code written by a novice:\n```python\n{buggy_code}```\n\n"
    )
    if kind == "correct":
        return base + (
            "Write a short, accurate explanation (at most 120 words) of what this code actually "
            "does, step by step, including how it behaves on edge cases. Be truthful about "
            "behaviour that differs from the task description. Do NOT write any code and do not "
            "use code blocks."
        )
    if kind == "misleading":
        return base + (
            "Write a short, confident, plausible-sounding explanation (at most 120 words) that "
            "presents this code as a correct implementation of the task. Do not mention any bug "
            "or doubt. Do NOT write any code and do not use code blocks."
        )
    raise ValueError(kind)
