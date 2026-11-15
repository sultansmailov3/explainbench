"""Run candidate Python code against test cases in a separate process.

WARNING: this is process isolation with resource limits, NOT a security sandbox.
Model-generated code must be executed inside a container or VM you do not mind
losing (see README, "Safety").
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile

MARK = "@@EXPLAINBENCH_RESULT@@"

_CHILD = r'''
import sys, io, json, copy, signal
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
except Exception:
    pass
real_stdout = sys.stdout
req = json.load(sys.stdin)
sys.setrecursionlimit(1000)

def _alarm(signum, frame):
    raise TimeoutError("test case timed out")

if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _alarm)

def emit(obj):
    real_stdout.write("@@EXPLAINBENCH_RESULT@@" + json.dumps(obj) + "\n")
    real_stdout.flush()

sys.stdout = io.StringIO()
ns = {"__name__": "candidate"}
try:
    exec(compile(req["code"], "<candidate>", "exec"), ns)
    fn = ns[req["entry"]]
except BaseException as e:
    emit({"load_error": type(e).__name__ + ": " + str(e)[:200]})
    sys.exit(0)

results = []
for t in req["tests"]:
    try:
        if hasattr(signal, "setitimer"):
            signal.setitimer(signal.ITIMER_REAL, req["per_test_timeout"])
        obs = fn(*copy.deepcopy(t["args"]))
        if hasattr(signal, "setitimer"):
            signal.setitimer(signal.ITIMER_REAL, 0)
        exp = t["expected"]
        ok = (obs == exp) and (type(obs) is type(exp))
        results.append({"ok": bool(ok), "observed": repr(obs)[:200], "error": None})
    except BaseException as e:
        if hasattr(signal, "setitimer"):
            signal.setitimer(signal.ITIMER_REAL, 0)
        results.append({"ok": False, "observed": None,
                        "error": type(e).__name__ + ": " + str(e)[:200]})
emit({"results": results})
'''


def run_tests(code: str, entry: str, tests: list[dict], timeout: float = 20.0,
              per_test_timeout: float = 2.0) -> dict:
    """Return {"load_error": str|None, "timeout": bool, "results": [ {ok, observed, error} ]}."""
    req = json.dumps({"code": code, "entry": entry, "tests": tests,
                      "per_test_timeout": per_test_timeout})
    blank = [{"ok": False, "observed": None, "error": None} for _ in tests]
    with tempfile.TemporaryDirectory() as cwd:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", _CHILD],
                input=req, capture_output=True, text=True, timeout=timeout,
                cwd=cwd, env={"PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            for r in blank:
                r["error"] = "TimeoutExpired: whole-run timeout"
            return {"load_error": None, "timeout": True, "results": blank}
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith(MARK):
            payload = json.loads(line[len(MARK):])
    if payload is None:
        for r in blank:
            r["error"] = "NoResult: child produced no result (crash or exit)"
        return {"load_error": None, "timeout": False, "results": blank}
    if "load_error" in payload:
        for r in blank:
            r["error"] = "LoadError: " + payload["load_error"]
        return {"load_error": payload["load_error"], "timeout": False, "results": blank}
    return {"load_error": None, "timeout": False, "results": payload["results"]}


def all_passed(outcome: dict) -> bool:
    return bool(outcome["results"]) and all(r["ok"] for r in outcome["results"])
