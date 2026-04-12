# deployment/mainnet_config.py
import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class NetworkConfig:
    """Mainnet network configuration"""
    name: str = "WorldWideCoin Mainnet"
    network_id: int = 1
    genesis_timestamp: int = int(time.time())
    
    # Network parameters
    port: int = 8333
    rpc_port: int = 8332
    max_peers: int = 50
    min_peers: int = 8
    
    # Mining parameters
    initial_difficulty: int = 4
    target_block_time: float = 600.0  # 10 minutes
    difficulty_window: int = 2016
    max_difficulty: int = 32
    
    # Economic parameters
    initial_reward: float = 50.0
    reward_halving_interval: int = 210000
    treasury_percent: float = 0.05
    fee_burn_percent: float = 0.5
    
    # Security parameters
    max_tx_size: int = 1000000  # 1MB
    max_block_size: int = 4000000  # 4MB
    mempool_max_size: int = 10000
    max_orphan_depth: int = 100


@dataclass
class SecurityConfig:
    """Security configuration for mainnet"""
    # Rate limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100
    max_connections_per_ip: int = 10
    
    # DDoS protection
    ddos_protection: bool = True
    connection_timeout: int = 30
    max_message_size: int = 1000000
    
    # Authentication
    require_auth: bool = True
    api_key_required: bool = True
    allowed_ips: List[str] = None
    
    # Encryption
    require_encryption: bool = True
    min_tls_version: str = "1.2"
    
    def __post_init__(self):
        if self.allowed_ips is None:
            self.allowed_ips = ["127.0.0.1", "::1"]


@dataclass
class DatabaseConfig:
    """Database configuration for mainnet"""
    # Blockchain storage
    blockchain_db_type: str = "rocksdb"
    blockchain_db_path: str = "/data/worldwidecoin/blockchain"
    
    # UTXO storage
    utxo_db_type: str = "rocksdb"
    utxo_db_path: str = "/data/worldwidecoin/utxo"
    
    # Mempool storage
    mempool_db_type: str = "redis"
    mempool_db_host: str = "localhost"
    mempool_db_port: int = 6379
    
    # Backup configuration
    backup_enabled: bool = True
    backup_interval: int = 3600  # 1 hour
    backup_retention_days: int = 30
    backup_path: str = "/data/worldwidecoin/backups"
    
    # Performance
    cache_size_mb: int = 1024
    write_buffer_size_mb: int = 128
    max_open_files: int = 1000


@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_interval: int = 15
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/var/log/worldwidecoin/mainnet.log"
    log_rotation: bool = True
    log_max_size_mb: int = 100
    log_max_files: int = 10
    
    # Health checks
    health_check_enabled: bool = True
    health_check_interval: int = 30
    health_check_port: int = 8080
    
    # Alerting
    alerting_enabled: bool = True
    alert_webhook_url: Optional[str] = None
    alert_email_smtp: Optional[str] = None
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "block_height_delay": 10,
                "peer_count_min": 5
            }


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    # Environment
    environment: str = "production"
    region: str = "us-west-2"
    availability_zone: str = "us-west-2a"
    
    # Scaling
    min_instances: int = 3
    max_instances: int = 10
    desired_instances: int = 5
    
    # Resources
    cpu_units: int = 1024
    memory_mb: int = 2048
    storage_gb: int = 100
    
    # Load balancing
    load_balancer_enabled: bool = True
    health_check_path: str = "/health"
    health_check_interval: int = 30
    
    # Auto-scaling
    auto_scaling_enabled: bool = True
    scale_up_threshold: float = 70.0
    scale_down_threshold: float = 30.0
    scale_cooldown: int = 300


class MainnetConfig:
    """Mainnet configuration manager"""
    
    def __init__(self, config_file: str = "mainnet.json"):
        self.config_file = config_file
        self.network = NetworkConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.monitoring = MonitoringConfig()
        self.deployment = DeploymentConfig()
        
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
                    self.network = NetworkConfig(**data['network'])
                if 'security' in data:
                    self.security = SecurityConfig(**data['security'])
                if 'database' in data:
                    self.database = DatabaseConfig(**data['database'])
                if 'monitoring' in data:
                    self.monitoring = MonitoringConfig(**data['monitoring'])
                if 'deployment' in data:
                    self.deployment = DeploymentConfig(**data['deployment'])
                
                print(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Using default configuration")
        else:
            print(f"Configuration file not found, using defaults")
    
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
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Network validation
        if self.network.port < 1024 or self.network.port > 65535:
            issues.append("Network port must be between 1024-65535")
        
        if self.network.max_peers < self.network.min_peers:
            issues.append("Max peers must be >= min peers")
        
        # Security validation
        if self.security.require_auth and not self.security.allowed_ips:
            issues.append("Allowed IPs must be specified when auth is required")
        
        # Database validation
        if not os.path.exists(os.path.dirname(self.database.blockchain_db_path)):
            issues.append(f"Blockchain DB path directory does not exist: {os.path.dirname(self.database.blockchain_db_path)}")
        
        # Monitoring validation
        if self.monitoring.alerting_enabled and not self.monitoring.alert_webhook_url:
            issues.append("Alert webhook URL required when alerting is enabled")
        
        return issues
    
    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables for deployment"""
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
        }
        
        return env_vars
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            os.path.dirname(self.database.blockchain_db_path),
            os.path.dirname(self.database.utxo_db_path),
            self.database.backup_path,
            os.path.dirname(self.monitoring.log_file),
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
    
    def get_docker_compose(self) -> str:
        """Generate Docker Compose configuration"""
        compose = {
            'version': '3.8',
            'services': {
                'worldwidecoin': {
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
                        f"{self.monitoring.log_file}:/var/log/worldwidecoin/mainnet.log"
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
                'redis': {
                    'image': 'redis:7-alpine',
                    'ports': [f"{self.database.mempool_db_port}:6379"],
                    'volumes': ['/data/redis:/data'],
                    'restart': 'unless-stopped'
                },
                'prometheus': {
                    'image': 'prom/prometheus:latest',
                    'ports': [f"{self.monitoring.metrics_port + 1}:9090"],
                    'volumes': ['./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml'],
                    'restart': 'unless-stopped'
                },
                'grafana': {
                    'image': 'grafana/grafana:latest',
                    'ports': [f"{self.monitoring.metrics_port + 2}:3000"],
                    'volumes': ['./monitoring/grafana:/var/lib/grafana'],
                    'restart': 'unless-stopped'
                }
            }
        }
        
        return json.dumps(compose, indent=2)
    
    def get_kubernetes_manifest(self) -> str:
        """Generate Kubernetes deployment manifest"""
        manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'worldwidecoin-mainnet',
                'labels': {'app': 'worldwidecoin', 'tier': 'backend'}
            },
            'spec': {
                'replicas': self.deployment.desired_instances,
                'selector': {'matchLabels': {'app': 'worldwidecoin'}},
                'template': {
                    'metadata': {'labels': {'app': 'worldwidecoin'}},
                    'spec': {
                        'containers': [{
                            'name': 'worldwidecoin',
                            'image': 'worldwidecoin:latest',
                            'ports': [
                                {'containerPort': self.network.port},
                                {'containerPort': self.network.rpc_port},
                                {'containerPort': self.monitoring.metrics_port}
                            ],
                            'env': [
                                {'name': k, 'value': v} 
                                for k, v in self.get_env_vars().items()
                            ],
                            'resources': {
                                'requests': {
                                    'cpu': f"{self.deployment.cpu_units}m",
                                    'memory': f"{self.deployment.memory_mb}Mi"
                                },
                                'limits': {
                                    'cpu': f"{self.deployment.cpu_units * 2}m",
                                    'memory': f"{self.deployment.memory_mb * 2}Mi"
                                }
                            },
                            'volumeMounts': [
                                {'name': 'blockchain-data', 'mountPath': '/data/blockchain'},
                                {'name': 'utxo-data', 'mountPath': '/data/utxo'},
                                {'name': 'logs', 'mountPath': '/var/log/worldwidecoin'}
                            ],
                            'livenessProbe': {
                                'httpGet': {
                                    'path': self.monitoring.health_check_path,
                                    'port': self.monitoring.health_check_port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/ready',
                                    'port': self.monitoring.health_check_port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }],
                        'volumes': [
                            {'name': 'blockchain-data', 'persistentVolumeClaim': {'claimName': 'blockchain-pvc'}},
                            {'name': 'utxo-data', 'persistentVolumeClaim': {'claimName': 'utxo-pvc'}},
                            {'name': 'logs', 'persistentVolumeClaim': {'claimName': 'logs-pvc'}}
                        ]
                    }
                }
            }
        }
        
        return json.dumps(manifest, indent=2)


def create_mainnet_config() -> MainnetConfig:
    """Create and configure mainnet deployment"""
    print("Creating mainnet configuration...")
    
    config = MainnetConfig()
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return None
    
    # Create directories
    config.create_directories()
    
    # Save configuration
    config.save_config()
    
    print("Mainnet configuration created successfully")
    return config


if __name__ == "__main__":
    config = create_mainnet_config()
    if config:
        print("\nDocker Compose:")
        print(config.get_docker_compose())
        
        print("\nEnvironment Variables:")
        for k, v in config.get_env_vars().items():
            print(f"  {k}={v}")
