"""Small AST-based mutation operators used to generate extra seeded bugs.

Generated mutants are labelled by operator, not by the five hand-assigned bug
categories: a category label for a generated mutant must be assigned by a person
before it is used in a category-level analysis.
"""
from __future__ import annotations

import ast
import copy

CMP_SWAP = {ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Lt: ast.LtE, ast.LtE: ast.Lt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
BIN_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add}


def _compare_sites(tree):
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for j, op in enumerate(node.ops):
                if type(op) in CMP_SWAP:
                    sites.append((node, j))
    return sites


def _const_sites(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and type(n.value) is int]


def _binop_sites(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.BinOp) and type(n.op) in BIN_SWAP]


def generate_mutants(source: str) -> list[dict]:
    """Return [{"operator": str, "site": int, "code": str}] with unique, changed sources."""
    tree = ast.parse(source)
    base = ast.unparse(tree)
    seen = {base}
    out: list[dict] = []

    def add(operator, site, mutated_tree):
        ast.fix_missing_locations(mutated_tree)
        code = ast.unparse(mutated_tree) + "\n"
        if code.strip() in seen:
            return
        seen.add(code.strip())
        out.append({"operator": operator, "site": site, "code": code})

    for i, (_, j) in enumerate(_compare_sites(tree)):
        t = copy.deepcopy(tree)
        node, jj = _compare_sites(t)[i]
        node.ops[jj] = CMP_SWAP[type(node.ops[jj])]()
        add("compare_swap", i, t)

    for i in range(len(_const_sites(tree))):
        for delta, name in ((1, "const_plus1"), (-1, "const_minus1")):
            t = copy.deepcopy(tree)
            node = _const_sites(t)[i]
            node.value = node.value + delta
            add(name, i, t)

    for i in range(len(_binop_sites(tree))):
        t = copy.deepcopy(tree)
        node = _binop_sites(t)[i]
        node.op = BIN_SWAP[type(node.op)]()
        add("arith_swap", i, t)

    return out
