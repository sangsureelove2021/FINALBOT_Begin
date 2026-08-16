"""
Base Broker Adapter Interface
กำหนดมาตรฐานกลางสำหรับทุก Broker Adapter
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime


class BaseBrokerAdapter(ABC):
    """คลาสพื้นฐานที่ทุก Broker ต้องสืบทอด"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected = False
        self._symbol_map: Dict[str, str] = {}  # Map symbol ของเรา -> symbol ของ broker
        
    @abstractmethod
    def connect(self) -> bool:
        """เชื่อมต่อไปยัง Broker"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """ตัดการเชื่อมต่อ"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """ตรวจสอบสถานะการเชื่อมต่อ"""
        pass
    
    @abstractmethod
    def get_server_timestamp(self) -> int:
        """ดึงเวลาปัจจุบันจาก Server ของ Broker (epoch milliseconds)"""
        pass
    
    @abstractmethod
    def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int, 
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """
        ดึงข้อมูลแท่งเทียน
        
        Args:
            symbol: ชื่อคู่เงิน (เช่น 'EURUSD')
            timeframe: เวลาของแท่ง (เช่น 'M1', 'M5')
            count: จำนวนแท่งที่ต้องการ
            end_time: เวลาสิ้นสุด (epoch ms) ถ้า None คือปัจจุบัน
            
        Returns:
            DataFrame ที่มี columns: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def subscribe_price(self, symbol: str, callback: callable) -> bool:
        """สมัครสมาชิกเพื่อรับราคา Real-time"""
        pass
    
    @abstractmethod
    def unsubscribe_price(self, symbol: str) -> bool:
        """ยกเลิกการรับราคา Real-time"""
        pass
    
    def map_symbol(self, our_symbol: str) -> str:
        """แปลงชื่อสัญลักษณ์ของเรา เป็นชื่อของ Broker"""
        return self._symbol_map.get(our_symbol, our_symbol)
    
    def validate_response(self, data: Any) -> bool:
        """ตรวจสอบความถูกต้องของข้อมูลที่รับมา"""
        if data is None:
            return False
        if isinstance(data, pd.DataFrame):
            return not data.empty
        return True
