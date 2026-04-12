# deployment/network_security.py
import time
import hashlib
import ipaddress
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
import threading


@dataclass
class ConnectionInfo:
    """Connection information for security tracking"""
    ip_address: str
    port: int
    user_agent: str
    connection_time: float
    last_activity: float
    requests_count: int
    bytes_sent: int
    bytes_received: int
    is_blocked: bool = False
    block_reason: str = ""
    block_until: float = 0.0


@dataclass
class SecurityEvent:
    """Security event for logging and alerting"""
    event_type: str
    severity: str  # low, medium, high, critical
    source_ip: str
    timestamp: float
    description: str
    metadata: Dict = None


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests_per_minute: int = 100, max_burst: int = 10):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_burst = max_burst
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed to make request"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        with self.lock:
            # Clean old requests
            while (self.requests[ip_address] and 
                   self.requests[ip_address][0] < minute_ago):
                self.requests[ip_address].popleft()
            
            # Check rate limit
            if len(self.requests[ip_address]) >= self.max_requests_per_minute:
                return False
            
            # Check burst limit
            if len(self.requests[ip_address]) >= self.max_burst:
                # Check if requests are too close together
                if len(self.requests[ip_address]) > 0:
                    last_request = self.requests[ip_address][-1]
                    if current_time - last_request < 1.0:  # Max 1 request per second
                        return False
            
            # Add current request
            self.requests[ip_address].append(current_time)
            return True
    
    def get_request_count(self, ip_address: str, window_seconds: int = 60) -> int:
        """Get request count for IP in time window"""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        with self.lock:
            return sum(1 for req_time in self.requests[ip_address] if req_time >= window_start)


class ConnectionManager:
    """Manages network connections with security controls"""
    
    def __init__(self, max_connections: int = 1000, max_connections_per_ip: int = 10):
        self.max_connections = max_connections
        self.max_connections_per_ip = max_connections_per_ip
        self.connections: Dict[str, ConnectionInfo] = {}
        self.ip_connection_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # Security thresholds
        self.max_bytes_per_connection = 100 * 1024 * 1024  # 100MB
        self.max_connection_age = 3600  # 1 hour
        self.suspicious_activity_threshold = 1000  # requests
    
    def add_connection(self, ip_address: str, port: int, user_agent: str = "") -> bool:
        """Add new connection if allowed"""
        with self.lock:
            # Check global connection limit
            if len(self.connections) >= self.max_connections:
                return False
            
            # Check per-IP connection limit
            if self.ip_connection_counts[ip_address] >= self.max_connections_per_ip:
                return False
            
            # Create connection info
            connection = ConnectionInfo(
                ip_address=ip_address,
                port=port,
                user_agent=user_agent,
                connection_time=time.time(),
                last_activity=time.time(),
                requests_count=0,
                bytes_sent=0,
                bytes_received=0
            )
            
            self.connections[f"{ip_address}:{port}"] = connection
            self.ip_connection_counts[ip_address] += 1
            
            return True
    
    def remove_connection(self, ip_address: str, port: str):
        """Remove connection"""
        connection_key = f"{ip_address}:{port}"
        
        with self.lock:
            if connection_key in self.connections:
                del self.connections[connection_key]
                self.ip_connection_counts[ip_address] -= 1
                
                if self.ip_connection_counts[ip_address] <= 0:
                    del self.ip_connection_counts[ip_address]
    
    def update_activity(self, ip_address: str, port: str, bytes_sent: int = 0, bytes_received: int = 0):
        """Update connection activity"""
        connection_key = f"{ip_address}:{port}"
        
        with self.lock:
            if connection_key in self.connections:
                connection = self.connections[connection_key]
                connection.last_activity = time.time()
                connection.requests_count += 1
                connection.bytes_sent += bytes_sent
                connection.bytes_received += bytes_received
    
    def block_ip(self, ip_address: str, reason: str, duration_seconds: int = 3600):
        """Block an IP address"""
        block_until = time.time() + duration_seconds
        
        with self.lock:
            # Block all connections from this IP
            for connection_key, connection in list(self.connections.items()):
                if connection.ip_address == ip_address:
                    connection.is_blocked = True
                    connection.block_reason = reason
                    connection.block_until = block_until
        
        print(f"Blocked IP {ip_address} for {duration_seconds}s: {reason}")
    
    def cleanup_expired_connections(self):
        """Clean up expired connections"""
        current_time = time.time()
        expired_connections = []
        
        with self.lock:
            for connection_key, connection in list(self.connections.items()):
                # Check if connection is expired
                if (current_time - connection.connection_time > self.max_connection_age or
                    (connection.is_blocked and current_time > connection.block_until)):
                    expired_connections.append(connection_key)
                
                # Check for suspicious activity
                if (connection.bytes_sent > self.max_bytes_per_connection or
                    connection.bytes_received > self.max_bytes_per_connection or
                    connection.requests_count > self.suspicious_activity_threshold):
                    self.block_ip(connection.ip_address, "Suspicious activity", 7200)
        
        # Remove expired connections
        for connection_key in expired_connections:
            ip_address, port = connection_key.split(":")
            self.remove_connection(ip_address, port)
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        with self.lock:
            total_connections = len(self.connections)
            blocked_connections = sum(1 for conn in self.connections.values() if conn.is_blocked)
            unique_ips = len(self.ip_connection_counts)
            
            # Calculate activity metrics
            total_requests = sum(conn.requests_count for conn in self.connections.values())
            total_bytes_sent = sum(conn.bytes_sent for conn in self.connections.values())
            total_bytes_received = sum(conn.bytes_received for conn in self.connections.values())
            
            return {
                "total_connections": total_connections,
                "blocked_connections": blocked_connections,
                "unique_ips": unique_ips,
                "total_requests": total_requests,
                "total_bytes_sent": total_bytes_sent,
                "total_bytes_received": total_bytes_received,
                "average_requests_per_connection": total_requests / max(total_connections, 1)
            }


class DDoSProtection:
    """DDoS protection system"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests_per_minute=100)
        self.connection_manager = ConnectionManager()
        self.security_events: List[SecurityEvent] = []
        self.suspicious_ips: Set[str] = set()
        
        # DDoS detection thresholds
        self.ddos_request_threshold = 10000  # requests per minute globally
        self.ddos_ip_threshold = 1000  # requests per minute per IP
        self.ddos_connection_threshold = 500  # connections per minute
        
        self.global_request_count = 0
        self.global_request_window = deque()
        self.last_cleanup = time.time()
    
    def handle_request(self, ip_address: str, port: int, user_agent: str = "") -> Tuple[bool, str]:
        """Handle incoming request with DDoS protection"""
        current_time = time.time()
        
        # Cleanup old requests periodically
        if current_time - self.last_cleanup > 60:
            self._cleanup_old_requests()
            self.last_cleanup = current_time
        
        # Check if IP is blocked
        if ip_address in self.suspicious_ips:
            return False, "IP blocked due to suspicious activity"
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(ip_address):
            self._create_security_event(
                "rate_limit_exceeded",
                "medium",
                ip_address,
                f"Rate limit exceeded for {ip_address}"
            )
            return False, "Rate limit exceeded"
        
        # Check connection limits
        if not self.connection_manager.add_connection(ip_address, port, user_agent):
            self._create_security_event(
                "connection_limit_exceeded",
                "medium",
                ip_address,
                f"Connection limit exceeded for {ip_address}"
            )
            return False, "Connection limit exceeded"
        
        # Update global request tracking
        self.global_request_count += 1
        self.global_request_window.append(current_time)
        
        # Check for DDoS patterns
        if self._detect_ddos_pattern(ip_address):
            return False, "DDoS pattern detected"
        
        return True, "Request allowed"
    
    def update_request_stats(self, ip_address: str, port: int, bytes_sent: int = 0, bytes_received: int = 0):
        """Update request statistics"""
        self.connection_manager.update_activity(ip_address, port, bytes_sent, bytes_received)
    
    def _detect_ddos_pattern(self, ip_address: str) -> bool:
        """Detect DDoS attack patterns"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Check global request rate
        recent_global_requests = sum(1 for req_time in self.global_request_window if req_time >= minute_ago)
        if recent_global_requests > self.ddos_request_threshold:
            self._create_security_event(
                "global_ddos_detected",
                "high",
                ip_address,
                f"Global DDoS detected: {recent_global_requests} requests/minute"
            )
            return True
        
        # Check per-IP request rate
        ip_requests = self.rate_limiter.get_request_count(ip_address)
        if ip_requests > self.ddos_ip_threshold:
            self._create_security_event(
                "ip_ddos_detected",
                "high",
                ip_address,
                f"IP-based DDoS detected: {ip_requests} requests/minute"
            )
            self.connection_manager.block_ip(ip_address, "DDoS attack", 7200)
            self.suspicious_ips.add(ip_address)
            return True
        
        return False
    
    def _cleanup_old_requests(self):
        """Clean up old request data"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Clean global request window
        while (self.global_request_window and 
               self.global_request_window[0] < hour_ago):
            self.global_request_window.popleft()
        
        # Clean rate limiter data
        self.rate_limiter.requests.clear()
        
        # Clean connection manager
        self.connection_manager.cleanup_expired_connections()
    
    def _create_security_event(self, event_type: str, severity: str, source_ip: str, description: str, metadata: Dict = None):
        """Create security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            timestamp=time.time(),
            description=description,
            metadata=metadata or {}
        )
        
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]
        
        print(f"[SECURITY] {severity.upper()}: {description}")
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        return {
            "global_requests_per_minute": len(self.global_request_window),
            "blocked_ips": len(self.suspicious_ips),
            "security_events_count": len(self.security_events),
            "connection_stats": self.connection_manager.get_connection_stats(),
            "recent_events": [
                {
                    "type": event.event_type,
                    "severity": event.severity,
                    "source_ip": event.source_ip,
                    "timestamp": event.timestamp,
                    "description": event.description
                }
                for event in self.security_events[-10:]
            ]
        }


class NetworkSecurity:
    """Main network security coordinator"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ddos_protection = DDoSProtection()
        self.allowed_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.whitelist_enabled = self.config.get("whitelist_enabled", False)
        self.blacklist_enabled = self.config.get("blacklist_enabled", True)
        
        # Initialize IP lists
        self._initialize_ip_lists()
    
    def _initialize_ip_lists(self):
        """Initialize allowed and blocked IP lists"""
        # Default allowed IPs (localhost)
        self.allowed_ips.update(["127.0.0.1", "::1", "0.0.0.0"])
        
        # Add configured allowed IPs
        if "allowed_ips" in self.config:
            self.allowed_ips.update(self.config["allowed_ips"])
        
        # Add configured blocked IPs
        if "blocked_ips" in self.config:
            self.blocked_ips.update(self.config["blocked_ips"])
        
        # Load blocked IP ranges (known malicious IPs)
        self._load_malicious_ip_ranges()
    
    def _load_malicious_ip_ranges(self):
        """Load known malicious IP ranges"""
        # Example malicious IP ranges (would be loaded from threat intelligence)
        malicious_ranges = [
            "192.0.2.0/24",    # TEST-NET-1
            "198.51.100.0/24", # TEST-NET-2
            "203.0.113.0/24",  # TEST-NET-3
        ]
        
        for range_str in malicious_ranges:
            try:
                network = ipaddress.ip_network(range_str, strict=False)
                for ip in network.hosts():
                    self.blocked_ips.add(str(ip))
            except ValueError:
                continue
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed"""
        # Check blacklist first
        if self.blacklist_enabled and ip_address in self.blocked_ips:
            return False
        
        # Check whitelist if enabled
        if self.whitelist_enabled and ip_address not in self.allowed_ips:
            return False
        
        return True
    
    def handle_connection(self, ip_address: str, port: int, user_agent: str = "") -> Tuple[bool, str]:
        """Handle new connection with full security checks"""
        # Basic IP filtering
        if not self.is_ip_allowed(ip_address):
            return False, "IP not allowed"
        
        # DDoS protection
        return self.ddos_protection.handle_request(ip_address, port, user_agent)
    
    def block_ip(self, ip_address: str, reason: str, duration_seconds: int = 3600):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        self.ddos_protection.connection_manager.block_ip(ip_address, reason, duration_seconds)
        self.ddos_protection.suspicious_ips.add(ip_address)
    
    def allow_ip(self, ip_address: str):
        """Allow an IP address"""
        self.blocked_ips.discard(ip_address)
        self.ddos_protection.suspicious_ips.discard(ip_address)
        self.allowed_ips.add(ip_address)
    
    def get_security_status(self) -> Dict:
        """Get comprehensive security status"""
        return {
            "allowed_ips_count": len(self.allowed_ips),
            "blocked_ips_count": len(self.blocked_ips),
            "whitelist_enabled": self.whitelist_enabled,
            "blacklist_enabled": self.blacklist_enabled,
            "ddos_stats": self.ddos_protection.get_security_stats()
        }
    
    def export_security_events(self, filename: str, duration_hours: int = 24):
        """Export security events to file"""
        cutoff_time = time.time() - (duration_hours * 3600)
        recent_events = [
            event for event in self.ddos_protection.security_events
            if event.timestamp >= cutoff_time
        ]
        
        events_data = {
            "export_time": time.time(),
            "duration_hours": duration_hours,
            "events": [
                {
                    "timestamp": event.timestamp,
                    "type": event.event_type,
                    "severity": event.severity,
                    "source_ip": event.source_ip,
                    "description": event.description,
                    "metadata": event.metadata
                }
                for event in recent_events
            ]
        }
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(events_data, f, indent=2)
            print(f"Security events exported to {filename}")
        except Exception as e:
            print(f"Error exporting events: {e}")


# Utility functions
def create_security_config() -> Dict:
    """Create default security configuration"""
    return {
        "whitelist_enabled": False,
        "blacklist_enabled": True,
        "allowed_ips": ["127.0.0.1", "::1"],
        "blocked_ips": [],
        "rate_limiting": {
            "max_requests_per_minute": 100,
            "max_burst": 10
        },
        "connection_limits": {
            "max_connections": 1000,
            "max_connections_per_ip": 10
        },
        "ddos_thresholds": {
            "global_requests_per_minute": 10000,
            "ip_requests_per_minute": 1000,
            "connections_per_minute": 500
        }
    }


def initialize_security(config: Dict = None) -> NetworkSecurity:
    """Initialize network security with configuration"""
    security_config = config or create_security_config()
    
    print("Initializing network security...")
    print(f"  Whitelist enabled: {security_config['whitelist_enabled']}")
    print(f"  Blacklist enabled: {security_config['blacklist_enabled']}")
    print(f"  Allowed IPs: {len(security_config['allowed_ips'])}")
    print(f"  Blocked IPs: {len(security_config['blocked_ips'])}")
    
    security = NetworkSecurity(security_config)
    
    print("Network security initialized")
    return security
