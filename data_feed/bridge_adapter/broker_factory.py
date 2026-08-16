"""
Broker Factory

Orchestrates the selection and instantiation of the correct broker adapter
based on configuration.
"""
import logging
from typing import Dict, Any

from data_feed.bridge_adapter.abstract_class import IDataSource
from data_feed.bridge_adapter.bridge_iq_adapter.bridge_iq_adapter import IQOptionAdapter
from data_feed.bridge_adapter.bridge_quotex_adapter.bridge_quotex_adapter import QuotexAdapter
from data_feed.bridge_adapter.bridge_pocket_adapter.bridge_pocket_adapter import PocketAdapter

logger = logging.getLogger(__name__)

class BrokerFactory:
    @staticmethod
    def create_broker(config: Dict[str, Any]) -> IDataSource:
        """Create broker adapter based on configuration.
        
        Args:
            config: Configuration dictionary containing active_broker setting
            
        Returns:
            IDataSource: Broker adapter instance
            
        Raises:
            ValueError: If broker is unknown and no fallback is configured
        """
        # Default to IQ_OPTION if not specified or missing
        active_broker = "IQ_OPTION"  # Default fallback
        if "active_broker" in config and config["active_broker"]:
            active_broker = str(config["active_broker"]).upper()
        
        logger.info(f"[BrokerFactory] Initializing broker adapter for: {active_broker}")
        
        if active_broker == "IQ_OPTION":
            return IQOptionAdapter(config=config)
        elif active_broker == "QUOTEX":
            return QuotexAdapter(config=config)
        elif active_broker == "POCKET_OPTION":
            return PocketAdapter(config=config)
        else:
            logger.error(f"[BrokerFactory] Unknown broker '{active_broker}' - must configure valid broker")
            raise ValueError(f"Unknown broker '{active_broker}'. Supported: IQ_OPTION, QUOTEX, POCKET_OPTION")
