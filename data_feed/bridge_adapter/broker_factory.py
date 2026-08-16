"""
Broker Factory Module
สร้างและจัดการ Broker Adapter instances
"""
import logging
from typing import Dict, Type, Optional

from ..brokers import (
    BaseBrokerAdapter,
    IQOptionAdapter,
    QuotexAdapter,
    PocketOptionAdapter,
)
from ..exceptions import DataFeedError

logger = logging.getLogger(__name__)


class BrokerFactory:
    """
    Factory สำหรับสร้างและจัดการ Broker Adapter instances
    
    Usage:
        factory = BrokerFactory()
        adapter = factory.get_adapter('iq', config)
    """
    
    _adapters: Dict[str, Type[BaseBrokerAdapter]] = {
        'iq': IQOptionAdapter,
        'iqoption': IQOptionAdapter,
        'iq_option': IQOptionAdapter,
        'quotex': QuotexAdapter,
        'pocket': PocketOptionAdapter,
        'pocketoption': PocketOptionAdapter,
        'pocket_option': PocketOptionAdapter,
    }
    
    def __init__(self):
        self._instances: Dict[str, BaseBrokerAdapter] = {}
        self._config_cache: Dict[str, dict] = {}
    
    def get_adapter(
        self, 
        broker_name: str, 
        config: Optional[dict] = None,
        force_new: bool = False
    ) -> BaseBrokerAdapter:
        """
        สร้างหรือดึง Broker Adapter instance
        
        Args:
            broker_name: ชื่อ broker ('iq', 'quotex', 'pocket')
            config: การตั้งค่า broker
            force_new: ถ้า True จะสร้าง instance ใหม่เสมอ
            
        Returns:
            Broker Adapter instance
            
        Raises:
            DataFeedError: ถ้าไม่พบชื่อ broker หรือเกิดข้อผิดพลาด
        """
        broker_key = broker_name.lower().strip()
        
        # ตรวจสอบว่ามี adapter นี้รองรับหรือไม่
        if broker_key not in self._adapters:
            supported = list(set(k for k in self._adapters.keys() if '_' not in k))
            raise DataFeedError(
                f"Unknown broker: {broker_name}. "
                f"Supported brokers: {supported}"
            )
        
        # ใช้ singleton pattern สำหรับแต่ละ broker (ยกเว้น force_new=True)
        if not force_new and broker_key in self._instances:
            logger.debug(f"Reusing existing {broker_key} adapter")
            return self._instances[broker_key]
        
        # หา adapter class
        adapter_class = self._adapters[broker_key]
        
        # ใช้ config ที่ส่งมา หรือ config ที่ cache ไว้
        if config is None:
            config = self._config_cache.get(broker_key, {})
        else:
            self._config_cache[broker_key] = config
        
        try:
            logger.info(f"Creating {broker_key} adapter...")
            adapter = adapter_class(config)
            self._instances[broker_key] = adapter
            logger.info(f"{broker_key} adapter created successfully")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create {broker_key} adapter: {e}")
            raise DataFeedError(f"Failed to initialize {broker_name} adapter: {e}")
    
    def get_all_adapters(self) -> Dict[str, BaseBrokerAdapter]:
        """
        ดึง adapters ทั้งหมดที่สร้างไว้แล้ว
        
        Returns:
            Dictionary ของ {broker_name: adapter}
        """
        return self._instances.copy()
    
    def close_all(self):
        """
        ปิดการเชื่อมต่อทั้งหมดและล้าง cache
        """
        logger.info("Closing all broker connections...")
        
        for name, adapter in self._instances.items():
            try:
                if hasattr(adapter, 'close'):
                    adapter.close()
                logger.info(f"{name} connection closed")
            except Exception as e:
                logger.error(f"Error closing {name} connection: {e}")
        
        self._instances.clear()
        logger.info("All broker connections closed")
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[BaseBrokerAdapter]):
        """
        Register adapter class ใหม่ (สำหรับ extension)
        
        Args:
            name: ชื่อ broker
            adapter_class: Adapter class ที่จะ register
        """
        cls._adapters[name.lower()] = adapter_class
        logger.info(f"Registered adapter: {name}")
    
    @classmethod
    def get_supported_brokers(cls) -> list:
        """
        ดึงรายชื่อ brokers ที่รองรับ
        
        Returns:
            List ของ broker names
        """
        return list(set(k for k in cls._adapters.keys() if '_' not in k))
