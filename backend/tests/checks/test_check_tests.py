"""Every registered check has at least one fire and one no-fire test."""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from app.core.checks import registry

TESTS_DIR = Path(__file__).parent


def _calls() -> dict[str, set[str]]:
    """check_id -> {"assert_fires", "assert_no_fire"} used in tests/checks/."""
    used: dict[str, set[str]] = defaultdict(set)
    for path in TESTS_DIR.glob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in {"assert_fires", "assert_no_fire"} and node.args
                    and isinstance(node.args[0], ast.Constant)):
                used[node.args[0].value].add(node.func.id)
    return used


def test_every_registered_check_has_fire_and_no_fire_tests():
    registry.load_implementations()
    used = _calls()
    missing = {cid: sorted({"assert_fires", "assert_no_fire"} - used[cid])
               for cid in registry.CHECKS if used[cid] != {"assert_fires", "assert_no_fire"}}
    assert not missing, f"checks without fire/no-fire tests: {missing}"
