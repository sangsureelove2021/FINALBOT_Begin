"""
Local AI Brain Package for FINALBOT (Athena Sniper Bot)
Provides In-Memory AI Decision Engines:
- Model A: Amazon Chronos Time-Series Foundation Model
- Model B: LightGBM High-Speed Price Action Classifier
- DualBrain: Coordinator for Mode A, Mode B, and Mode AB
"""

from .chronos_engine import ChronosEngine
from .lightgbm_engine import LightGBMEngine
from .dual_brain import DualBrainCoordinator

__all__ = ["ChronosEngine", "LightGBMEngine", "DualBrainCoordinator"]
