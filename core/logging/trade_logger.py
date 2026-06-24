"""
Trade Logger - บันทึกข้อมูลการเทรดเป็น snapshot
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger("TradeLogger")

class TradeLogger:
    """
    บันทึกข้อมูลการเทรดลงไฟล์ snapshot
    """
    
    def __init__(self, logs_dir: str = "logs/process", indicator_store: Optional[Any] = None):
        """
        Args:
            logs_dir: ไดเรกทอรีสำหรับบันทึกไฟล์ log
            indicator_store: Instance of IndicatorStore for fetching indicator payloads
        """
        self.process_logs_dir = Path(logs_dir)
        self.process_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Store reference to indicator_store
        self.indicator_store = indicator_store
    
    def save_indicator_snapshot(self, symbol: str) -> Optional[str]:
        """
        Fetch the full indicator payload from indicator_store and save it as JSON.
        
        Args:
            symbol: Trading pair symbol (e.g., 'EURUSD')
            
        Returns:
            Path to the saved file, or None if failed
        """
        if self.indicator_store is None:
            logger.error("indicator_store not set. Cannot save indicator snapshot.")
            return None
        
        try:
            # Fetch the full payload from indicator_store
            payload = self.indicator_store.get_payload(symbol)
            
            if not payload:
                logger.warning(f"No payload data found for {symbol}")
                return None
            
            # Generate filename with current timestamp
            now = datetime.now(timezone.utc)
            filename = f"indicator_{now.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.process_logs_dir / filename
            
            # Ensure the payload is JSON serializable
            def convert_to_serializable(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Series):
                    return obj.tolist()
                elif isinstance(obj, pd.DataFrame):
                    return obj.to_dict(orient='records')
                elif isinstance(obj, dict):
                    return {k: convert_to_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_to_serializable(item) for item in obj]
                else:
                    return obj
            
            # Clean the payload for JSON serialization
            cleaned_payload = convert_to_serializable(payload)
            
            # Add metadata to the payload
            snapshot_data = {
                "symbol": symbol,
                "timestamp": now.isoformat(timespec='seconds') + 'Z',
                "payload": cleaned_payload
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Indicator snapshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save indicator snapshot for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
