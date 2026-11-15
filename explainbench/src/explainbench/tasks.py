"""Load benchmark tasks from tasks/<task_id>/ directories.

Layout of one task directory:
    task.json        metadata + test cases (see below)
    reference.py     correct implementation
    docs.md          documentation notes shown in the "docs" condition
    mutants/*.py     hand-written seeded-bug variants (listed in task.json)
    alt_*.py         optional: other VALID solutions (must pass the full suite)
    cheat_*.py       optional: hard-coded solutions (must pass the demo suite, fail the full one)

task.json keys: id, title, entry, description, demo_count, tests, mutants.
Each test: {"args": [...], "expected": ...}; the first `demo_count` tests are the
short "demo" suite used as the baseline in the validation study.
Each mutant: {"id", "file", "category"}.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = [
    "off_by_one",
    "loop_condition",
    "base_case",
    "boundary_operator",
    "data_structure_update",
]


@dataclass
class Mutant:
    id: str
    category: str
    code: str
    origin: str = "handwritten"  # or "generated"
    operator: str = ""


@dataclass
class Task:
    id: str
    title: str
    entry: str
    description: str
    demo_count: int
    tests: list
    reference: str
    docs: str
    mutants: list = field(default_factory=list)
    alternatives: dict = field(default_factory=dict)
    cheats: dict = field(default_factory=dict)

    @property
    def demo_tests(self):
        return self.tests[: self.demo_count]


@dataclass
class Instance:
    """One buggy program that a model is asked to repair."""
    id: str
    task_id: str
    category: str
    code: str
    origin: str


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_task(path: Path) -> Task:
    meta = json.loads((path / "task.json").read_text(encoding="utf-8"))
    mutants = []
    for m in meta.get("mutants", []):
        if m["category"] not in CATEGORIES:
            raise ValueError(f"{meta['id']}: unknown category {m['category']}")
        mutants.append(Mutant(id=m["id"], category=m["category"],
                              code=(path / m["file"]).read_text(encoding="utf-8")))
    alts = {p.stem: p.read_text(encoding="utf-8") for p in sorted(path.glob("alt_*.py"))}
    cheats = {p.stem: p.read_text(encoding="utf-8") for p in sorted(path.glob("cheat_*.py"))}
    docs_path = path / "docs.md"
    return Task(
        id=meta["id"], title=meta["title"], entry=meta["entry"],
        description=meta["description"], demo_count=meta["demo_count"],
        tests=meta["tests"], reference=(path / "reference.py").read_text(encoding="utf-8"),
        docs=docs_path.read_text(encoding="utf-8") if docs_path.exists() else "",
        mutants=mutants, alternatives=alts, cheats=cheats,
    )


def load_tasks(root: Path | str = "tasks") -> list[Task]:
    root = Path(root)
    return [load_task(p.parent) for p in sorted(root.glob("*/task.json"))]


def bug_instances(tasks: list[Task]) -> list[Instance]:
    out = []
    for t in tasks:
        for m in t.mutants:
            out.append(Instance(id=f"{t.id}__{m.id}", task_id=t.id,
                                category=m.category, code=m.code, origin=m.origin))
    return out
