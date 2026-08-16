"""
Broker Adapters Package
รวมทุก Broker Adapter ที่รองรับ
"""
from .base_adapter import BaseBrokerAdapter
from .iq_adapter import IQOptionAdapter
from .quotex_adapter import QuotexAdapter
from .pocket_adapter import PocketOptionAdapter

__all__ = [
    'BaseBrokerAdapter',
    'IQOptionAdapter',
    'QuotexAdapter',
    'PocketOptionAdapter',
]


def get_broker_adapter(broker_name: str, config: dict) -> BaseBrokerAdapter:
    """
    Factory function สำหรับสร้าง Broker Adapter
    
    Args:
        broker_name: ชื่อ broker ('iq', 'quotex', 'pocket')
        config: การตั้งค่า
        
    Returns:
        Broker Adapter instance
        
    Raises:
        ValueError: ถ้าไม่พบชื่อ broker
    """
    adapters = {
        'iq': IQOptionAdapter,
        'quotex': QuotexAdapter,
        'pocket': PocketOptionAdapter,
    }
    
    broker_lower = broker_name.lower()
    
    if broker_lower not in adapters:
        raise ValueError(
            f"Unknown broker: {broker_name}. "
            f"Supported brokers: {list(adapters.keys())}"
        )
    
    return adapters[broker_lower](config)
