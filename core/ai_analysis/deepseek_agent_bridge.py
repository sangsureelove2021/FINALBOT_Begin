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
import re
import ast
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
        r"""
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
        
    def check_readiness(self) -> str:
        """ทดสอบการเชื่อมต่อ AI ก่อนเริ่มรันระบบจริง"""
        agent_exec = self.agent_path if self.agent_path else self.agent_command
        cmd_args = [agent_exec, "--headless", "--no-tui", "--max-iterations=1", "System check. Briefly introduce yourself (including your AI model name) and state you are ready to analyze the market. Reply in a single short line in English."]

        
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        try:
            p = subprocess.Popen(
                cmd_args,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            stdout_bytes, stderr_bytes = p.communicate(timeout=75)
            stdout_text = stdout_bytes.decode('utf-8', errors='replace').strip()
            
            # ลบ ANSI escape codes ออก
            ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
            stdout_text = ansi_escape.sub('', stdout_text)
            
            # ลบข้อความ UI ของ DeepSeek Agent ออกให้เหลือแค่คำตอบ AI
            if "TASK COMPLETE" in stdout_text:
                parts = stdout_text.split("TASK COMPLETE")
                if len(parts) > 1:
                    clean_text = parts[-1]
                    clean_text = re.sub(r'[━═]', '', clean_text)
                    clean_text = re.sub(r'ℹ|Shutting down\.\.\.', '', clean_text)
                    # บังคับให้อยู่ในบรรทัดเดียว
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    if clean_text:
                        return clean_text
                        
            if len(stdout_text) > 0:
                return stdout_text
            return ""
        except Exception as e:
            logger.error(f"AI Readiness check failed: {e}")
            return ""

    def _get_cache_key(self, context) -> str:
        """สร้าง cache key จาก market context"""
        try:
            if isinstance(context, dict):
                last_price = context.get('current_price', 0)
                symbol = context.get('symbol', 'unknown')
            else:
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
        # เพิ่ม flags เพื่อบังคับให้ส่งเฉพาะข้อความ JSON กลับมา:
        # --no-tui: ปิด TUI decorations (กรอบ, สี, spinner)
        # --format=json-raw: output เป็น JSON เท่านั้น
        # --max-iterations=1: ไม่ให้เรียก tools (run_command, write_file) แค่ตอบ JSON
        cmd_args = [agent_exec, "--headless", "--no-tui", "--format=json-raw", "--max-iterations=1", prompt]
        use_shell = True
            
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        try:
            # ใช้ subprocess.Popen เพื่อควบคุม process tree
            p = subprocess.Popen(
                cmd_args,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
                creationflags=creation_flags
            )
            try:
                stdout_bytes, stderr_bytes = p.communicate(timeout=self.timeout)
                stdout_text = stdout_bytes.decode('utf-8', errors='replace')
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
                self.consecutive_failures += 1
                logger.warning(f"AI timeout — ข้ามรอบนี้ ไม่เทรด (timeout {self.timeout}s)")
                return None
                
            if p.returncode != 0:
                logger.error(f"Agent error (code {p.returncode})")
                if stdout_text:
                    logger.error(f"Error details: {stdout_text[:200]}")
                stderr_text = stderr_bytes.decode('utf-8', errors='replace')
                if stderr_text:
                    logger.error(f"Stderr: {stderr_text[:200]}")
                self.consecutive_failures += 1
                logger.warning("AI error — ข้ามรอบนี้ ไม่เทรด")
                return None
            
            self.consecutive_failures = 0
            insight = self._parse_response(stdout_text, context)
            if insight:
                self._cache[cache_key] = (datetime.now(), insight)
                return insight
            else:
                logger.warning("AI parse failed — ข้ามรอบนี้ ไม่เทรด")
                return None
        except FileNotFoundError as e:
            # พยายามค้นหาอีกครั้ง (อาจมีการติดตั้งระหว่างรัน)
            self.agent_path = self._find_agent_executable()
            if self.agent_path:
                logger.info("Re-attempting with newly found agent executable")
                return self.analyze_market(context)  # recursive retry once
            else:
                logger.error(f"Agent command '{self.agent_command}' not found even after search. Is deepseek-agent installed?")
                self.consecutive_failures = self.max_failures
                logger.warning("AI not found — ข้ามรอบนี้ ไม่เทรด")
                return None
        except Exception as e:
            logger.exception(f"Unexpected error calling agent: {e}")
            self.consecutive_failures += 1
            logger.warning("AI unexpected error — ข้ามรอบนี้ ไม่เทรด")
            return None

    def _build_prompt(self, context) -> str:
        if hasattr(context, '__dict__'):
            ctx = context.__dict__
        else:
            ctx = context if isinstance(context, dict) else {}
            
        # --- Advanced Context Mode ---
        if ctx.get("is_advanced"):
            payload = dict(ctx)
            payload.pop("is_advanced", None)
            json_payload = json.dumps(payload, indent=2, ensure_ascii=False)
            
            prompt = f"""You are a professional binary options trader. Analyze the following comprehensive market JSON data and reply with ONLY a valid JSON object.
CRITICAL INSTRUCTIONS:
1. DO NOT use any tools.
2. DO NOT run any shell commands.
3. DO NOT write or save any files.
4. Just type the raw JSON text as your normal chat response.
5. EXTREMELY IMPORTANT: Your JSON must be strictly valid. ALL keys and ALL string values MUST be enclosed in double quotes ("").
6. REASON LENGTH: The "reason" field MUST be in Thai, and MUST be strictly between 20 and 40 words, summarizing the most important factor.

You can choose the optimal expiry time (from 1 to 5 minutes) based on market structure and volatility.
MARKET DATA JSON:
{json_payload}

OUTPUT FORMAT (Return exactly this JSON structure and nothing else):
{{
  "action": "CALL",
  "confidence": 85,
  "expiry": 3,
  "reason": "Explain the most important reason in Thai (20-40 words)"
}}
"""
            return prompt
        
        # --- Legacy Context Mode ---
        symbol = ctx.get('symbol', getattr(context, 'symbol', 'EURUSD'))
        current_price = ctx.get('current_price', getattr(context, 'current_price', 0))
        rsi = ctx.get('rsi', getattr(context, 'rsi', 50))
        macd = ctx.get('macd', getattr(context, 'macd', 0))
        trend = ctx.get('trend', getattr(context, 'trend', 'neutral'))
        volatility = ctx.get('volatility', getattr(context, 'volatility', 'medium'))
        support_resistance = ctx.get('support_resistance', getattr(context, 'support_resistance', 'N/A'))
        
        prompt = f"""You are a professional binary options trader. Analyze the following market data and reply with ONLY a valid JSON object.
CRITICAL INSTRUCTIONS:
1. DO NOT use any tools.
2. DO NOT run any shell commands (like echo).
3. DO NOT write or save any files.
4. Just type the raw JSON text as your normal chat response.
5. EXTREMELY IMPORTANT: Your JSON must be strictly valid. ALL keys and ALL string values MUST be enclosed in double quotes (""). Do not leave strings unquoted.

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

OUTPUT FORMAT (Return exactly this JSON structure and nothing else):
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
            ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
            response_text = ansi_escape.sub('', response_text)
            
            # Find the FIRST '{' and LAST '}' to extract the outermost JSON block
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0 or start_idx > end_idx:
                logger.error(f"No JSON found in response")
                return None
            
            json_str = response_text[start_idx:end_idx]
            
            # --- FIX: Auto-correct unquoted keys and known string values ---
            # AI sometimes returns: { action: CALL, confidence: 75, expiry: 5, reason: ... }
            # Add quotes to known keys
            # Add quotes to known keys, only if they follow {, or newline to avoid replacing inside strings
            for key in ["action", "confidence", "expiry", "reason"]:
                json_str = re.sub(rf'([{{,\n]\s*|^){key}\s*:', rf'\1"{key}":', json_str)
                
            # Add quotes to known string values if unquoted
            for val in ["CALL", "PUT", "NO_TRADE"]:
                # Matches if the value is directly after a colon/space and followed by a comma or newline
                json_str = re.sub(rf':\s*{val}\b(?!")', f': "{val}"', json_str)
                
            # Try to fix unquoted reason strings (anything after "reason": that isn't quoted, up to the closing brace)
            # This is tricky, so we just attempt json.loads and ast.literal_eval first.
            
            data = None
            try:
                data = json.loads(json_str)
            except Exception as json_e:
                try:
                    data = ast.literal_eval(json_str)
                except Exception as ast_e:
                    # Final aggressive fallback: manually extract values using regex
                    logger.warning(f"Standard parsing failed. Attempting regex extraction. Extracted string: {json_str[:200]}")
                    data = {}
                    
                    action_match = re.search(r'"?action"?\s*:\s*"?([A-Z_]+)"?', json_str, re.IGNORECASE)
                    if action_match:
                        data["action"] = action_match.group(1).upper()
                        
                    conf_match = re.search(r'"?confidence"?\s*:\s*(\d+)', json_str, re.IGNORECASE)
                    if conf_match:
                        data["confidence"] = int(conf_match.group(1))
                        
                    exp_match = re.search(r'"?expiry"?\s*:\s*(\d+)', json_str, re.IGNORECASE)
                    if exp_match:
                        data["expiry"] = int(exp_match.group(1))
                        
                    # Capture reason - anything from reason: up to the closing } or another key
                    reason_match = re.search(r'"?reason"?\s*:\s*"?([^}]+)"?\s*}?\s*', json_str, re.IGNORECASE | re.DOTALL)
                    if reason_match:
                        data["reason"] = reason_match.group(1).strip().strip('"').strip("'")
                    
                    if not data:
                        logger.error(f"JSON, AST, and Regex parsing all failed. Extracted string: {json_str[:200]}")
                        return None
            
            if not isinstance(data, dict):
                logger.error(f"Parsed data is not a dictionary: {type(data)}")
                return None
                
            action = data.get('action', 'NO_TRADE')
            action = action.upper() if isinstance(action, str) else 'NO_TRADE'
            if action not in ['CALL', 'PUT', 'NO_TRADE']:
                action = 'NO_TRADE'
            
            try:
                conf_val = data.get('confidence', 0)
                if isinstance(conf_val, str):
                    conf_val = re.sub(r'[^\d]', '', conf_val)
                confidence = int(conf_val) if conf_val else 0
            except:
                confidence = 0
            confidence = max(0, min(100, confidence))
            
            # Extract expiry (default to 5 minutes if missing or out of bounds)
            expiry = int(data.get('expiry', 5))
            if expiry < 1 or expiry > 15:
                expiry = 5
            
            reason = data.get('reason', 'No reason provided')[:500]
            
            if isinstance(context, dict):
                symbol = context.get('symbol', 'unknown')
            else:
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
    
