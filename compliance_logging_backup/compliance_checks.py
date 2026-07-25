"""
Zero Tolerance Compliance Checks
ตรวจสอบและบันทึกทุกปัญหาทันทีพบ
"""

import json
from pathlib import Path
from typing import Dict, Any, List

# Avoid circular import
try:
    import logging
except ImportError:
    logging = None

from logging.compliance_logger import compliance_logger

class ComplianceChecker:
    """ตรวจสอบ Zero Tolerance compliance ทุกครั้งที่มีปัญหา"""
    
    def __init__(self):
        self.logger = None
        if logging:
            self.logger = logging.getLogger("COMPLIANCE_CHECKER")
        self.violations_count = 0
    
    def check_config_violations(self, config_file: str) -> Dict[str, Any]:
        """ตรวจสอบ configuration violations"""
        violations = []
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Check retry mechanisms
            if "data_feed" in config:
                data_feed = config["data_feed"]
                
                # Check data_adapter retry
                if "data_adapter" in data_feed:
                    data_adapter = data_feed["data_adapter"]
                    retry_attempts = data_adapter.get("retry_attempts", 0)
                    retry_delay = data_adapter.get("retry_delay", 0)
                    
                    if retry_attempts > 0:
                        violations.append({
                            "type": "RETRY_ATTEMPTS",
                            "location": "data_adapter.retry_attempts",
                            "value": retry_attempts,
                            "expected": 0,
                            "message": "Retry attempts violate Zero Tolerance"
                        })
                        compliance_logger.log_retry_detection(
                            "data_adapter.retry_attempts",
                            {"retry_attempts": retry_attempts}
                        )
                    
                    if retry_delay > 0:
                        violations.append({
                            "type": "RETRY_DELAY",
                            "location": "data_adapter.retry_delay", 
                            "value": retry_delay,
                            "expected": 0,
                            "message": "Retry delay violates Zero Tolerance"
                        })
                        compliance_logger.log_retry_detection(
                            "data_adapter.retry_delay",
                            {"retry_delay": retry_delay}
                        )
                
                # Check iq_option_adapter retry
                if "iq_option_adapter" in data_feed:
                    iq_adapter = data_feed["iq_option_adapter"]
                    connection_retries = iq_adapter.get("connection_retries", 0)
                    
                    if connection_retries > 0:
                        violations.append({
                            "type": "CONNECTION_RETRIES",
                            "location": "iq_option_adapter.connection_retries",
                            "value": connection_retries,
                            "expected": 0,
                            "message": "Connection retries violate Zero Tolerance"
                        })
                        compliance_logger.log_retry_detection(
                            "iq_option_adapter.connection_retries",
                            {"connection_retries": connection_retries}
                        )
            
            # Check fallback systems
            self._check_fallback_systems(config, violations)
            
            # Check mock data
            self._check_mock_data(config, violations)
            
        except Exception as e:
            violations.append({
                "type": "CONFIG_LOAD_ERROR",
                "location": config_file,
                "value": str(e),
                "message": f"Failed to load config: {e}"
            })
            compliance_logger.log_violation("CONFIG_LOAD_ERROR", {
                "file": config_file,
                "error": str(e)
            })
        
        # Log results
        checks = {
            "no_retry_mechanisms": len([v for v in violations if "RETRY" in v["type"]]) == 0,
            "no_fallback_systems": len([v for v in violations if "FALLBACK" in v["type"]]) == 0,
            "no_mock_data": len([v for v in violations if "MOCK" in v["type"]]) == 0,
            "config_loaded": len(violations) == 0 or not any("CONFIG_LOAD" in v["type"] for v in violations)
        }
        
        compliance_logger.log_configuration_check(config_file, checks)
        
        return {
            "violations": violations,
            "checks": checks,
            "passed": len(violations) == 0
        }
    
    def _check_fallback_systems(self, config: Dict[str, Any], violations: List[Dict]):
        """ตรวจสอบ fallback systems"""
        # Check for fallback_to_traditional
        if "ai_mode" in config and "fallback_to_traditional" in config["ai_mode"]:
            if config["ai_mode"]["fallback_to_traditional"]:
                violations.append({
                    "type": "FALLBACK_TO_TRADITIONAL",
                    "location": "ai_mode.fallback_to_traditional",
                    "value": True,
                    "expected": False,
                    "message": "Fallback to traditional AI violates Zero Tolerance"
                })
                compliance_logger.log_fallback_detection(
                    "ai_mode.fallback_to_traditional",
                    {"fallback_to_traditional": True}
                )
    
    def _check_mock_data(self, config: Dict[str, Any], violations: List[Dict]):
        """ตรวจสอบ mock data usage"""
        # Check for any mock or synthetic data configurations
        mock_keywords = ["mock", "synthetic", "fallback", "backup", "alternative"]
        
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(keyword in key.lower() for keyword in mock_keywords):
                        violations.append({
                            "type": "MOCK_DATA_CONFIG",
                            "location": current_path,
                            "value": value,
                            "message": f"Mock data configuration found at {current_path}"
                        })
                        compliance_logger.log_mock_data_detection(current_path, {key: value})
                    check_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    check_recursive(item, current_path)
        
        check_recursive(config)
    
    def check_code_violations(self, file_path: str, content: str) -> List[Dict]:
        """ตรวจสอบ code violations ในไฟล์"""
        violations = []
        
        # Check for retry mechanisms in code
        retry_patterns = [
            "retry_attempts",
            "retry_delay", 
            "connection_retries",
            "try:",
            "except:",
            "finally:",
            "raise",
            "return False",
            "continue"
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Check retry patterns
            if any(pattern in line_lower for pattern in retry_patterns if pattern != "try:" and pattern != "except:" and pattern != "finally:" and pattern != "raise"):
                if "retry" in line_lower:
                    violations.append({
                        "type": "CODE_RETRY",
                        "file": file_path,
                        "line": i,
                        "content": line.strip(),
                        "message": "Retry mechanism found in code"
                    })
                    compliance_logger.log_violation("CODE_RETRY", {
                        "file": file_path,
                        "line": i,
                        "content": line.strip()
                    })
        
        return violations
    
    def log_immediate_stop(self, reason: str, details: Dict[str, Any]):
        """บันทึกการ stop ทันที"""
        compliance_logger.log_immediate_stop(reason, details)
        
        # Update violation count
        self.violations_count += 1
        
        if self.logger:
            self.logger.critical(f"IMMEDIATE STOP #{self.violations_count}: {reason}")
            self.logger.critical(f"Stop details: {details}")
        else:
            print(f"CRITICAL: IMMEDIATE STOP #{self.violations_count}: {reason}")
            print(f"Stop details: {details}")
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """สรุป compliance status"""
        return {
            "total_violations": self.violations_count,
            "compliant": self.violations_count == 0,
            "status": "COMPLIANT" if self.violations_count == 0 else "VIOLATIONS_FOUND"
        }

# Global compliance checker instance
compliance_checker = ComplianceChecker()