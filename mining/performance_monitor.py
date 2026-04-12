# mining/performance_monitor.py
import time
import threading
import psutil
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MiningMetrics:
    """Mining performance metrics data structure"""
    timestamp: float
    hash_rate: float
    cpu_usage: float
    memory_usage: float
    temperature: float
    power_usage: float
    blocks_found: int
    efficiency: float  # hashes per watt
    difficulty: int


class PerformanceMonitor:
    """Real-time mining performance monitoring"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.monitoring = False
        self.metrics_history: List[MiningMetrics] = []
        self.current_metrics = None
        
        # System monitoring
        self.process = psutil.Process()
        self.max_history_size = 1000
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # Alert if CPU > 80%
        self.temp_threshold = 70.0  # Alert if temp > 70°C
        self.memory_threshold = 80.0  # Alert if memory > 80%
        
        # Callbacks for alerts
        self.alert_callbacks = []
        
        # Monitoring thread
        self.monitor_thread = None
        self.lock = threading.Lock()
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("📊 Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("📊 Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                
                with self.lock:
                    self.current_metrics = metrics
                    self.metrics_history.append(metrics)
                    
                    # Limit history size
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                # Check for alerts
                self._check_alerts(metrics)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(self.update_interval)
    
    def _collect_metrics(self) -> MiningMetrics:
        """Collect current performance metrics"""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Process-specific metrics
        process_cpu = self.process.cpu_percent()
        process_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Temperature (if available)
        temperature = self._get_temperature()
        
        # Power usage (estimated)
        power_usage = self._estimate_power_usage(cpu_usage)
        
        # Hash rate (will be updated by miner)
        hash_rate = getattr(self, '_current_hash_rate', 0.0)
        blocks_found = getattr(self, '_blocks_found', 0)
        difficulty = getattr(self, '_current_difficulty', 1)
        
        # Efficiency
        efficiency = hash_rate / power_usage if power_usage > 0 else 0.0
        
        return MiningMetrics(
            timestamp=time.time(),
            hash_rate=hash_rate,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            temperature=temperature,
            power_usage=power_usage,
            blocks_found=blocks_found,
            efficiency=efficiency,
            difficulty=difficulty
        )
    
    def _get_temperature(self) -> float:
        """Get system temperature if available"""
        try:
            # Try to get temperature from psutil
            temps = psutil.sensors_temperatures()
            if temps:
                # Average all available temperature sensors
                all_temps = []
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            all_temps.append(entry.current)
                
                if all_temps:
                    return sum(all_temps) / len(all_temps)
        except:
            pass
        
        return 0.0  # Temperature not available
    
    def _estimate_power_usage(self, cpu_usage: float) -> float:
        """Estimate power usage based on CPU usage"""
        # Simple estimation: base power + CPU-dependent power
        base_power = 50.0  # Base system power in watts
        cpu_power = (cpu_usage / 100.0) * 65.0  # Max 65W for CPU
        
        return base_power + cpu_power
    
    def _check_alerts(self, metrics: MiningMetrics):
        """Check for performance alerts"""
        alerts = []
        
        if metrics.cpu_usage > self.cpu_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.memory_threshold:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.temperature > self.temp_threshold and metrics.temperature > 0:
            alerts.append(f"High temperature: {metrics.temperature:.1f}°C")
        
        if metrics.hash_rate == 0 and self.monitoring:
            alerts.append("Mining hash rate is zero")
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert, metrics)
                except:
                    pass
    
    def update_mining_stats(self, hash_rate: float, blocks_found: int, difficulty: int):
        """Update mining-specific statistics"""
        self._current_hash_rate = hash_rate
        self._blocks_found = blocks_found
        self._current_difficulty = difficulty
    
    def add_alert_callback(self, callback):
        """Add callback for performance alerts"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[MiningMetrics]:
        """Get current performance metrics"""
        with self.lock:
            return self.current_metrics
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[MiningMetrics]:
        """Get metrics history for specified duration"""
        cutoff_time = time.time() - (duration_minutes * 60)
        
        with self.lock:
            return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_performance_summary(self, duration_minutes: int = 60) -> Dict:
        """Get performance summary for specified duration"""
        history = self.get_metrics_history(duration_minutes)
        
        if not history:
            return {}
        
        # Calculate statistics
        hash_rates = [m.hash_rate for m in history]
        cpu_usages = [m.cpu_usage for m in history]
        memory_usages = [m.memory_usage for m in history]
        temperatures = [m.temperature for m in history if m.temperature > 0]
        power_usages = [m.power_usage for m in history]
        efficiencies = [m.efficiency for m in history if m.efficiency > 0]
        
        summary = {
            "duration_minutes": duration_minutes,
            "sample_count": len(history),
            "hash_rate": {
                "current": hash_rates[-1] if hash_rates else 0,
                "average": sum(hash_rates) / len(hash_rates) if hash_rates else 0,
                "maximum": max(hash_rates) if hash_rates else 0,
                "minimum": min(hash_rates) if hash_rates else 0
            },
            "cpu_usage": {
                "average": sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
                "maximum": max(cpu_usages) if cpu_usages else 0
            },
            "memory_usage": {
                "average": sum(memory_usages) / len(memory_usages) if memory_usages else 0,
                "maximum": max(memory_usages) if memory_usages else 0
            }
        }
        
        if temperatures:
            summary["temperature"] = {
                "average": sum(temperatures) / len(temperatures),
                "maximum": max(temperatures),
                "minimum": min(temperatures)
            }
        
        if power_usages:
            summary["power_usage"] = {
                "average": sum(power_usages) / len(power_usages),
                "maximum": max(power_usages),
                "total_kwh": (sum(power_usages) / 1000) * (duration_minutes / 60)
            }
        
        if efficiencies:
            summary["efficiency"] = {
                "average": sum(efficiencies) / len(efficiencies),
                "maximum": max(efficiencies)
            }
        
        return summary
    
    def export_metrics(self, filename: str, duration_minutes: int = 60):
        """Export metrics to JSON file"""
        history = self.get_metrics_history(duration_minutes)
        
        # Convert to serializable format
        data = {
            "export_time": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "metrics": [asdict(m) for m in history]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"📁 Metrics exported to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def print_realtime_stats(self):
        """Print real-time statistics"""
        metrics = self.get_current_metrics()
        if not metrics:
            return
        
        print(f"\r⛏️ Hash Rate: {metrics.hash_rate:.0f} H/s | "
              f"CPU: {metrics.cpu_usage:.1f}% | "
              f"Memory: {metrics.memory_usage:.1f}% | "
              f"Temp: {metrics.temperature:.1f}°C | "
              f"Power: {metrics.power_usage:.1f}W | "
              f"Efficiency: {metrics.efficiency:.1f} H/W", end="", flush=True)


class MiningOptimizer:
    """Mining optimization based on performance metrics"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.optimization_history = []
        self.last_optimization = 0
    
    def optimize_mining_parameters(self, current_threads: int, current_difficulty: int) -> Dict:
        """Suggest optimal mining parameters"""
        metrics = self.monitor.get_performance_summary(duration_minutes=10)
        
        if not metrics:
            return {"threads": current_threads, "difficulty": current_difficulty}
        
        suggestions = {}
        
        # Optimize thread count based on CPU usage
        avg_cpu = metrics.get("cpu_usage", {}).get("average", 0)
        if avg_cpu > 90:
            suggestions["threads"] = max(1, current_threads - 1)
            suggestions["reason"] = "High CPU usage, reducing threads"
        elif avg_cpu < 50 and current_threads < psutil.cpu_count():
            suggestions["threads"] = current_threads + 1
            suggestions["reason"] = "Low CPU usage, can increase threads"
        else:
            suggestions["threads"] = current_threads
            suggestions["reason"] = "Thread count optimal"
        
        # Optimize based on efficiency
        efficiency = metrics.get("efficiency", {}).get("average", 0)
        if efficiency > 0:
            suggestions["efficiency"] = efficiency
            suggestions["status"] = "good" if efficiency > 10 else "poor"
        
        return suggestions
    
    def should_adjust_difficulty(self, current_difficulty: int) -> bool:
        """Determine if difficulty adjustment is needed"""
        metrics = self.monitor.get_performance_summary(duration_minutes=30)
        
        if not metrics:
            return False
        
        avg_hash_rate = metrics.get("hash_rate", {}).get("average", 0)
        
        # If hash rate is very low, might need difficulty adjustment
        if avg_hash_rate < 100:  # Less than 100 H/s
            return True
        
        return False


def default_alert_handler(alert: str, metrics: MiningMetrics):
    """Default alert handler"""
    timestamp = datetime.fromtimestamp(metrics.timestamp).strftime("%H:%M:%S")
    print(f"\n⚠️ [{timestamp}] {alert}")


if __name__ == "__main__":
    # Test performance monitoring
    monitor = PerformanceMonitor(update_interval=2.0)
    monitor.add_alert_callback(default_alert_handler)
    
    try:
        monitor.start_monitoring()
        
        # Simulate mining stats
        for i in range(10):
            monitor.update_mining_stats(
                hash_rate=1000 + i * 100,
                blocks_found=i // 5,
                difficulty=3
            )
            time.sleep(2)
        
        # Print summary
        summary = monitor.get_performance_summary(duration_minutes=1)
        print(f"\n📊 Performance Summary:")
        print(f"   Average Hash Rate: {summary.get('hash_rate', {}).get('average', 0):.0f} H/s")
        print(f"   Average CPU Usage: {summary.get('cpu_usage', {}).get('average', 0):.1f}%")
        print(f"   Average Memory Usage: {summary.get('memory_usage', {}).get('average', 0):.1f}%")
        
    finally:
        monitor.stop_monitoring()
