# deployment/monitoring.py
import time
import json
import threading
import logging
import psutil
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import queue


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class Alert:
    """Alert data"""
    alert_name: str
    severity: str  # info, warning, critical
    message: str
    timestamp: float
    resolved: bool = False
    resolved_timestamp: Optional[float] = None


class MetricsCollector:
    """Collects and stores metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: Dict[str, deque] = {}
        self.lock = threading.Lock()
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            
            metric = Metric(
                name=name,
                value=self.counters[key],
                timestamp=time.time(),
                labels=labels or {}
            )
            
            self._add_metric(key, metric)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            )
            
            self._add_metric(key, metric)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            )
            
            self._add_metric(key, metric)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key from name and labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_metric(self, key: str, metric: Metric):
        """Add metric to storage"""
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=self.max_metrics)
        
        self.metrics[key].append(metric)
    
    def get_metrics(self, name: str = None, since: float = None) -> List[Metric]:
        """Get metrics by name and time range"""
        with self.lock:
            if name:
                keys = [k for k in self.metrics.keys() if k.startswith(name)]
            else:
                keys = list(self.metrics.keys())
            
            result = []
            for key in keys:
                for metric in self.metrics[key]:
                    if since is None or metric.timestamp >= since:
                        result.append(metric)
            
            return sorted(result, key=lambda m: m.timestamp)
    
    def get_metric_summary(self, name: str, duration_seconds: int = 300) -> Dict:
        """Get metric summary for recent time period"""
        since = time.time() - duration_seconds
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "duration_seconds": duration_seconds
        }


class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
        self.interval = 15  # seconds
    
    def start_monitoring(self):
        """Start system monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(self.interval)
            except Exception as e:
                print(f"System monitoring error: {e}")
                time.sleep(self.interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.set_gauge("system_cpu_percent", cpu_percent)
        
        cpu_count = psutil.cpu_count()
        self.metrics.set_gauge("system_cpu_count", cpu_count)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics.set_gauge("system_memory_percent", memory.percent)
        self.metrics.set_gauge("system_memory_used_bytes", memory.used)
        self.metrics.set_gauge("system_memory_available_bytes", memory.available)
        self.metrics.set_gauge("system_memory_total_bytes", memory.total)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.metrics.set_gauge("system_disk_percent", (disk.used / disk.total) * 100)
        self.metrics.set_gauge("system_disk_used_bytes", disk.used)
        self.metrics.set_gauge("system_disk_free_bytes", disk.free)
        self.metrics.set_gauge("system_disk_total_bytes", disk.total)
        
        # Network metrics
        network = psutil.net_io_counters()
        self.metrics.set_gauge("system_network_bytes_sent", network.bytes_sent)
        self.metrics.set_gauge("system_network_bytes_recv", network.bytes_recv)
        self.metrics.set_gauge("system_network_packets_sent", network.packets_sent)
        self.metrics.set_gauge("system_network_packets_recv", network.packets_recv)
        
        # Process metrics
        process = psutil.Process()
        self.metrics.set_gauge("process_cpu_percent", process.cpu_percent())
        self.metrics.set_gauge("process_memory_percent", process.memory_percent())
        self.metrics.set_gauge("process_memory_rss_bytes", process.memory_info().rss)
        self.metrics.set_gauge("process_memory_vms_bytes", process.memory_info().vms)
        self.metrics.set_gauge("process_num_threads", process.num_threads())
        self.metrics.set_gauge("process_num_fds", process.num_fds() if hasattr(process, 'num_fds') else 0)


class BlockchainMonitor:
    """Blockchain-specific monitoring"""
    
    def __init__(self, blockchain, metrics_collector: MetricsCollector):
        self.blockchain = blockchain
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
        self.interval = 30  # seconds
    
    def start_monitoring(self):
        """Start blockchain monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Blockchain monitoring started")
    
    def stop_monitoring(self):
        """Stop blockchain monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Blockchain monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_blockchain_metrics()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Blockchain monitoring error: {e}")
                time.sleep(self.interval)
    
    def _collect_blockchain_metrics(self):
        """Collect blockchain metrics"""
        # Chain metrics
        chain_length = len(self.blockchain.chain)
        self.metrics.set_gauge("blockchain_height", chain_length)
        
        # Mempool metrics
        mempool_size = len(self.blockchain.mempool.transactions)
        self.metrics.set_gauge("mempool_size", mempool_size)
        
        # UTXO metrics
        utxo_size = len(self.blockchain.utxo.utxos)
        self.metrics.set_gauge("utxo_size", utxo_size)
        
        # Difficulty metrics
        if hasattr(self.blockchain, 'get_difficulty'):
            difficulty = self.blockchain.get_difficulty()
            self.metrics.set_gauge("blockchain_difficulty", difficulty)
        
        # Block time metrics
        if len(self.blockchain.chain) > 1:
            latest_block = self.blockchain.chain[-1]
            previous_block = self.blockchain.chain[-2]
            block_time = latest_block.timestamp - previous_block.timestamp
            self.metrics.record_histogram("block_time_seconds", block_time)
        
        # Transaction metrics
        total_transactions = sum(len(block.transactions) for block in self.blockchain.chain)
        self.metrics.set_gauge("blockchain_total_transactions", total_transactions)


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict] = []
        self.alert_callbacks: List[Callable] = []
        self.alert_queue = queue.Queue()
        self.monitoring = False
        self.monitor_thread = None
        
        # Default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            {
                "name": "high_cpu_usage",
                "metric": "system_cpu_percent",
                "condition": "gt",
                "threshold": 80.0,
                "severity": "warning",
                "duration": 300,  # 5 minutes
                "message": "CPU usage is {value:.1f}% (threshold: {threshold}%)"
            },
            {
                "name": "high_memory_usage",
                "metric": "system_memory_percent",
                "condition": "gt",
                "threshold": 85.0,
                "severity": "warning",
                "duration": 300,
                "message": "Memory usage is {value:.1f}% (threshold: {threshold}%)"
            },
            {
                "name": "high_disk_usage",
                "metric": "system_disk_percent",
                "condition": "gt",
                "threshold": 90.0,
                "severity": "critical",
                "duration": 60,
                "message": "Disk usage is {value:.1f}% (threshold: {threshold}%)"
            },
            {
                "name": "blockchain_height_stalled",
                "metric": "blockchain_height",
                "condition": "eq",
                "threshold": None,  # Check if value hasn't changed
                "severity": "warning",
                "duration": 600,  # 10 minutes
                "message": "Blockchain height has not changed for {duration}s"
            },
            {
                "name": "large_mempool",
                "metric": "mempool_size",
                "condition": "gt",
                "threshold": 5000,
                "severity": "info",
                "duration": 60,
                "message": "Mempool size is {value} (threshold: {threshold})"
            }
        ]
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start alert monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Alert monitoring started")
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Alert monitoring stopped")
    
    def _monitor_loop(self):
        """Main alert monitoring loop"""
        while self.monitoring:
            try:
                self._check_alert_rules()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Alert monitoring error: {e}")
                time.sleep(30)
    
    def _check_alert_rules(self):
        """Check all alert rules"""
        current_time = time.time()
        
        for rule in self.alert_rules:
            try:
                self._check_rule(rule, current_time)
            except Exception as e:
                print(f"Error checking rule {rule['name']}: {e}")
    
    def _check_rule(self, rule: Dict, current_time: float):
        """Check individual alert rule"""
        metric_name = rule["metric"]
        condition = rule["condition"]
        threshold = rule["threshold"]
        duration = rule["duration"]
        
        # Get recent metrics
        since = current_time - duration
        recent_metrics = self.metrics.get_metrics(metric_name, since)
        
        if not recent_metrics:
            return
        
        latest_metric = recent_metrics[-1]
        latest_value = latest_metric.value
        
        # Check condition
        triggered = False
        
        if condition == "gt" and threshold is not None:
            triggered = latest_value > threshold
        elif condition == "lt" and threshold is not None:
            triggered = latest_value < threshold
        elif condition == "eq" and threshold is None:
            # Check if value hasn't changed during duration
            if len(recent_metrics) > 1:
                first_value = recent_metrics[0].value
                triggered = first_value == latest_value
        
        # Handle alert state
        alert_key = rule["name"]
        
        if triggered and alert_key not in self.alerts:
            # Create new alert
            alert = Alert(
                alert_name=alert_key,
                severity=rule["severity"],
                message=rule["message"].format(
                    value=latest_value,
                    threshold=threshold,
                    duration=duration
                ),
                timestamp=current_time
            )
            
            self.alerts[alert_key] = alert
            self.alert_queue.put(alert)
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Alert callback error: {e}")
        
        elif not triggered and alert_key in self.alerts:
            # Resolve alert
            alert = self.alerts[alert_key]
            alert.resolved = True
            alert.resolved_timestamp = current_time
            
            # Trigger resolution callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Alert resolution callback error: {e}")
            
            # Remove from active alerts after delay
            del self.alerts[alert_key]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        return list(self.alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        # This would typically read from a persistent store
        # For now, return active alerts
        return self.get_active_alerts()[:limit]


class HealthChecker:
    """Health check system"""
    
    def __init__(self, blockchain, metrics_collector: MetricsCollector):
        self.blockchain = blockchain
        self.metrics = metrics_collector
        self.health_checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, Dict] = {}
        
        # Setup default health checks
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Setup default health checks"""
        self.health_checks = {
            "blockchain": self._check_blockchain_health,
            "mempool": self._check_mempool_health,
            "utxo": self._check_utxo_health,
            "system": self._check_system_health,
            "database": self._check_database_health
        }
    
    def _check_blockchain_health(self) -> Dict:
        """Check blockchain health"""
        try:
            chain_length = len(self.blockchain.chain)
            
            # Check if chain is not empty
            if chain_length == 0:
                return {"status": "unhealthy", "reason": "Empty blockchain"}
            
            # Check latest block
            latest_block = self.blockchain.chain[-1]
            time_since_last_block = time.time() - latest_block.timestamp
            
            if time_since_last_block > 3600:  # 1 hour
                return {
                    "status": "unhealthy",
                    "reason": f"No blocks for {time_since_last_block:.0f} seconds"
                }
            
            return {
                "status": "healthy",
                "chain_length": chain_length,
                "time_since_last_block": time_since_last_block
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}
    
    def _check_mempool_health(self) -> Dict:
        """Check mempool health"""
        try:
            mempool_size = len(self.blockchain.mempool.transactions)
            
            if mempool_size > 10000:
                return {
                    "status": "warning",
                    "reason": f"Large mempool: {mempool_size} transactions"
                }
            
            return {
                "status": "healthy",
                "mempool_size": mempool_size
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}
    
    def _check_utxo_health(self) -> Dict:
        """Check UTXO health"""
        try:
            utxo_size = len(self.blockchain.utxo.utxos)
            
            return {
                "status": "healthy",
                "utxo_size": utxo_size
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}
    
    def _check_system_health(self) -> Dict:
        """Check system health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 95 or memory_percent > 95:
                return {
                    "status": "unhealthy",
                    "reason": f"High resource usage: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%"
                }
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent
            }
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}
    
    def _check_database_health(self) -> Dict:
        """Check database health"""
        try:
            # Simple check - try to access blockchain data
            _ = len(self.blockchain.chain)
            _ = len(self.blockchain.utxo.utxos)
            
            return {"status": "healthy"}
            
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}
    
    def run_health_checks(self) -> Dict:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.health_checks.items():
            try:
                result = check_func()
                results[check_name] = result
                
                if result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                elif result["status"] == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                results[check_name] = {"status": "unhealthy", "reason": str(e)}
                overall_status = "unhealthy"
        
        self.last_check_results = {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": time.time()
        }
        
        return self.last_check_results
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return self.last_check_results


class MonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self, blockchain, config: Dict = None):
        self.config = config or {}
        self.blockchain = blockchain
        
        # Initialize components
        self.metrics = MetricsCollector(max_metrics=10000)
        self.system_monitor = SystemMonitor(self.metrics)
        self.blockchain_monitor = BlockchainMonitor(blockchain, self.metrics)
        self.alert_manager = AlertManager(self.metrics)
        self.health_checker = HealthChecker(blockchain, self.metrics)
        
        # Setup logging
        self._setup_logging()
        
        print("Monitoring system initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get("log_level", "INFO")
        log_file = self.config.get("log_file", "/var/log/worldwidecoin/monitoring.log")
        
        # Create log directory
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("worldwidecoin.monitoring")
    
    def start(self):
        """Start all monitoring components"""
        print("Starting monitoring system...")
        
        self.system_monitor.start_monitoring()
        self.blockchain_monitor.start_monitoring()
        self.alert_manager.start_monitoring()
        
        # Setup default alert callback
        self.alert_manager.add_alert_callback(self._handle_alert)
        
        print("Monitoring system started")
    
    def stop(self):
        """Stop all monitoring components"""
        print("Stopping monitoring system...")
        
        self.system_monitor.stop_monitoring()
        self.blockchain_monitor.stop_monitoring()
        self.alert_manager.stop_monitoring()
        
        print("Monitoring system stopped")
    
    def _handle_alert(self, alert: Alert):
        """Handle alert notifications"""
        if not alert.resolved:
            self.logger.warning(f"ALERT: {alert.severity.upper()} - {alert.message}")
        else:
            self.logger.info(f"ALERT RESOLVED: {alert.alert_name}")
    
    def get_metrics_summary(self) -> Dict:
        """Get comprehensive metrics summary"""
        summary = {
            "timestamp": time.time(),
            "system_metrics": {},
            "blockchain_metrics": {},
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "health_status": self.health_checker.get_health_status()
        }
        
        # System metrics
        system_metrics = [
            "system_cpu_percent",
            "system_memory_percent",
            "system_disk_percent"
        ]
        
        for metric_name in system_metrics:
            summary["system_metrics"][metric_name] = self.metrics.get_metric_summary(metric_name)
        
        # Blockchain metrics
        blockchain_metrics = [
            "blockchain_height",
            "mempool_size",
            "utxo_size",
            "block_time_seconds"
        ]
        
        for metric_name in blockchain_metrics:
            summary["blockchain_metrics"][metric_name] = self.metrics.get_metric_summary(metric_name)
        
        return summary
    
    def export_metrics(self, filename: str, duration_hours: int = 24):
        """Export metrics to file"""
        since = time.time() - (duration_hours * 3600)
        all_metrics = self.metrics.get_metrics(since=since)
        
        metrics_data = {
            "export_time": time.time(),
            "duration_hours": duration_hours,
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "timestamp": metric.timestamp,
                    "labels": metric.labels
                }
                for metric in all_metrics
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            print(f"Metrics exported to {filename}")
        except Exception as e:
            print(f"Error exporting metrics: {e}")


def create_monitoring_system(blockchain, config: Dict = None) -> MonitoringSystem:
    """Create and initialize monitoring system"""
    monitoring_config = config or {
        "log_level": "INFO",
        "log_file": "/var/log/worldwidecoin/monitoring.log"
    }
    
    print("Creating monitoring system...")
    
    monitoring = MonitoringSystem(blockchain, monitoring_config)
    
    print("Monitoring system created")
    return monitoring
