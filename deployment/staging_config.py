# deployment/staging_config.py
import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from deployment.mainnet_config import NetworkConfig, SecurityConfig, DatabaseConfig, MonitoringConfig, DeploymentConfig


@dataclass
class StagingNetworkConfig:
    """Staging network configuration"""
    name: str = "WorldWideCoin Staging"
    network_id: int = 2  # Different from mainnet (1)
    genesis_timestamp: int = int(time.time())
    
    # Network parameters (different from mainnet)
    port: int = 18333  # Different port range
    rpc_port: int = 18332
    max_peers: int = 20  # Fewer peers for staging
    min_peers: int = 3
    
    # Mining parameters (faster for testing)
    initial_difficulty: int = 1  # Lower difficulty for faster mining
    target_block_time: float = 60.0  # 1 minute blocks instead of 10
    difficulty_window: int = 100  # Smaller window
    max_difficulty: int = 8  # Lower max difficulty
    
    # Economic parameters (same as mainnet)
    initial_reward: float = 50.0
    reward_halving_interval: int = 210000
    treasury_percent: float = 0.05
    fee_burn_percent: float = 0.5
    
    # Security parameters (smaller limits for staging)
    max_tx_size: int = 500000  # 500KB
    max_block_size: int = 2000000  # 2MB
    mempool_max_size: int = 1000  # Smaller mempool
    max_orphan_depth: int = 50


@dataclass
class StagingSecurityConfig:
    """Staging security configuration (more relaxed for testing)"""
    # Rate limiting (higher limits for staging)
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 1000  # Higher limit
    max_connections_per_ip: int = 20  # More connections per IP
    
    # DDoS protection (disabled for staging)
    ddos_protection: bool = False
    connection_timeout: int = 60
    max_message_size: int = 5000000  # 5MB
    
    # Authentication (disabled for staging)
    require_auth: bool = False
    api_key_required: bool = False
    allowed_ips: List[str] = None
    
    # Encryption (optional for staging)
    require_encryption: bool = False
    min_tls_version: str = "1.2"
    
    def __post_init__(self):
        if self.allowed_ips is None:
            # Allow all local and test IPs
            self.allowed_ips = ["127.0.0.1", "::1", "0.0.0.0", "10.0.0.0/8", "192.168.0.0/16"]


@dataclass
class StagingDatabaseConfig:
    """Staging database configuration"""
    # Use local paths for staging
    blockchain_db_type: str = "rocksdb"
    blockchain_db_path: str = "./data/staging/blockchain"
    
    utxo_db_type: str = "rocksdb"
    utxo_db_path: str = "./data/staging/utxo"
    
    mempool_db_type: str = "redis"
    mempool_db_host: str = "localhost"
    mempool_db_port: int = 6380  # Different port
    
    # Backup configuration (more frequent for staging)
    backup_enabled: bool = True
    backup_interval: int = 300  # 5 minutes
    backup_retention_days: int = 7  # Shorter retention
    backup_path: str = "./data/staging/backups"
    
    # Performance (smaller for staging)
    cache_size_mb: int = 256
    write_buffer_size_mb: int = 32
    max_open_files: int = 100


@dataclass
class StagingMonitoringConfig:
    """Staging monitoring configuration"""
    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 19090  # Different port
    metrics_interval: int = 10  # More frequent
    
    # Logging
    log_level: str = "DEBUG"  # More verbose for staging
    log_file: str = "./logs/staging/staging.log"
    log_rotation: bool = True
    log_max_size_mb: int = 50
    log_max_files: int = 5
    
    # Health checks
    health_check_enabled: bool = True
    health_check_interval: int = 15  # More frequent
    health_check_port: int = 18080  # Different port
    
    # Alerting (disabled for staging)
    alerting_enabled: bool = False
    alert_webhook_url: Optional[str] = None
    alert_email_smtp: Optional[str] = None
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 90.0,  # Higher threshold for staging
                "memory_usage": 95.0,
                "disk_usage": 95.0,
                "block_height_delay": 60,  # Longer delay
                "peer_count_min": 1  # Lower minimum
            }


@dataclass
class StagingDeploymentConfig:
    """Staging deployment configuration"""
    # Environment
    environment: str = "staging"
    region: str = "us-west-2"
    availability_zone: str = "us-west-2a"
    
    # Scaling (smaller for staging)
    min_instances: int = 1
    max_instances: int = 3
    desired_instances: int = 2
    
    # Resources (smaller for staging)
    cpu_units: int = 512
    memory_mb: int = 1024
    storage_gb: int = 20
    
    # Load balancing
    load_balancer_enabled: bool = True
    health_check_path: str = "/health"
    health_check_interval: int = 15
    
    # Auto-scaling (disabled for staging)
    auto_scaling_enabled: bool = False
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 20.0
    scale_cooldown: int = 300


class StagingConfig:
    """Staging environment configuration manager"""
    
    def __init__(self, config_file: str = "staging.json"):
        self.config_file = config_file
        self.network = StagingNetworkConfig()
        self.security = StagingSecurityConfig()
        self.database = StagingDatabaseConfig()
        self.monitoring = StagingMonitoringConfig()
        self.deployment = StagingDeploymentConfig()
        
        # Load configuration if exists
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update configurations
                if 'network' in data:
                    self.network = StagingNetworkConfig(**data['network'])
                if 'security' in data:
                    self.security = StagingSecurityConfig(**data['security'])
                if 'database' in data:
                    self.database = StagingDatabaseConfig(**data['database'])
                if 'monitoring' in data:
                    self.monitoring = StagingMonitoringConfig(**data['monitoring'])
                if 'deployment' in data:
                    self.deployment = StagingDeploymentConfig(**data['deployment'])
                
                print(f"Staging configuration loaded from {self.config_file}")
                
            except Exception as e:
                print(f"Error loading staging config: {e}")
                print("Using default staging configuration")
        else:
            print(f"Staging configuration file not found, using defaults")
    
    def save_config(self):
        """Save configuration to file"""
        config_data = {
            'network': asdict(self.network),
            'security': asdict(self.security),
            'database': asdict(self.database),
            'monitoring': asdict(self.monitoring),
            'deployment': asdict(self.deployment),
            'updated_at': time.time()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"Staging configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving staging config: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Network validation
        if self.network.port < 1024 or self.network.port > 65535:
            issues.append("Network port must be between 1024-65535")
        
        if self.network.max_peers < self.network.min_peers:
            issues.append("Max peers must be >= min peers")
        
        # Check for port conflicts with mainnet
        if self.network.port == 8333:
            issues.append("Port 8333 conflicts with mainnet, use different port")
        
        # Database validation
        parent_dir = os.path.dirname(self.database.blockchain_db_path)
        if parent_dir and not os.path.exists(parent_dir):
            issues.append(f"Blockchain DB path directory does not exist: {parent_dir}")
        
        return issues
    
    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables for staging deployment"""
        env_vars = {
            # Network
            'WWC_NETWORK_NAME': self.network.name,
            'WWC_NETWORK_ID': str(self.network.network_id),
            'WWC_PORT': str(self.network.port),
            'WWC_RPC_PORT': str(self.network.rpc_port),
            
            # Security
            'WWC_RATE_LIMIT_ENABLED': str(self.security.rate_limit_enabled),
            'WWC_MAX_REQUESTS_PER_MINUTE': str(self.security.max_requests_per_minute),
            'WWC_REQUIRE_AUTH': str(self.security.require_auth),
            
            # Database
            'WWC_BLOCKCHAIN_DB_PATH': self.database.blockchain_db_path,
            'WWC_UTXO_DB_PATH': self.database.utxo_db_path,
            'WWC_MEMPOOL_DB_HOST': self.database.mempool_db_host,
            'WWC_MEMPOOL_DB_PORT': str(self.database.mempool_db_port),
            
            # Monitoring
            'WWC_METRICS_ENABLED': str(self.monitoring.metrics_enabled),
            'WWC_METRICS_PORT': str(self.monitoring.metrics_port),
            'WWC_LOG_LEVEL': self.monitoring.log_level,
            'WWC_LOG_FILE': self.monitoring.log_file,
            
            # Deployment
            'WWC_ENVIRONMENT': self.deployment.environment,
            'WWC_REGION': self.deployment.region,
            
            # Staging-specific
            'WWC_STAGING': 'true',
            'WWC_FAST_MINING': 'true',
            'WWC_DEBUG_MODE': 'true'
        }
        
        return env_vars
    
    def create_directories(self):
        """Create necessary directories for staging"""
        directories = [
            os.path.dirname(self.database.blockchain_db_path),
            os.path.dirname(self.database.utxo_db_path),
            self.database.backup_path,
            os.path.dirname(self.monitoring.log_file),
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created staging directory: {directory}")
            except Exception as e:
                print(f"Error creating staging directory {directory}: {e}")
    
    def get_docker_compose(self) -> str:
        """Generate Docker Compose configuration for staging"""
        compose = {
            'version': '3.8',
            'services': {
                'worldwidecoin-staging': {
                    'build': '.',
                    'ports': [
                        f"{self.network.port}:{self.network.port}",
                        f"{self.network.rpc_port}:{self.network.rpc_port}",
                        f"{self.monitoring.metrics_port}:{self.monitoring.metrics_port}",
                        f"{self.monitoring.health_check_port}:{self.monitoring.health_check_port}"
                    ],
                    'environment': self.get_env_vars(),
                    'volumes': [
                        f"{self.database.blockchain_db_path}:/data/blockchain",
                        f"{self.database.utxo_db_path}:/data/utxo",
                        f"{self.database.backup_path}:/data/backups",
                        f"{self.monitoring.log_file}:/var/log/worldwidecoin/staging.log"
                    ],
                    'restart': 'unless-stopped',
                    'deploy': {
                        'replicas': self.deployment.desired_instances,
                        'resources': {
                            'limits': {
                                'cpus': f"{self.deployment.cpu_units / 1024}",
                                'memory': f"{self.deployment.memory_mb}M"
                            }
                        }
                    }
                },
                'redis-staging': {
                    'image': 'redis:7-alpine',
                    'ports': [f"{self.database.mempool_db_port}:6379"],
                    'volumes': ['./data/staging/redis:/data'],
                    'restart': 'unless-stopped',
                    'command': 'redis-server --port 6379'
                },
                'prometheus-staging': {
                    'image': 'prom/prometheus:latest',
                    'ports': [f"{self.monitoring.metrics_port + 1}:9090"],
                    'volumes': ['./monitoring/staging-prometheus.yml:/etc/prometheus/prometheus.yml'],
                    'restart': 'unless-stopped',
                    'command': '--config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus'
                },
                'grafana-staging': {
                    'image': 'grafana/grafana:latest',
                    'ports': [f"{self.monitoring.metrics_port + 2}:3000"],
                    'volumes': ['./monitoring/staging-grafana:/var/lib/grafana'],
                    'restart': 'unless-stopped',
                    'environment': {
                        'GF_SECURITY_ADMIN_PASSWORD': 'staging123'
                    }
                }
            }
        }
        
        return json.dumps(compose, indent=2)
    
    def get_staging_tests(self) -> List[Dict]:
        """Get staging test configurations"""
        return [
            {
                "name": "basic_connectivity",
                "description": "Test basic node connectivity",
                "test_function": "test_basic_connectivity",
                "timeout": 30,
                "critical": True
            },
            {
                "name": "blockchain_sync",
                "description": "Test blockchain synchronization",
                "test_function": "test_blockchain_sync",
                "timeout": 120,
                "critical": True
            },
            {
                "name": "mining_functionality",
                "description": "Test mining functionality",
                "test_function": "test_mining",
                "timeout": 180,
                "critical": True
            },
            {
                "name": "api_endpoints",
                "description": "Test API endpoints",
                "test_function": "test_api_endpoints",
                "timeout": 60,
                "critical": True
            },
            {
                "name": "monitoring_system",
                "description": "Test monitoring system",
                "test_function": "test_monitoring",
                "timeout": 30,
                "critical": False
            },
            {
                "name": "security_features",
                "description": "Test security features",
                "test_function": "test_security",
                "timeout": 60,
                "critical": False
            }
        ]


def create_staging_config() -> StagingConfig:
    """Create and configure staging environment"""
    print("Creating staging environment configuration...")
    
    config = StagingConfig()
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print("Staging configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return None
    
    # Create directories
    config.create_directories()
    
    # Save configuration
    config.save_config()
    
    print("Staging configuration created successfully")
    return config


if __name__ == "__main__":
    config = create_staging_config()
    if config:
        print("\nDocker Compose for Staging:")
        print(config.get_docker_compose())
        
        print("\nEnvironment Variables for Staging:")
        for k, v in config.get_env_vars().items():
            print(f"  {k}={v}")
        
        print("\nStaging Tests:")
        for test in config.get_staging_tests():
            print(f"  - {test['name']}: {test['description']}")
