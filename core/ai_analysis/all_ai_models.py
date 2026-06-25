# core/all_ai_models.py
"""Aggregate import of all AI engine modules in the Antigravity project.

The project contains many *engine* classes that act as AI models (trend detection,
price analysis, probability estimation, etc.).  This module attempts to import
each engine safely and expose them via the ``AI_MODELS`` dictionary.

If an engine fails to import (e.g., due to syntax errors in the source), the
exception is caught and the engine is skipped – this prevents the whole package
from breaking while still giving developers a single place to see which AI
components are available.

Usage::

    from core.all_ai_models import AI_MODELS, load_all_engines
    print(AI_MODELS.keys())

The ``load_all_engines`` helper can be called at runtime to refresh the
registry after code changes.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper to import a module and retrieve the primary ``BaseEngine`` subclass.
# ---------------------------------------------------------------------------

def _import_engine(module_name: str) -> Any:
    """Import ``core.engines.<module_name>`` and return the first subclass of
    ``BaseEngine`` found in the module.

    Returns ``None`` if the import fails or no suitable class is present.
    """
    full_name = f"core.engines.{module_name}"
    try:
        mod = importlib.import_module(full_name)
    except Exception as exc:
        logger.warning(f"[AI Registry] Failed to import %s: %s", full_name, exc, exc_info=True)
        return None

    # Find a subclass of BaseEngine (skip the abstract BaseEngine itself)
    from core.orchestration.base_engine import BaseEngine
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if isinstance(obj, type) and issubclass(obj, BaseEngine) and obj is not BaseEngine:
            return obj
    logger.info(f"[AI Registry] No concrete BaseEngine subclass in %s", full_name)
    return None

# ---------------------------------------------------------------------------
# List of engine module filenames (without extension) present in the project.
# This list is generated from the directory listing of ``core/engines``.
# ---------------------------------------------------------------------------
_ENGINE_MODULES = [
    "analytical_utils",
    "anomaly_detector",
    "base_engine",
    "behavior_analyzer",
    "candle_pattern_analyzer",
    "confidence_framework",
    "conflict_analyzer",
    "context_synthesizer",
    "continuation_analyzer",
    "divergence_analyzer",
    "efficiency_analyzer",
    "engine_registry",
    "engine_setup",
    "explainability_engine",
    "liquidity_engine",
    "market_pressure_analyzer",
    "market_state_classifier",
    "mtf_engine",
    "noise_detector",
    "performance_tracker_signal",
    "persistence_analyzer",
    "price_action_handler",
    "probability_estimator",
    "regime_quality_scorer",
    "signal_quality_scorer",
    "strength_engine",
    "structure_engine",
    "transition_analyzer",
    "trap_detector",
    "trend_engine",
    "volatility_engine",
]

# ---------------------------------------------------------------------------
# Build the registry at import time.
# ---------------------------------------------------------------------------
AI_MODELS: Dict[str, Any] = {}
for _mod in _ENGINE_MODULES:
    cls = _import_engine(_mod)
    if cls is not None:
        AI_MODELS[_mod] = cls

# ---------------------------------------------------------------------------
# Public helper to (re)load all engines – useful after code changes.
# ---------------------------------------------------------------------------
def load_all_engines() -> Dict[str, Any]:
    """Reload every engine module and return a fresh ``AI_MODELS`` dictionary.

    This function clears the current registry, re‑imports each module and
    populates ``AI_MODELS`` again.  It can be called from a REPL or a management
    script when developers add new engines.
    """
    global AI_MODELS
    AI_MODELS = {}
    for module in _ENGINE_MODULES:
        cls = _import_engine(module)
        if cls:
            AI_MODELS[module] = cls
    return AI_MODELS

# ---------------------------------------------------------------------------
# Simple demo when the file is executed directly.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Discovered AI engine modules:")
    for name, cls in AI_MODELS.items():
        print(f" - {name}: {cls.__name__}")
    print(f"Total active AI models: {len(AI_MODELS)}")
