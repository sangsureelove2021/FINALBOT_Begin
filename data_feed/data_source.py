
"""
data_feed/data_source.py

กำหนด Abstract Base Class (ABC) สำหรับเป็น Interface มาตรฐานของแหล่งข้อมูล (Data Source)
ไฟล์นี้ทำหน้าที่เป็นสัญญา (Contract) ให้ Adapter ที่จะสร้างขึ้นมาทั้งหมด
ต้องมีเมธอดตามที่กำหนดไว้ เพื่อให้ส่วนอื่นของระบบเรียกใช้งานได้ในรูปแบบเดียวกัน
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Any, List, Dict

class IDataSource(ABC):
    """
    Interface สำหรับ Data Source กำหนดเมธอดมาตรฐานที่ต้องมีในทุก Adapter
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with configuration from datafeed_config.json
        
        Args:
            config (Dict[str, Any]): Configuration from get_data_source_config()
        """
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        """
        สร้างการเชื่อมต่อเริ่มต้นไปยังแหล่งข้อมูล
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """
        ยกเลิกการเชื่อมต่อจากแหล่งข้อมูล
        """
        raise NotImplementedError

    @abstractmethod
    async def start_stream(self, symbol: str, timeframe: int, callback: Callable[[Dict[str, Any]], asyncio.Future]) -> None:
        """
        เริ่มต้นการสตรีมข้อมูลราคาสำหรับสินทรัพย์และ Timeframe ที่กำหนด
        
        Args:
            symbol (str): ชื่อย่อของสินทรัพย์ เช่น 'EURUSD'
            timeframe (int): ขนาดแท่งเทียนเป็นวินาที เช่น 60 สำหรับ 1 นาที
            callback (Callable): ฟังก์ชันที่จะถูกเรียกเมื่อมีข้อมูลใหม่เข้ามา
        """
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """
        ตรวจสอบสถานะการเชื่อมต่อ
        
        Returns:
            bool: คืนค่า True หากเชื่อมต่ออยู่, มิฉะนั้นเป็น False
        """
        raise NotImplementedError

    @abstractmethod
    async def get_historical_candles(self, symbol: str, timeframe: int, count: int, end_time: float) -> List[Dict[str, Any]]:
        """
        (Optional) ดึงข้อมูลแท่งเทียนย้อนหลัง
        หมายเหตุ: ในโปรเจกต์นี้ ฟังก์ชันนี้อาจไม่ถูกใช้งานตามข้อกำหนด
        แต่ใส่ไว้เพื่อความสมบูรณ์ของ Interface
        """
        # ตามข้อกำหนดที่ห้ามดึงข้อมูลย้อนหลัง เราจะคืนค่าว่างเสมอ
        return []

