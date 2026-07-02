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

from monitoring.console_dashboard import ConsoleUI

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
        logger.info(f"DeepSeek Agent found at: {self.agent_path}")
    
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
        if 'APPDATA' not in os.environ:
            raise KeyError("Missing APPDATA in os.environ")
        appdata = os.environ['APPDATA']
        npm_dirs = [os.path.join(appdata, 'npm')]
        
        if 'USERPROFILE' not in os.environ:
            raise KeyError("Missing USERPROFILE in os.environ")
        userprofile = os.environ['USERPROFILE']
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
        
        raise Exception("Agent executable not found")
        
    def check_readiness(self) -> str:
        """ทดสอบการเชื่อมต่อ AI ก่อนเริ่มรันระบบจริง"""
        agent_exec = self.agent_path
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
            raise Exception("AI Readiness check failed: empty output")
        except Exception as e:
            logger.exception(f"AI Readiness check failed: {e}")
            raise Exception(str(e))

    def _get_cache_key(self, context) -> str:
        """สร้าง cache key จาก market context"""
        try:
            if isinstance(context, dict):
                last_price = context.get('meta', {}).get('price', context.get('current_price'))
                symbol = context.get('meta', {}).get('symbol', context.get('symbol'))
            else:
                last_price = getattr(context, 'current_price', 0.0)
                symbol = getattr(context, 'symbol', 'UNKNOWN')
                
            minute_key = datetime.now().strftime('%Y%m%d%H%M')
            return f"{symbol}_{last_price}_{minute_key}"
        except Exception as e:
            logger.warning(f"Cache key generation error: {e}", exc_info=True)
            raise e
    
    def analyze_market(self, context) -> Optional[AIInsight]:
        """
        วิเคราะห์ตลาดโดยเรียก DeepSeek Agent
        """
        # --- Data Validation (Separation of Concerns) ---
        if isinstance(context, dict):
            if 'meta' in context and 'symbol' in context['meta']:
                symbol = context['meta']['symbol']
            else:
                symbol = context['symbol']
            timeframes = context['timeframes']
            m5_inds = timeframes['m5']
            rsi = m5_inds['rsi']
            ema5 = m5_inds['ema5']
            
            has_real_data = rsi != 0.0 and ema5 != 0.0
            if not has_real_data:
                logger.warning(f"Indicators for {symbol} are all zero — warming up, skipping AI call")
                raise ValueError(f"Indicators for {symbol} are all zero - missing real data")
        # -----------------------------------------------
        
        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            cached_time, cached_insight = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.debug(f"Using cached insight for {cache_key}")
                return cached_insight
        prompt = self._build_prompt(context)
        
        # ใช้ executable path ที่ตรวจพบ (หรือ fallback เป็น command name)
        agent_exec = self.agent_path

        # ──────────────────────────────────────────────────────────────
        # FIX: Windows shell=True ตีความ " ใน JSON ผิด → prompt ถูกตัด
        # แก้โดย: เขียน prompt ลง temp file แล้วส่ง path ผ่าน arg แทน
        # ใช้ shell=False + cmd /c สำหรับ .CMD files บน Windows
        # ──────────────────────────────────────────────────────────────
        import tempfile
        tmp_file = None
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.txt', prefix='bot_prompt_')
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                f.write(prompt)
            tmp_file = tmp_path
        except OSError as e:
            logger.exception("Failed to write prompt temp file — falling back to inline arg")
            raise Exception(str(e))

        # สร้าง flag list (ไม่มี profile flag เพราะ system prompt แก้ไขตรงแล้ว)
        agent_flags = ["--headless", "--no-tui", "--format=json-raw", "--max-iterations=1"]

        if tmp_path and os.path.exists(tmp_path):
            # ใช้ temp file เพื่อหลีกเลี่ยง shell quoting issues
            task_arg = f"@read_task_file:{tmp_path}"
        else:
            task_arg = prompt

        # บน Windows ใช้ shell=False + cmd /c เพื่อหลีกเลี่ยง cmd.exe quote parsing
        if os.name == 'nt':
            if agent_exec.lower().endswith(('.cmd', '.bat', '.ps1')):
                cmd_args = ['cmd', '/c', agent_exec] + agent_flags + [task_arg]
            else:
                cmd_args = [agent_exec] + agent_flags + [task_arg]
            use_shell = False
        else:
            cmd_args = [agent_exec] + agent_flags + [task_arg]
            use_shell = False

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
            ConsoleUI.show_ai_prompt_sent()
            try:
                stdout_bytes, stderr_bytes = p.communicate(timeout=self.timeout)
                stdout_text = stdout_bytes.decode('utf-8', errors='replace')
            except subprocess.TimeoutExpired:
                logger.warning(f"Agent timeout after {self.timeout}s. Terminating process tree...")
                if sys.platform == 'win32':
                    try:
                        subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
                    except subprocess.SubprocessError as e:
                        raise Exception("Failed to run taskkill on win32 process tree") from e
                else:
                    # บน Unix/Mac ทำลาย process group
                    try:
                        import signal
                        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    except OSError as e:
                        raise Exception("Failed to kill process group using killpg") from e
                p.wait()
                self.consecutive_failures += 1
                logger.warning(f"AI timeout — ข้ามรอบนี้ ไม่เทรด (timeout {self.timeout}s)")
                raise TimeoutError(f"AI timeout after {self.timeout}s")
                
            if p.returncode != 0:
                logger.error(f"Agent error (code {p.returncode})")
                if stdout_text:
                    logger.error(f"Error details: {stdout_text[:200]}")
                stderr_text = stderr_bytes.decode('utf-8', errors='replace')
                if stderr_text:
                    logger.error(f"Stderr: {stderr_text[:200]}")
                self.consecutive_failures += 1
                logger.warning("AI error — ข้ามรอบนี้ ไม่เทรด")
                raise Exception(f"Agent error (code {p.returncode}), stderr: {stderr_text}")
            
            self.consecutive_failures = 0
            insight = self._parse_response(stdout_text, context)
            if insight:
                self._cache[cache_key] = (datetime.now(), insight)
                return insight
            else:
                logger.warning("AI parse failed — ข้ามรอบนี้ ไม่เทรด")
                raise Exception("AI parse failed")
        except FileNotFoundError:
            logger.error(f"Agent command '{self.agent_command}' not found. Is deepseek-agent installed?")
            self.consecutive_failures = self.max_failures
            logger.warning("AI not found — ข้ามรอบนี้ ไม่เทรด")
            raise FileNotFoundError(f"Agent command '{self.agent_command}' not found")
        except Exception as e:
            logger.exception(f"Unexpected error calling agent: {e}")
            self.consecutive_failures += 1
            logger.warning("AI unexpected error — ข้ามรอบนี้ ไม่เทรด")
            raise Exception(str(e))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as cleanup_e:
                    logger.warning(f"Failed to delete temp file {tmp_path}: {cleanup_e}")
                    raise Exception(str(cleanup_e))

    def _build_prompt(self, context):
        try:
            from core.ai_analysis.prompt_ai_context import build_prompt
            
            # Extract strategy type from market state if available
            if hasattr(context, '__dict__'):
                ctx = dict(context.__dict__)
            else:
                ctx = dict(context) if isinstance(context, dict) else {}
            return build_prompt(ctx)
        except Exception as e:
            logger.exception(f"Error building prompt: {e}")
            raise e

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
                raise ValueError("No JSON found in response")
            
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
            except json.JSONDecodeError as json_e:
                logger.error(f"JSON parsing failed. Extracted string: {json_str[:200]}")
                raise json_e
            
            if not isinstance(data, dict):
                logger.error(f"Parsed data is not a dictionary: {type(data)}")
                raise TypeError(f"Parsed data is not a dictionary: {type(data)}")
                
            if 'action' not in data:
                raise KeyError("Missing 'action' in response data")
            action = data['action']
            if not isinstance(action, str):
                raise TypeError("'action' must be a string")
            action = action.upper()
            if action not in ['CALL', 'PUT', 'NO_TRADE']:
                raise ValueError(f"Invalid action: {action}")
            
            if 'confidence' not in data:
                raise KeyError("Missing 'confidence' in response data")
            conf_val = data['confidence']
            try:
                if isinstance(conf_val, str):
                    conf_val = re.sub(r'[^\d]', '', conf_val)
                    if not conf_val:
                        raise ValueError("Empty confidence string")
                    confidence = int(conf_val)
                elif isinstance(conf_val, (int, float)):
                    confidence = int(conf_val)
                else:
                    raise TypeError(f"Unexpected type for confidence: {type(conf_val)}")
            except Exception as e:
                logger.exception("Failed to parse confidence value")
                raise Exception(str(e))
            confidence = max(0, min(100, confidence))
            
            if 'expiry' not in data:
                raise KeyError("Missing 'expiry' in response data")
            expiry = int(data['expiry'])
            if expiry < 1 or expiry > 15:
                raise ValueError(f"Invalid expiry: {expiry}")
            
            if 'reason' not in data:
                raise KeyError("Missing 'reason' in response data")
            reason = data['reason'][:500]
            
            if isinstance(context, dict):
                if 'meta' in context and 'symbol' in context['meta']:
                    symbol = context['meta']['symbol']
                else:
                    symbol = context['symbol']
            else:
                symbol = getattr(context, 'symbol')
            
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
                logger.exception(f"Parse error: {e}. Raw response: {response_text[:500]}")
                raise Exception(str(e))
    
