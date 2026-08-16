"""
IDataSource — Abstract Base Class (ABC) Interface มาตรฐานสำหรับทุก Broker Adapter
data_feed/abstract_class.py

กฎ: Adapter ทุกตัวต้อง implement เมธอดที่ marked @abstractmethod ทั้งหมด
เพื่อให้ DataAdapter (Coordinator) เรียกใช้งานได้ในรูปแบบเดียวกัน ไม่สนว่าดึงมาจากโบรกเกอร์ไหน
กำหนด Abstract Base Class (ABC) สำหรับเป็น Interface มาตรฐานของแหล่งข้อมูล (Data Source)
ไฟล์นี้ทำหน้าที่เป็นสัญญา (Contract) ให้ Adapter ที่จะสร้างขึ้นมาทั้งหมด
ต้องมีเมธอดตามที่กำหนดไว้ เพื่อให้ส่วนอื่นของระบบเรียกใช้งานได้ในรูปแบบเดียวกัน
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from typing import Callable, Any, List, Dict


class IDataSource(ABC):
    """
    Interface (สัญญา) สำหรับ Data Source Adapter ทุกตัว
    กำหนดเมธอดมาตรฐานที่ทุกโบรกเกอร์ต้อง implement เพื่อให้ DataAdapter เรียกใช้งานได้ในรูปแบบเดียวกัน
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with configuration from settings.json.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}

    # ── Connection ──────────────────────────────────────────────────

    @abstractmethod
    def connect(self) -> None:
        """สร้างการเชื่อมต่อเริ่มต้นไปยังแหล่งข้อมูล"""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """ยกเลิกการเชื่อมต่อจากแหล่งข้อมูล"""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """
        ตรวจสอบสถานะการเชื่อมต่อ
        Returns:
            bool: True หากเชื่อมต่อ, False หากไม่ได้เชื่อมต่อ
        """
        raise NotImplementedError

    # ── Candle & Stream Data ────────────────────────────────────────

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, count: int, end_time: Optional[float] = None) -> pd.DataFrame:
        """
        ดึงข้อมูลแท่งเทียนสำหรับสัญลักษณ์และ timeframe ที่กำหนด

        Args:
            symbol: ชื่อสัญลักษณ์ เช่น 'EURUSD-OTC' (ตาม settings.json)
            timeframe: 'M1', 'M5', 'M15'
            count: จำนวนแท่งเทียนที่ต้องการ
            end_time: epoch timestamp สิ้นสุด (optional)

        Returns:
            DataFrame [open, high, low, close, volume] indexed by UTC datetime
        """
        raise NotImplementedError

    @abstractmethod
    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """
        เริ่มต้นการสตรีมข้อมูลราคาสำหรับสินทรัพย์และ Timeframe ที่กำหนด
        
        Args:
            symbol: ชื่อสัญลักษณ์ เช่น 'EURUSD-OTC'
            timeframe: 'M1', 'M5', 'M15'
            count: จำนวนแท่งเทียนที่ต้องการเก็บใน stream buffer
        """
        raise NotImplementedError

    # ── Server Time ────────────────────────────────────────────────

    @abstractmethod
    def get_server_timestamp(self) -> float:
        """
        ดึงเวลาปัจจุบันจากเซิร์ฟเวอร์โบรกเกอร์
        
        Returns:
            float: server epoch timestamp
        """
        raise NotImplementedError

    # ── Account ─────────────────────────────────────────────────────

    @abstractmethod
    def get_balance(self) -> float:
        """
        ดึงยอดเงินคงเหลือในบัญชี

        Returns:
            float: ยอดเงินคงเหลือ
        """
        raise NotImplementedError

    # ── Optional & Advanced ─────────────────────────────────────────

    @property
    def connected(self) -> bool:
        """Property shortcut สำหรับ self.is_connected()"""
        return self.is_connected()

    async def get_historical_candles(self, symbol: str, timeframe: int, count: int, end_time: float) -> List[Dict[str, Any]]:
        """
        (Optional) ดึงข้อมูลแท่งเทียนย้อนหลัง (สำหรับระบบที่ต้องการ)
        หมายเหตุ: ในโปรเจกต์นี้ ฟังก์ชันนี้อาจไม่ถูกใช้งานตามข้อกำหนด
        แต่ใส่ไว้เพื่อความสมบูรณ์ของ Interface
        """
        # ตามข้อกำหนดที่ห้ามดึงข้อมูลย้อนหลัง เราจะคืนค่าว่างเสมอ
        return []

class BaseSkeletonAdapter(IDataSource):
    """
    Base Skeleton Adapter for unimplemented brokers to remove duplicated code.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None, broker_name: str = "Skeleton"):
        super().__init__(config)
        self._connected = False
        self.broker_name = broker_name
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"{self.broker_name}Adapter is a skeleton and not yet fully implemented.")

    def is_connected(self) -> bool:
        return self._connected

    @property
    def connected(self) -> bool:
        return self._connected

    def get_candles(self, symbol: str, timeframe: str, count: int, end_time: Optional[float] = None) -> pd.DataFrame:
        raise NotImplementedError(f"{self.broker_name} get_candles not implemented")

    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        raise NotImplementedError(f"{self.broker_name} start_stream not implemented")

    def get_server_timestamp(self) -> float:
        raise NotImplementedError(f"{self.broker_name} get_server_timestamp not implemented")

    def get_balance(self) -> float:
        raise NotImplementedError(f"{self.broker_name} get_balance not implemented")

    def connect(self) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"{self.broker_name} connect() not implemented - skeleton only")
        self._connected = True

    def disconnect(self) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"{self.broker_name} disconnect() not implemented - skeleton only")
        self._connected = False
