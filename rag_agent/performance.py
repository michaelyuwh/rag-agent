"""
Performance utilities for RAG Agent.
Handles caching, monitoring, and optimization.
"""

import time
import functools
import logging
import psutil
import threading
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_gb: float
    response_time_ms: float
    operation: str
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    """Monitors system performance and operation metrics."""
    
    def __init__(self, metrics_file: str = "data/performance_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(exist_ok=True)
        self.metrics = []
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from file."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    # Keep only last 1000 metrics to prevent file bloat
                    self.metrics = data[-1000:]
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            self.metrics = []
    
    def _save_metrics(self):
        """Save metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump([asdict(m) for m in self.metrics], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def record_operation(self, operation: str, start_time: float, success: bool = True, error: str = None):
        """Record performance metrics for an operation."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Create metrics record
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / (1024 * 1024),
                disk_usage_gb=disk.used / (1024 * 1024 * 1024),
                response_time_ms=response_time_ms,
                operation=operation,
                success=success,
                error_message=error
            )
            
            # Add to metrics list
            self.metrics.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
            
            # Save periodically
            if len(self.metrics) % 10 == 0:
                threading.Thread(target=self._save_metrics, daemon=True).start()
            
            # Log slow operations
            if response_time_ms > 5000:  # > 5 seconds
                logger.warning(f"Slow operation: {operation} took {response_time_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {"message": "No metrics available"}
        
        # Recent metrics (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m.timestamp) > recent_cutoff
        ]
        
        if not recent_metrics:
            recent_metrics = self.metrics[-10:]  # Last 10 if no recent
        
        # Calculate statistics
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
        max_response_time = max(m.response_time_ms for m in recent_metrics)
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        
        # Operation breakdown
        operations = {}
        for m in recent_metrics:
            if m.operation not in operations:
                operations[m.operation] = {'count': 0, 'avg_time': 0, 'success_rate': 0}
            operations[m.operation]['count'] += 1
        
        # Calculate per-operation stats
        for op in operations:
            op_metrics = [m for m in recent_metrics if m.operation == op]
            operations[op]['avg_time'] = sum(m.response_time_ms for m in op_metrics) / len(op_metrics)
            operations[op]['success_rate'] = sum(1 for m in op_metrics if m.success) / len(op_metrics) * 100
        
        return {
            "total_operations": len(recent_metrics),
            "avg_response_time_ms": round(avg_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2),
            "success_rate_percent": round(success_rate, 2),
            "avg_cpu_percent": round(avg_cpu, 2),
            "avg_memory_percent": round(avg_memory, 2),
            "operations": operations,
            "time_period": "Last hour" if len(recent_metrics) > 10 else "Recent operations"
        }

class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self.cache:
                item = self.cache[key]
                # Check if expired
                if time.time() > item['expires']:
                    del self.cache[key]
                    return None
                return item['value']
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self.cache[key] = {
                'value': value,
                'expires': time.time() + ttl,
                'created': time.time()
            }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, item in self.cache.items():
                if current_time > item['expires']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(len(str(item['value'])) for item in self.cache.values())
            return {
                "total_keys": len(self.cache),
                "estimated_size_bytes": total_size,
                "oldest_entry": min((item['created'] for item in self.cache.values()), default=0)
            }

def performance_monitor(operation: str):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                # Record metrics
                monitor.record_operation(operation, start_time, success, error_msg)
        
        return wrapper
    return decorator

def cache_result(key_func: Callable = None, ttl: int = 3600):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        return wrapper
    return decorator

# Global instances
monitor = PerformanceMonitor()
cache = SimpleCache()

# Background cleanup thread
def _cleanup_thread():
    """Background thread for cache cleanup."""
    while True:
        try:
            time.sleep(300)  # Clean every 5 minutes
            expired_count = cache.cleanup_expired()
            if expired_count > 0:
                logger.debug(f"Cleaned up {expired_count} expired cache entries")
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")

# Start cleanup thread
_thread = threading.Thread(target=_cleanup_thread, daemon=True)
_thread.start()
