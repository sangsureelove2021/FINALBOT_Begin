import time
from typing import Dict


class SignalThrottle:
    def __init__(self, cooldown_seconds: int = 300):
        self.last_signal_time: Dict[str, float] = {}
        self.cooldown_seconds = cooldown_seconds

    def allow(self, symbol: str, action: str) -> bool:
        now = time.time()
        key = f'{symbol}_{action}'
        if key in self.last_signal_time:
            if now - self.last_signal_time[key] < self.cooldown_seconds:
                return False
        self.last_signal_time[key] = now
        return True

    def reset(self):
        self.last_signal_time.clear()
