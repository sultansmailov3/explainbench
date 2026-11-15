"""Model clients: a local Ollama client and a mock client for plumbing tests only."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request


class OllamaClient:
    """Minimal client for a local Ollama server (https://ollama.com), stdlib only."""

    def __init__(self, model: str, host: str = "http://localhost:11434", timeout: float = 600):
        self.model, self.host, self.timeout = model, host.rstrip("/"), timeout
        self.mock = False
        self._digest = None

    def _post(self, path, payload):
        req = urllib.request.Request(self.host + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode())

    @property
    def digest(self) -> str:
        """Model digest from /api/tags; record it so the exact weights are identifiable."""
        if self._digest is None:
            with urllib.request.urlopen(self.host + "/api/tags", timeout=30) as r:
                tags = json.loads(r.read().decode())["models"]
            for m in tags:
                if m["name"] == self.model or m.get("model") == self.model:
                    self._digest = m.get("digest", "unknown")
                    break
            else:
                raise RuntimeError(f"model {self.model!r} not found in Ollama; run `ollama pull`")
        return self._digest

    def generate(self, prompt: str, seed: int, temperature: float = 0.2,
                 max_tokens: int = 1024) -> dict:
        t0 = time.time()
        out = self._post("/api/generate", {
            "model": self.model, "prompt": prompt, "stream": False,
            "options": {"seed": seed, "temperature": temperature, "num_predict": max_tokens},
        })
        return {"text": out.get("response", ""), "latency_s": round(time.time() - t0, 3),
                "eval_count": out.get("eval_count")}


class MockClient:
    """Deterministic fake model. Its output is NEVER valid research data.

    `oracle` maps buggy code -> reference code; the mock returns the reference with a
    pseudo-random probability so that the pipeline produces both passes and failures.
    """

    def __init__(self, name="mock", oracle=None, p_fix=0.6):
        self.model, self.mock, self.oracle, self.p_fix = name, True, oracle or {}, p_fix
        self.digest = "mock"

    def generate(self, prompt, seed, temperature=0.2, max_tokens=1024):
        if "Return the complete corrected function" not in prompt:
            # explainer prompt (make_explanations): return plain text, no code block
            return {"text": "Mock explanation of the code.", "latency_s": 0.0, "eval_count": 0}
        m = re.search(r"```python\n(.*?)```", prompt, re.DOTALL)
        buggy = m.group(1) if m else ""
        h = int(hashlib.sha256(f"{prompt}|{seed}".encode()).hexdigest(), 16)
        fix = self.oracle.get(buggy)
        code = fix if (fix and (h % 100) < self.p_fix * 100) else buggy
        conf = round(((h >> 8) % 100) / 100, 2)
        return {"text": f"```python\n{code}```\nCONFIDENCE: {conf}", "latency_s": 0.0,
                "eval_count": 0}
