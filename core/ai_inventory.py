# core/ai_inventory.py
"""Utility module to enumerate all AI engine classes in the Antigravity project.

It scans the ``core/engines`` package, imports each module, finds classes that inherit
from ``BaseEngine`` and returns a dictionary mapping module names to the concrete
engine class.

The module also provides a simple CLI entry point to print the total number of
AI engines and list their names.
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Tuple

# BaseEngine is the common abstract class for all engines.
import sys
import os
# Ensure the project root is in sys.path for relative imports
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# BaseEngine is the common abstract class for all engines.
from core.engines.base_engine import BaseEngine


def _discover_engine_modules() -> List[Tuple[str, str]]:
    """Discover all sub‑modules inside ``core.engines``.

    Returns a list of ``(module_name, file_path)`` tuples.
    """
    package_path = Path(__file__).parent / "engines"
    modules: List[Tuple[str, str]] = []
    for _, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if not is_pkg:
            modules.append((name, str(package_path / f"{name}.py")))
    return modules


def _load_engine_classes() -> Dict[str, type]:
    """Import each engine module and collect classes that subclass ``BaseEngine``.

    Returns:
        dict: ``{module_name: EngineClass}``
    """
    engine_classes: Dict[str, type] = {}
    for module_name, _ in _discover_engine_modules():
        full_name = f"core.engines.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception as e:
            # If a module fails to import we skip it but log the error for debugging.
            print(f"[WARN] Failed to import {full_name}: {e}")
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseEngine) and obj is not BaseEngine:
                engine_classes[module_name] = obj
                break  # Assume one primary engine per file.
    return engine_classes


def list_ai_models() -> Dict[str, str]:
    """Return a mapping of engine module name → class name.
    """
    classes = _load_engine_classes()
    return {mod: cls.__name__ for mod, cls in classes.items()}


def count_ai_models() -> int:
    """Return the total number of AI engine classes discovered.
    """
    return len(_load_engine_classes())


if __name__ == "__main__":
    models = list_ai_models()
    total = len(models)
    print(f"🔎 Discovered {total} AI engine(s) in the project:\n")
    for mod, cls_name in sorted(models.items()):
        print(f"- {mod}: {cls_name}")
