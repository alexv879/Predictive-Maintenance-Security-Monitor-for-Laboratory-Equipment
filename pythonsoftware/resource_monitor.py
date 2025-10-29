"""
Resource monitoring utilities for PREMONITOR.
Tracks CPU, memory, and provides performance metrics.
"""

import psutil
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger('resource_monitor')


@dataclass
class ResourceSnapshot:
    """Snapshot of system resource usage at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    process_threads: int

    def __str__(self) -> str:
        return (f"CPU: {self.cpu_percent:.1f}% | "
                f"RAM: {self.memory_mb:.1f}MB ({self.memory_percent:.1f}%) | "
                f"Threads: {self.process_threads}")


class ResourceMonitor:
    """
    Monitors system resource usage for the PREMONITOR process.
    Provides memory/CPU tracking and alerts if limits are exceeded.
    """

    def __init__(self,
                 memory_limit_mb: float = 115.0,
                 cpu_limit_percent: float = 5.0):
        """
        Initialize resource monitor.

        Args:
            memory_limit_mb: Alert if memory usage exceeds this (MB)
            cpu_limit_percent: Alert if CPU usage exceeds this (%)
        """
        self.process = psutil.Process()
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self.baseline: Optional[ResourceSnapshot] = None
        self.snapshots = []

    def capture_snapshot(self) -> ResourceSnapshot:
        """Capture current resource usage."""
        mem_info = self.process.memory_info()

        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=self.process.cpu_percent(interval=0.1),
            memory_mb=mem_info.rss / (1024 * 1024),
            memory_percent=self.process.memory_percent(),
            process_threads=self.process.num_threads()
        )

        self.snapshots.append(snapshot)

        # Keep only last 100 snapshots
        if len(self.snapshots) > 100:
            self.snapshots.pop(0)

        return snapshot

    def set_baseline(self):
        """Set current resource usage as baseline."""
        self.baseline = self.capture_snapshot()
        logger.info(f"Baseline set: {self.baseline}")

    def check_limits(self) -> Dict[str, bool]:
        """
        Check if resource usage exceeds configured limits.

        Returns:
            Dict with 'memory_ok' and 'cpu_ok' booleans
        """
        current = self.capture_snapshot()

        results = {
            'memory_ok': current.memory_mb <= self.memory_limit_mb,
            'cpu_ok': current.cpu_percent <= self.cpu_limit_percent,
            'current': current
        }

        if not results['memory_ok']:
            logger.warning(f"Memory limit exceeded: {current.memory_mb:.1f}MB > {self.memory_limit_mb}MB")

        if not results['cpu_ok']:
            logger.warning(f"CPU limit exceeded: {current.cpu_percent:.1f}% > {self.cpu_limit_percent}%")

        return results

    def get_stats(self) -> Dict[str, float]:
        """Get aggregate statistics from collected snapshots."""
        if not self.snapshots:
            return {}

        cpu_values = [s.cpu_percent for s in self.snapshots]
        mem_values = [s.memory_mb for s in self.snapshots]

        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': sum(mem_values) / len(mem_values),
            'memory_max': max(mem_values),
            'memory_min': min(mem_values),
            'samples': len(self.snapshots)
        }

    def log_stats(self):
        """Log aggregate statistics."""
        stats = self.get_stats()
        if stats:
            logger.info(
                f"Resource Stats (n={stats['samples']}): "
                f"CPU avg={stats['cpu_avg']:.1f}% max={stats['cpu_max']:.1f}% | "
                f"MEM avg={stats['memory_avg']:.1f}MB max={stats['memory_max']:.1f}MB"
            )


# Global instance for easy access
_monitor = None


def get_monitor() -> ResourceMonitor:
    """Get global resource monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
