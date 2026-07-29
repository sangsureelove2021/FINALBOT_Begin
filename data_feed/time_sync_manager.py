import sys
import os
import time
import logging
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class TimeSyncManager:
    """
    ระบบบริหารจัดการการซิงค์เวลากับเซิร์ฟเวอร์ (Time Sync Manager)
    """
    def __init__(self, data_adapter=None, config=None):
        self.data_adapter = data_adapter
        if config is None:
            from config_setting.config_loader import get_time_sync_manager_config
            config = get_time_sync_manager_config()
        
        self.time_offset = 0
        self.sync_interval = config.get("sync_interval", 30)
        self.max_sync_attempts = config.get("max_sync_attempts", 3)

        # หากมี data_adapter ตั้งแต่ init ให้ทำการซิงค์เวลา 1 ครั้ง
        if self.data_adapter is not None:
            self.sync_server_time()

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

    def get_broker_epoch(self) -> float:
        """
        คืนค่า time.time() + self.time_offset สำหรับส่งต่อให้ระบบดึงข้อมูลแท่งเทียน
        """
        return time.time() + self.time_offset