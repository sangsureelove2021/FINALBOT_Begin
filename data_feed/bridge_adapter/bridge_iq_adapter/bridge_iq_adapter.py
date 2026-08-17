"""
IQ Option Data Feed Adapter (Facade / Coordinator)

Provides a unified interface conforming to IDataSource by coordinating
IQConnectionManager, IQRestFetcher, and IQStreamManager.
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd

from data_feed.bridge_adapter.abstract_class import IDataSource
from .connection import IQConnectionManager
from .rest_fetcher import IQRestFetcher
from .stream_manager import IQStreamManager

logger = logging.getLogger(__name__)


class IQOptionAdapter(IDataSource):
    """
    IQ Option Adapter coordinating connection, REST fetcher, and stream manager.
    Conforms to IDataSource interface.
    """

    def __init__(self, email: Optional[str] = None,
                 password: Optional[str] = None,
                 account_type: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize IQ Option adapter facade.
        """
        self.connection_manager = IQConnectionManager(
            email=email,
            password=password,
            account_type=account_type,
            config=config
        )
        self.rest_fetcher = IQRestFetcher(
            timeout_sec=self.connection_manager.timeout_sec,
            max_workers=self.connection_manager.max_workers
        )
        self.stream_manager = IQStreamManager(
            timeout_sec=self.connection_manager.timeout_sec
        )
        logger.info("[IQOPTION] IQOptionAdapter facade initialized successfully")

    @property
    def connected(self) -> bool:
        """Returns True if the adapter is connected to the broker."""
        return self.connection_manager.connected

    @property
    def api(self) -> Any:
        """Access underlying API instance."""
        return self.connection_manager.api

    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connection_manager.is_connected()

    def ensure_connected(self) -> None:
        """Reconnect check if the websocket dropped."""
        self.connection_manager.ensure_connected()

    def connect(self) -> None:
        """Connect to broker."""
        self.connection_manager.connect()

    def disconnect(self) -> None:
        """Disconnect from broker."""
        self.connection_manager.disconnect()

    def get_balance(self) -> float:
        """Get account balance."""
        return self.connection_manager.get_balance()

    def get_server_timestamp(self) -> float:
        """Get broker server timestamp."""
        return self.connection_manager.get_server_timestamp()

    def get_candles(self, symbol: str, timeframe: str = 'M1',
                    count: int = 250, end_time: Optional[Any] = None) -> pd.DataFrame:
        """
        Fetch historical candles via REST API.
        """
        self.ensure_connected()
        return self.rest_fetcher.fetch_candles(
            api=self.connection_manager.api,
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            end_time=end_time
        )

    def get_multi_timeframe(self, symbol: str,
                            timeframes: Optional[List[str]] = None,
                            count: int = 250) -> Dict[str, pd.DataFrame]:
        """
        Fetch candles for multiple timeframes sequentially.
        """
        if timeframes is None:
            timeframes = ['M1', 'M5']
        
        result: Dict[str, pd.DataFrame] = {}
        for tf in timeframes:
            result[tf] = self.get_candles(symbol, timeframe=tf, count=count)
        return result

    def start_stream(self, symbol: str, timeframe: str = 'M1', count: int = 250) -> None:
        """
        Start WebSocket candle streaming.
        """
        self.ensure_connected()
        self.stream_manager.start_stream(
            api=self.connection_manager.api,
            symbol=symbol,
            timeframe=timeframe,
            count=count
        )

    def update_with_streaming(self, symbol: str, timeframe: str = 'M1', count: int = 250) -> pd.DataFrame:
        """
        Get latest candles from WebSocket cache.
        """
        self.ensure_connected()
        return self.stream_manager.update_with_streaming(
            api=self.connection_manager.api,
            symbol=symbol,
            timeframe=timeframe,
            count=count
        )

    def get_symbols(self) -> List[str]:
        """Get list of active trading symbols from configuration."""
        from config_setting.config_loader import get_symbols
        return get_symbols()

    def get_open_symbols(self, target_symbols: Optional[List[str]] = None) -> List[str]:
        """
        Check and return list of open/tradable symbols from the broker matching target_symbols.
        """
        self.ensure_connected()
        if target_symbols is None:
            target_symbols = self.get_symbols()

        if not target_symbols:
            logger.warning("[IQOPTION] No target symbols provided or configured.")
            return []

        open_asset_names: set[str] = set()

        # 1. Query get_all_init_v2() for fast, comprehensive active asset status
        try:
            init_v2 = self.api.get_all_init_v2()
            if isinstance(init_v2, dict):
                for cat in ["turbo", "binary", "digital", "cfd", "forex", "crypto"]:
                    cat_data = init_v2.get(cat, {})
                    if isinstance(cat_data, dict):
                        actives = cat_data.get("actives", {})
                        if isinstance(actives, dict):
                            for _, active_info in actives.items():
                                if isinstance(active_info, dict):
                                    is_enabled = bool(active_info.get("enabled", False))
                                    is_suspended = bool(active_info.get("is_suspended", False))
                                    raw_name = str(active_info.get("name", ""))
                                    if "." in raw_name:
                                        sym_clean = raw_name.split(".", 1)[1]
                                    else:
                                        sym_clean = raw_name
                                    if is_enabled and not is_suspended:
                                        open_asset_names.add(sym_clean.strip().upper())
        except Exception as e:
            logger.warning(f"[IQOPTION] get_all_init_v2() check encountered issue: {e}")

        # 2. Supplement with get_all_open_time() if available / needed
        if not open_asset_names:
            try:
                open_time_data = self.api.get_all_open_time()
                if isinstance(open_time_data, dict):
                    for category, assets in open_time_data.items():
                        if isinstance(assets, dict):
                            for sym_name, status in assets.items():
                                if isinstance(status, dict) and status.get("open") is True:
                                    open_asset_names.add(str(sym_name).strip().upper())
            except Exception as e:
                logger.warning(f"[IQOPTION] get_all_open_time() query failed: {e}")

        def normalize_sym(s: str) -> str:
            return s.replace("/", "").replace("_", "").replace(" ", "").upper()

        normalized_open_map: Dict[str, str] = {normalize_sym(name): name for name in open_asset_names}

        verified_open_symbols: List[str] = []
        for target in target_symbols:
            target_clean = str(target).strip()
            target_norm = normalize_sym(target_clean)
            if target_clean.upper() in open_asset_names or target_norm in normalized_open_map:
                verified_open_symbols.append(target_clean)
                logger.info(f"[IQOPTION] Asset {target_clean} is verified OPEN on broker")
            else:
                logger.warning(f"[IQOPTION] Asset {target_clean} is currently CLOSED on broker")

        return verified_open_symbols
