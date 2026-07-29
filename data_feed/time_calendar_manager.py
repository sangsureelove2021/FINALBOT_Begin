import sys
import os
import time
import threading
import subprocess
import logging
from datetime import datetime

from monitoring.console_dashboard import logger, ConsoleUI


class TimeCalendarManager:
    """
    ระบบบริหารจัดการเวลาและข่าวสารเศรษฐกิจรวมศูนย์ (Time & News Calendar Manager)
    """
    def __init__(self, data_adapter=None):
        self.data_adapter = data_adapter
        self.time_offset = 0
        self._sync_thread = None

        # ระบบจัดการข่าวสารประจำวัน
        self.ensure_calendar_news()

        # หากมี data_adapter ตั้งแต่ init ให้ทำการซิงค์เวลาและเริ่ม daemon thread ทันที
        if self.data_adapter is not None:
            self.sync_server_time()
            self.start_time_sync_thread()

    def ensure_calendar_news(self):
        """
        ตรวจสอบว่าไฟล์ข่าวประจำวันนี้ใน all_filelogs/calendar_logs/calendar_YYYY-MM-DD.json มีอยู่แล้วหรือยัง
        หากยังไม่มี ให้รัน calendar_news.py เพื่อดาวน์โหลดและส่งออกไฟล์ข่าวทันทีเมื่อเริ่มรันบอท
        """
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "all_filelogs", "calendar_logs")
            calendar_file = os.path.join(log_dir, f"calendar_{today_str}.json")

            if not os.path.exists(calendar_file):
                logger.info(f"[NEWS] Calendar file for today ({today_str}) not found. Running calendar_news.py...")
                script_path = os.path.join(base_dir, "calendar_news.py")
                if os.path.exists(script_path):
                    subprocess.run([sys.executable, script_path], check=True, timeout=60)
                    logger.info("[NEWS] calendar_news.py executed successfully.")
                    ConsoleUI.show_news_status(f"ดาวน์โหลดปฏิทินข่าวประจำวัน ({today_str}) : สำเร็จเรียบร้อย")
                else:
                    logger.warning(f"[NEWS] calendar_news.py script not found at {script_path}")
                    raise FileNotFoundError(f"script not found at {script_path}")
            else:
                logger.info(f"[NEWS] Calendar file for today ({today_str}) already exists.")
                ConsoleUI.show_news_status(f"ตรวจสอบปฏิทินข่าวประจำวัน ({today_str}) : มีไฟล์แล้วพร้อมใช้งาน")
        except Exception as e:
            logger.exception("Failed to check or run calendar_news.py at startup")
            raise RuntimeError(f"FAIL-FAST: Failed to execute calendar_news.py: {e}") from e

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
            ConsoleUI.show_time_offset(self.time_offset)
        except RuntimeError:
            raise
        except Exception as e:
            logger.exception("Failed to get server time offset")
            raise RuntimeError("FAIL-FAST: Failed to get server time offset from broker") from e

    def start_time_sync_thread(self):
        """
        เปิด Daemon Thread คอยซิงค์เวลาใหม่ในทุกๆ วินาทีที่ 30 (:30) ของทุกนาที
        """
        if self._sync_thread is not None and self._sync_thread.is_alive():
            logger.info("[TIME SYNC] Time sync thread is already running.")
            return

        def sync_worker():
            while True:
                try:
                    now = datetime.now()
                    sleep_sec = (30 - now.second) % 60
                    if sleep_sec == 0:
                        sleep_sec = 60
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
