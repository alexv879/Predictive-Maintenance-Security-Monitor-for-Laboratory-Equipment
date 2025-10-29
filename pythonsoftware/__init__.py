"""
PREMONITOR - Predictive Maintenance Monitoring System
Core package for AI-powered equipment monitoring on Raspberry Pi.
"""

__version__ = "1.0.0"
__author__ = "PREMONITOR Team"

# Expose key components for easier imports
from . import config
from . import equipment_registry
from .equipment_registry import (
    get_equipment_by_pi,
    get_equipment_by_id,
    get_equipment_thresholds,
    validate_equipment_config
)

__all__ = [
    'config',
    'equipment_registry',
    'get_equipment_by_pi',
    'get_equipment_by_id',
    'get_equipment_thresholds',
    'validate_equipment_config',
]
