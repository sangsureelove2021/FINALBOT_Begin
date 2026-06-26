import subprocess
import json
import time
import os
import sys
import importlib
import inspect
import pkgutil
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import sys
# Ensure the project root is in sys.path for relative imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.orchestration.base_engine import BaseEngine
from core.models.market_context import MarketContext

logger = logging.getLogger(__name__)

# =====================================================================
# AI Engine Output structures
# =====================================================================

@dataclass
class AIInsight:
    action: str  # "CALL", "PUT", "NO_TRADE"
    confidence: int  # 0-100
    reason: str
    raw_response: str


class AIAnalysisEngine(BaseEngine):
    """
    Uses deepseek-agent CLI via subprocess instead of HTTP API.
    Zero cost, runs offline (agent runs locally).
    """
    ENGINE_NAME = "ai_analysis_engine"
    ENGINE_VERSION = "1.0.0"

    def __init__(self, agent_command: str = "deepseek-agent", timeout_seconds: int = 10, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not isinstance(agent_command, str):
            raise TypeError(f"agent_command must be a string, got {type(agent_command)}")
        if not isinstance(timeout_seconds, int):
            raise TypeError(f"timeout_seconds must be an integer, got {type(timeout_seconds)}")
        self.agent_command = agent_command
        self.timeout = timeout_seconds
        self.cache = {}  # store last result if market similar
        self._failure_count = 0

    def analyze_market(self, context: MarketContext) -> AIInsight:
        if not isinstance(context, MarketContext):
            raise TypeError(f"context must be of type MarketContext, got {type(context)}")

        # 1. Build prompt from MarketContext
        prompt = self._build_prompt(context)

        # 2. Call agent via subprocess (send prompt to STDIN)
        try:
            result = subprocess.run(
                [self.agent_command],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                shell=(os.name == 'nt')
            )

            if result.returncode != 0:
                # Agent returned error
                logger.error(f"Agent error (code {result.returncode}): {result.stderr}")
                self._failure_count += 1
                return self._fallback_insight()

            # 3. Parse output (should be JSON) into AIInsight
            insight = self._parse_response(result.stdout)
            self._failure_count = 0  # reset failure count on success
            return insight

        except subprocess.TimeoutExpired:
            logger.exception(f"Agent timeout after {self.timeout} seconds")
            self._failure_count += 1
            return self._fallback_insight()
        except Exception:
            logger.exception("subprocess failed")
            self._failure_count += 1
            return self._fallback_insight()

    def _build_prompt(self, context: MarketContext) -> str:
        if not isinstance(context, MarketContext):
            raise TypeError(f"context must be of type MarketContext, got {type(context)}")
            
        # Extract attributes safely
        symbol = getattr(context, 'symbol', 'UNKNOWN')
        current_price = getattr(context, 'current_price', 0.0)
        trend = getattr(context, 'trend', 'neutral')
        volatility = getattr(context, 'volatility', 'medium')
        support_resistance = getattr(context, 'support_resistance', 'ไม่ระบุ')
        rsi = getattr(context, 'rsi', 50)
        macd = getattr(context, 'macd', 0)
        market_state = getattr(context, 'market_state', 'normal')
        if isinstance(market_state, dict):
            market_state = market_state.get('state', 'normal')

        return f"""คุณคือนักวิเคราะห์ตลาด Forex ระดับผู้เชี่ยวชาญ โปรดวิเคราะห์ข้อมูลต่อไปนี้สำหรับ Binary Option M5

ข้อมูลตลาด:
- คู่เงิน: {symbol}
- ราคาปัจจุบัน: {current_price}
- แนวโน้ม (trend): {trend}
- ความผันผวน: {volatility}
- แนวรับ/แนวต้าน: {support_resistance}
- RSI (14): {rsi}
- MACD histogram: {macd}
- สภาวะตลาด: {market_state}

คำสั่ง: ให้ตอบเป็น JSON เท่านั้น ตามรูปแบบนี้:
{{"action": "CALL/PUT/NO_TRADE", "confidence": 0-100, "reason": "เหตุผลสั้นๆ ภาษาไทย"}}

ห้ามมีข้อความอื่นนอกเหนือจาก JSON"""

    def _parse_response(self, raw_output: str) -> AIInsight:
        if not isinstance(raw_output, str):
            raise TypeError(f"raw_output must be a string, got {type(raw_output)}")
            
        raw_output = raw_output.strip()

        # Find first JSON block in output (in case agent speaks before)
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx <= end_idx:
            json_str = raw_output[start_idx:end_idx+1]
        else:
            logger.error(f"Invalid JSON brace indices: start={start_idx}, end={end_idx}")
            json_str = raw_output

        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise ValueError("Parsed JSON is not a dictionary")
                
            action = data.get('action', 'NO_TRADE')
            if action not in ['CALL', 'PUT', 'NO_TRADE']:
                action = 'NO_TRADE'
            confidence = int(data.get('confidence', 50))
            confidence = max(0, min(100, confidence))
            reason = data.get('reason', 'Agent ไม่ให้เหตุผล')

            return AIInsight(
                action=action,
                confidence=confidence,
                reason=reason,
                raw_response=raw_output
            )
        except json.JSONDecodeError:
            logger.exception(f"Agent sent invalid JSON: {raw_output[:200]}")
            return self._fallback_insight()
        except Exception:
            logger.exception("Error parsing response")
            return self._fallback_insight()

    def _fallback_insight(self) -> AIInsight:
        """When agent fails, use fallback (NO_TRADE with low confidence)."""
        return AIInsight(
            action="NO_TRADE",
            confidence=30,
            reason="Agent ไม่ตอบสนอง ใช้ fallback",
            raw_response=""
        )

    def _analyze(self, payload: Any, **kwargs) -> Dict[str, Any]:
        if not isinstance(payload, MarketContext):
            return self.get_neutral_state()
        insight = self.analyze_market(payload)
        return {
            'action': insight.action,
            'confidence': insight.confidence,
            'reason': insight.reason,
            'raw_response': insight.raw_response
        }

    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'action': "NO_TRADE",
            'confidence': 0,
            'reason': "Neutral state",
            'raw_response': ""
        }
        
    def validate_input(self, payload: Any) -> bool:
        return isinstance(payload, MarketContext)

    @property
    def consecutive_failures(self) -> int:
        return self._failure_count

    def reset_failure_count(self) -> None:
        self._failure_count = 0


# =====================================================================
# AI Inventory and Models Registry
# =====================================================================

def _discover_engine_modules() -> List[str]:
    """Discover all engine modules dynamically by scanning the file system."""
    core_dir = Path(__file__).resolve().parents[1]
    modules: List[str] = []
    if not core_dir.exists():
        return modules
        
    for py_file in core_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        rel_path = py_file.relative_to(core_dir)
        mod_name = "core." + str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")
        modules.append(mod_name)
        
    return modules


def _load_engine_classes() -> Dict[str, type]:
    """Import each engine module and collect classes that subclass ``BaseEngine``.
    Returns: dict: ``{module_name: EngineClass}``
    """
    engine_classes: Dict[str, type] = {}
    for full_name in _discover_engine_modules():
        try:
            module = importlib.import_module(full_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseEngine) and obj is not BaseEngine:
                    mod_name = full_name.split('.')[-1]
                    engine_classes[mod_name] = obj
                    break  # Assume one primary engine per file
        except Exception:
            logger.exception(f"[WARN] Failed to import {full_name}")
            continue
    return engine_classes


def list_ai_models() -> Dict[str, str]:
    """Return a mapping of engine module name → class name."""
    classes = _load_engine_classes()
    return {mod: cls.__name__ for mod, cls in classes.items()}


def count_ai_models() -> int:
    """Return the total number of AI engine classes discovered."""
    return len(_load_engine_classes())


def _import_engine(full_name: str) -> Any:
    """Import an engine by full module path and return the first subclass of ``BaseEngine`` found."""
    if not isinstance(full_name, str):
        raise TypeError(f"module_name must be a string, got {type(full_name)}")
        
    try:
        mod = importlib.import_module(full_name)
    except Exception:
        logger.exception(f"[AI Registry] Failed to import {full_name}")
        return None

    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if isinstance(obj, type) and issubclass(obj, BaseEngine) and obj is not BaseEngine:
            return obj
    logger.info(f"[AI Registry] No concrete BaseEngine subclass in {full_name}")
    return None

AI_MODELS: Dict[str, Any] = {}

def load_all_engines() -> Dict[str, Any]:
    """Reload every engine module and return a fresh ``AI_MODELS`` dictionary."""
    global AI_MODELS
    AI_MODELS = {}
    
    modules = _discover_engine_modules()
    for full_name in modules:
        cls = _import_engine(full_name)
        if cls:
            mod_name = full_name.split('.')[-1]
            AI_MODELS[mod_name] = cls
            
    return AI_MODELS

# Pre-load engines on module initialization
load_all_engines()

if __name__ == "__main__":
    models = list_ai_models()
    print(f"[SEARCH] Discovered {len(models)} AI engine(s) via pkgutil:")
    for mod, cls_name in sorted(models.items()):
        print(f"- {mod}: {cls_name}")
        
    print("\n[REGISTRY] Pre-loaded AI models from known list:")
    for name, cls in AI_MODELS.items():
        print(f" - {name}: {cls.__name__}")
    print(f"Total active AI models in registry: {len(AI_MODELS)}")
