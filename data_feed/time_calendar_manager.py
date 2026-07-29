import sys
import os
import time
import threading
import logging
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class TimeCalendarManager:
    """
    ระบบบริหารจัดการเวลาและข่าวสารเศรษฐกิจรวมศูนย์ (Time & News Calendar Manager)
    """
    def __init__(self, data_adapter=None, config=None):
        self.data_adapter = data_adapter
        if config is None:
            from config_setting.config_loader import get_time_calendar_manager_config
            config = get_time_calendar_manager_config()
        
        self.time_offset = 0
        self._sync_thread = None
        self.sync_interval = config.get("sync_interval", 30)
        self.max_sync_attempts = config.get("max_sync_attempts", 3)
        self.enable_news_sync = False  # Disable news sync by default

        # หากมี data_adapter ตั้งแต่ init ให้ทำการซิงค์เวลาและเริ่ม daemon thread ทันที
        if self.data_adapter is not None:
            self.sync_server_time()
            self.start_time_sync_thread()

    def sync_server_time(self, data_adapter=None):
        """
        ดึงเวลาจาก broker server timestamp และคำนวณ time_offset = server_time - local_time
        หากยิงขอเวลาไม่สำเร็จ ให้ระเบิด Fail-Fast: raise RuntimeError("FAIL-FAST: Failed to get server time offset from broker")
        """
        if data_adapter is not None:
            self.data_adapter = data_adapter

        if self.data_adapter is None or not hasattr(self.data_adapter, 'api') or self.data_adapter.api is None:
            logger.error("Failed to get server time offset: data_adapter or api is None")
            raise RuntimeError("FAIL-FAST: Failed to get server time offset from broker")

        try:
            server_time = self.data_adapter.api.get_server_timestamp()
            if server_time is None:
                raise ValueError("get_server_timestamp returned None")
            local_time = int(time.time())
            self.time_offset = server_time - local_time
            logger.info(f"[TIME SYNC] Server time offset: {self.time_offset} seconds")
        except RuntimeError:
            raise
        except Exception as e:
            logger.exception("Failed to get server time offset")
            raise RuntimeError("FAIL-FAST: Failed to get server time offset from broker") from e

    def start_time_sync_thread(self):
        """
        เปิด Daemon Thread คอยซิงค์เวลาใหม่โดยใช้ sync_interval จาก config
        """
        if self._sync_thread is not None and self._sync_thread.is_alive():
            logger.info("[TIME SYNC] Time sync thread is already running.")
            return

        def sync_worker():
            while True:
                try:
                    # Use configurable sync interval instead of hardcoded 30 seconds
                    now = datetime.now()
                    sleep_sec = (self.sync_interval - now.second % self.sync_interval) % self.sync_interval
                    if sleep_sec == 0:
                        sleep_sec = self.sync_interval
                    time.sleep(sleep_sec)
                    try:
                        self.sync_server_time()
                    except Exception as ex:
                        logger.exception("Error in periodic time sync")
                        raise  # No fallback - immediate failure
                except Exception as e:
                    logger.exception("Error in time sync worker thread")
                    raise  # No fallback - immediate failure

        self._sync_thread = threading.Thread(target=sync_worker, daemon=True, name="TimeSyncThread")
        self._sync_thread.start()
        logger.info("[TIME SYNC] Started time sync daemon thread (scheduled at :30 of every minute)")

    def get_broker_epoch(self) -> float:
        """
        คืนค่า time.time() + self.time_offset สำหรับส่งต่อให้ระบบดึงข้อมูลแท่งเทียน
        """
        return time.time() + self.time_offset

    def ensure_calendar_news(self):
        """
        ตรวจสอบว่ามีไฟล์ข่าวประจำวันนี้หรือยัง หากยังไม่มี ให้รัน calendar_news.py
        """
        try:
            import subprocess
            today_str = datetime.now().strftime("%Y-%m-%d")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            calendar_dir = os.path.join(base_dir, "data_base", "calendar_news")
            calendar_file = os.path.join(calendar_dir, f"calendar_{today_str}.json")
            
            if not os.path.exists(calendar_file):
                logger.info(f"[NEWS] Calendar file for today ({today_str}) not found. Running calendar_news.py...")
                script_path = os.path.join(base_dir, "calendar_news.py")
                if not os.path.exists(script_path):
                    script_path = os.path.join(base_dir, "data_evaluate", "calendar_news.py")
                    
                if os.path.exists(script_path):
                    subprocess.run([sys.executable, script_path], check=True, timeout=60)
                    logger.info("[NEWS] calendar_news.py executed successfully.")
                else:
                    logger.warning(f"[NEWS] calendar_news.py script not found at {script_path}")
            else:
                logger.info(f"[NEWS] Calendar file for today ({today_str}) already exists.")
        except Exception as e:
            logger.exception(f"Failed to ensure calendar news: {e}")