"""
Anomaly Detector re-exporter for data_evaluate module.
Moved from data_feed to data_evaluate per system architecture.
"""

from data_evaluate.orchestration.anomaly_detector import AnomalyDetector

__all__ = ["AnomalyDetector"]
