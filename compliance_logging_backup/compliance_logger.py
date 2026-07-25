"""
Zero Tolerance Compliance Logger
บันทึกทุกปัญหา ทุกการเออเรอ ตามมาตรฐาน Boss's Zero Tolerance
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Fix circular import by using different module name
sys.modules['logging'] = sys.modules.pop('__main__') if '__main__' in sys.modules and 'logging' in sys.modules['__main__'].__dict__ else None

try:
    import logging as logging_module
except ImportError:
    logging_module = None
import sys

class ComplianceLogger:
    """Logger สำหรับ Zero Tolerance compliance tracking"""
    
    def __init__(self, log_file: str = "all_filelogs/compliance.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger (avoid circular import with logging module)
        self.logger = None
        try:
            import logging
            self.logger = logging.getLogger("COMPLIANCE")
            self.logger.setLevel(logging.INFO)
            
            # File handler
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Console handler for critical errors
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        except Exception as e:
            # Fallback to print if logging fails
            print(f"[COMPLIANCE] Logger initialization failed: {e}")
            self.logger = None
    
    def log_violation(self, violation_type: str, details: Dict[str, Any], 
                     severity: str = "CRITICAL"):
        """บันทฺกการละเมิด Zero Tolerance"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "violation_type": violation_type,
            "severity": severity,
            "details": details,
            "policy": "Zero Tolerance"
        }
        
        if self.logger:
            self.logger.error(f"VIOLATION: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            print(f"VIOLATION: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # บันทึกในรูปแบบ structured สำหรับ analysis
        violation_file = self.log_file.parent / f"violations_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(violation_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to write violation log: {e}")
            else:
                print(f"Failed to write violation log: {e}")
    
    def log_configuration_check(self, config_file: str, checks: Dict[str, Any]):
        """บันทึกการตรวจสอบ configuration"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "check_type": "CONFIGURATION",
            "config_file": config_file,
            "checks": checks,
            "status": "PASSED" if all(checks.values()) else "FAILED"
        }
        
        if all(checks.values()):
            self.logger.info(f"CONFIG CHECK PASSED: {config_file}")
        else:
            self.logger.error(f"CONFIG CHECK FAILED: {config_file}")
        
        # บันทึก detail
        detail_file = self.log_file.parent / "config_checks.json"
        try:
            with open(detail_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write config log: {e}")
    
    def log_retry_detection(self, location: str, retry_config: Dict[str, Any]):
        """บันทึกการพบ retry mechanism"""
        violation = {
            "location": location,
            "retry_config": retry_config,
            "violation": "RETRY_MECHANISM",
            "message": "Retry mechanisms violate Zero Tolerance policy"
        }
        
        self.log_violation("RETRY_MECHANISM", violation, "CRITICAL")
    
    def log_fallback_detection(self, location: str, fallback_config: Dict[str, Any]):
        """บันทึกการพบ fallback system"""
        violation = {
            "location": location,
            "fallback_config": fallback_config,
            "violation": "FALLBACK_SYSTEM",
            "message": "Fallback systems violate Zero Tolerance policy"
        }
        
        self.log_violation("FALLBACK_SYSTEM", violation, "CRITICAL")
    
    def log_mock_data_detection(self, location: str, mock_config: Dict[str, Any]):
        """บันทึกการพบ mock data"""
        violation = {
            "location": location,
            "mock_config": mock_config,
            "violation": "MOCK_DATA",
            "message": "Mock data violates Zero Tolerance policy"
        }
        
        self.log_violation("MOCK_DATA", violation, "CRITICAL")
    
    def log_immediate_stop(self, reason: str, details: Dict[str, Any]):
        """บันทึกการ stop ทันทีตาม Zero Tolerance"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "IMMEDIATE_STOP",
            "reason": reason,
            "details": details,
            "policy": "Zero Tolerance - No Retry, No Fallback"
        }
        
        self.logger.critical(f"IMMEDIATE STOP: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # บันทึกเหตุการณ์ stop
        stop_file = self.log_file.parent / "immediate_stops.json"
        try:
            with open(stop_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write stop log: {e}")
    
    def log_compliance_score(self, score: int, max_score: int, issues: list):
        """บันทึก compliance score"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "compliance_score": score,
            "max_score": max_score,
            "percentage": (score / max_score) * 100,
            "issues": issues,
            "status": "COMPLIANT" if score == max_score else "VIOLATIONS_FOUND"
        }
        
        self.logger.info(f"COMPLIANCE SCORE: {score}/{max_score} ({log_entry['percentage']:.1f}%)")
        
        # บันทึก score history
        score_file = self.log_file.parent / "compliance_scores.json"
        try:
            with open(score_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write score log: {e}")

# Global compliance logger instance
compliance_logger = ComplianceLogger()