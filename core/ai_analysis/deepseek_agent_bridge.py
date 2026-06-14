"""
DeepSeek Agent Bridge - เชื่อมต่อ FINALBOT กับ DeepSeek Agent CLI

บทบาท:
- รับ MarketContext (RSI, MACD, EMA, trend, market_state, etc.)
- สร้าง prompt ที่มีตัวเลขทางเทคนิคครบถ้วน
- เรียก DeepSeek Agent ผ่าน subprocess
- แปลง JSON response เป็น AIInsight (action, confidence, expiry, reason)
- ส่งกลับไปยัง Pipeline หรือ FusionGate

ใช้กับ BOT_MODE = 'AI' ใน runner.py
"""

import subprocess
import json
import logging
import os
import sys
import shutil
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger("DeepSeekAgent")


@dataclass
class AIInsight:
    """ผลการวิเคราะห์จาก DeepSeek Agent"""
    action: str          # "CALL", "PUT", or "NO_TRADE"
    confidence: int      # 0-100
    expiry: int          # Expiry time in minutes (e.g. 1, 2, 3, 4, 5)
    reason: str
    raw_response: str
    timestamp: str
    symbol: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeepSeekAgentBridge:
    """
    สะพานเชื่อมระหว่าง FINALBOT กับ DeepSeek Agent CLI
    ใช้ subprocess เพื่อเรียก Agent โดยไม่มีค่าใช้จ่าย
    """
    
    def __init__(self, 
                 agent_command: str = "deepseek-agent",
                 timeout_seconds: int = 15,
                 cache_ttl_seconds: int = 5):
        """
        Args:
            agent_command: ชื่อคำสั่งหรือพาธไปยัง deepseek-agent executable
            timeout_seconds: หมดเวลารอ Agent ตอบ (วินาที)
            cache_ttl_seconds: อายุของ cache (วินาที) - ใช้ลดการเรียกซ้ำ
        """
        self.agent_command = agent_command
        self.timeout = timeout_seconds
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, AIInsight)
        self.consecutive_failures = 0
        self.max_failures = 3
        
        # Auto-detect the actual executable path on Windows
        self.agent_path = self._find_agent_executable()
        if self.agent_path:
            logger.info(f"DeepSeek Agent found at: {self.agent_path}")
        else:
            logger.warning(f"DeepSeek Agent not found in PATH or common locations. Will search again at runtime.")
    
    def _find_agent_executable(self) -> Optional[str]:
        """
        ค้นหา deepseek-agent executable บน Windows โดยอัตโนมัติ
        ค้นหาจาก:
        1. system PATH (shutil.which)
        2. %APPDATA%\npm\deepseek-agent.cmd
        3. %USERPROFILE%\AppData\Roaming\npm\deepseek-agent.cmd
        4. ทดลองใส่ .cmd, .bat, .exe ต่อท้าย
        Returns:
            พาธแบบเต็มของ executable หรือ None ถ้าไม่พบ
        """
        # ถ้าผู้ใช้ระบุพาธแบบเต็มแล้ว และมีอยู่จริง ให้ใช้ทันที
        if os.path.isfile(self.agent_command):
            return self.agent_command
        
        # รายชื่อนามสกุลที่รองรับบน Windows
        exe_names = [self.agent_command]
        if sys.platform == 'win32':
            for ext in ['.cmd', '.bat', '.exe']:
                if not self.agent_command.lower().endswith(ext):
                    exe_names.append(self.agent_command + ext)
        
        # 1. ค้นหาใน PATH
        for name in exe_names:
            found = shutil.which(name)
            if found:
                logger.debug(f"Found {name} in PATH: {found}")
                return found
        
        # 2. ค้นหาในโฟลเดอร์ npm global (Windows)
        appdata = os.environ.get('APPDATA', '')
        npm_dirs = []
        if appdata:
            npm_dirs.append(os.path.join(appdata, 'npm'))
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            npm_dirs.append(os.path.join(userprofile, 'AppData', 'Roaming', 'npm'))
        
        for npm_dir in npm_dirs:
            if os.path.isdir(npm_dir):
                for name in exe_names:
                    candidate = os.path.join(npm_dir, name)
                    if os.path.isfile(candidate):
                        logger.debug(f"Found {name} in npm directory: {candidate}")
                        return candidate
        
        # 3. ค้นหาในไดเรกทอรีของ Python environment (Scripts folder)
        if hasattr(sys, 'prefix'):
            scripts_dir = os.path.join(sys.prefix, 'Scripts')
            if os.path.isdir(scripts_dir):
                for name in exe_names:
                    candidate = os.path.join(scripts_dir, name)
                    if os.path.isfile(candidate):
                        logger.debug(f"Found {name} in Scripts: {candidate}")
                        return candidate
        
        return None
        
    def _get_cache_key(self, context) -> str:
        """สร้าง cache key จาก market context"""
        try:
            last_price = getattr(context, 'current_price', 0)
            symbol = getattr(context, 'symbol', 'unknown')
            minute_key = datetime.now().strftime('%Y%m%d%H%M')
            return f"{symbol}_{last_price}_{minute_key}"
        except:
            return datetime.now().strftime('%Y%m%d%H%M%S')
    
    def analyze_market(self, context) -> Optional[AIInsight]:
        """
        วิเคราะห์ตลาดโดยเรียก DeepSeek Agent
        """
        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            cached_time, cached_insight = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.debug(f"Using cached insight for {cache_key}")
                return cached_insight
        prompt = self._build_prompt(context)
        
        # ใช้ executable path ที่ตรวจพบ (หรือ fallback เป็น command name)
        agent_exec = self.agent_path if self.agent_path else self.agent_command
        
        # รันผ่าน shell=True เพื่อให้โหลด NPM environment สำเร็จ และรองรับการทำความสะอาดโปรเซสลูก
        # ใช้การบันทึกผลลัพธ์ลงไฟล์ชั่วคราวเพื่อเลี่ยงท่อ (pipe) ค้างในระบบปฏิบัติการต่างๆ
        temp_file = os.path.abspath(f"temp_ds_{datetime.now().strftime('%H%M%S')}.txt")
        
        # แปลงขึ้นบรรทัดใหม่เป็นเว้นวรรค
        prompt_clean = prompt.replace('\r', '').replace('\n', ' ')
        cmd_args = f'"{agent_exec}" --headless "{prompt_clean}" > "{temp_file}" 2>&1'
        use_shell = True
            
        try:
            # ใช้ subprocess.Popen เพื่อควบคุม process tree
            p = subprocess.Popen(
                cmd_args,
                shell=use_shell,
                env=os.environ.copy()
            )
            try:
                p.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Agent timeout after {self.timeout}s. Terminating process tree...")
                if sys.platform == 'win32':
                    subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
                else:
                    # บน Unix/Mac ทำลาย process group
                    try:
                        import signal
                        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    except:
                        p.kill()
                p.wait()
                if os.path.exists(temp_file):
                    try: os.remove(temp_file)
                    except: pass
                self.consecutive_failures += 1
                return self.get_fallback_insight(context)
                
            # ดึงข้อความจากไฟล์ชั่วคราว
            stdout_text = ""
            if os.path.exists(temp_file):
                try:
                    with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
                        stdout_text = f.read()
                    os.remove(temp_file)
                except Exception as e:
                    logger.error(f"Failed to read/remove temp file: {e}")
                
            if p.returncode != 0:
                logger.error(f"Agent error (code {p.returncode})")
                if stdout_text:
                    logger.error(f"Error details: {stdout_text[:200]}")
                self.consecutive_failures += 1
                return self.get_fallback_insight(context)
            
            self.consecutive_failures = 0
            insight = self._parse_response(stdout_text, context)
            if insight:
                self._cache[cache_key] = (datetime.now(), insight)
                return insight
            else:
                return self.get_fallback_insight(context)
        except FileNotFoundError as e:
            # พยายามค้นหาอีกครั้ง (อาจมีการติดตั้งระหว่างรัน)
            self.agent_path = self._find_agent_executable()
            if self.agent_path:
                logger.info("Re-attempting with newly found agent executable")
                return self.analyze_market(context)  # recursive retry once
            else:
                logger.error(f"Agent command '{self.agent_command}' not found even after search. Is deepseek-agent installed?")
                self.consecutive_failures = self.max_failures
                return self.get_fallback_insight(context)
        except Exception as e:
            logger.exception(f"Unexpected error calling agent: {e}")
            self.consecutive_failures += 1
            return self.get_fallback_insight(context)

    def _build_prompt(self, context) -> str:
        if hasattr(context, '__dict__'):
            ctx = context.__dict__
        else:
            ctx = context if isinstance(context, dict) else {}
        
        symbol = ctx.get('symbol', getattr(context, 'symbol', 'EURUSD'))
        current_price = ctx.get('current_price', getattr(context, 'current_price', 0))
        rsi = ctx.get('rsi', getattr(context, 'rsi', 50))
        macd = ctx.get('macd', getattr(context, 'macd', 0))
        trend = ctx.get('trend', getattr(context, 'trend', 'neutral'))
        volatility = ctx.get('volatility', getattr(context, 'volatility', 'medium'))
        support_resistance = ctx.get('support_resistance', getattr(context, 'support_resistance', 'N/A'))
        
        prompt = f"""You are a professional binary options trader. Analyze the following market data and output ONLY a valid JSON object.
You can choose the optimal expiry time (from 1 to 5 minutes) based on market structure and volatility.

MARKET DATA:
Symbol: {symbol}
Current Price: {current_price}
Timestamp: {datetime.now().isoformat()}

TECHNICAL INDICATORS:
- RSI (14): {rsi:.2f}
- MACD Histogram/Difference: {macd:.5f}
- Trend: {trend}
- Volatility: {volatility}
- Support/Resistance: {support_resistance}

OUTPUT FORMAT (JSON only, no other text):
{{
  "action": "CALL",
  "confidence": 85,
  "expiry": 3,
  "reason": "Explain reason briefly in Thai"
}}
"""
        return prompt
    
    def _parse_response(self, response_text: str, context) -> Optional[AIInsight]:
        try:
            response_text = response_text.strip()
            
            # ลบ ANSI escape codes (สีใน terminal) ออกทั้งหมดเพื่อป้องกันปัญหาระบบจัดรูปตัวอักษรพัง
            import re
            ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
            response_text = ansi_escape.sub('', response_text)
            
            start_idx = response_text.rfind('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0 or start_idx > end_idx:
                logger.error(f"No JSON found in response")
                return None
            
            json_str = response_text[start_idx:end_idx]
            try:
                data = json.loads(json_str)
            except Exception:
                import ast
                # Fallback to ast.literal_eval if the AI used single quotes or python dict format
                data = ast.literal_eval(json_str)
            
            action = data.get('action', 'NO_TRADE').upper()
            if action not in ['CALL', 'PUT', 'NO_TRADE']:
                action = 'NO_TRADE'
            
            confidence = int(data.get('confidence', 0))
            confidence = max(0, min(100, confidence))
            
            # Extract expiry (default to 5 minutes if missing or out of bounds)
            expiry = int(data.get('expiry', 5))
            if expiry < 1 or expiry > 15:
                expiry = 5
            
            reason = data.get('reason', 'No reason provided')[:500]
            symbol = getattr(context, 'symbol', 'unknown')
            
            return AIInsight(
                action=action,
                confidence=confidence,
                expiry=expiry,
                reason=reason,
                raw_response=response_text[:1000],
                timestamp=datetime.now().isoformat(),
                symbol=symbol
            )
            
        except Exception as e:
            logger.error(f"Parse error: {e}. Raw response: {response_text[:500]}")
            return None
    
    def get_fallback_insight(self, context) -> AIInsight:
        symbol = getattr(context, 'symbol', 'unknown')
        return AIInsight(
            action='NO_TRADE',
            confidence=0,
            expiry=5,
            reason='Fallback to NO_TRADE',
            raw_response='',
            timestamp=datetime.now().isoformat(),
            symbol=symbol
        )
