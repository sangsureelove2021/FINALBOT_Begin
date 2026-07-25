"""
Zero Tolerance Logging System
บันทึกทุกปัญหาทุกการเออเร่อ ตามมาตรฐาน Boss's Zero Tolerance
"""

# Import compliance_logger without triggering initialization compliance_checker = None

try:
    from .compliance_logger import compliance_logger
except ImportError:
    compliance_logger = None

__all__ = ['compliance_logger']