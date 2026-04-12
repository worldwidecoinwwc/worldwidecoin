# WorldWideCoin Mainnet Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying WorldWideCoin mainnet with production-grade security, monitoring, and automation.

## Prerequisites

### System Requirements

- **Minimum**: 3 instances, t3.medium (2 vCPU, 4GB RAM)
- **Recommended**: 5 instances, t3.large (2 vCPU, 8GB RAM)
- **Storage**: 100GB SSD per instance
- **Network**: 1Gbps connectivity
- **Operating System**: Ubuntu 20.04 LTS or later

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (optional)
- Python 3.9+
- Git 2.30+

### Security Requirements

- Firewall configuration
- SSL/TLS certificates
- VPN access for management
- Security scanning tools

## Architecture

### Components

1. **Blockchain Nodes** - Core blockchain functionality
2. **API Servers** - REST API endpoints
3. **Monitoring Stack** - Prometheus, Grafana, AlertManager
4. **Load Balancer** - Traffic distribution
5. **Database Storage** - RocksDB persistence
6. **Security Layer** - DDoS protection, rate limiting

### Network Topology

```
Internet
    |
    v
[Load Balancer]
    |
    +--[API Gateway]--[Blockchain Node 1]
    |
    +--[API Gateway]--[Blockchain Node 2]
    |
    +--[API Gateway]--[Blockchain Node 3]
    |
    +--[Monitoring Stack]
```

## Deployment Steps

### 1. Environment Setup

#### 1.1 Create Deployment Configuration

```python
from deployment.mainnet_config import create_mainnet_config

# Create mainnet configuration
config = create_mainnet_config()

# Customize as needed
config.network.port = 8333
config.security.rate_limit_enabled = True
config.database.backup_enabled = True
config.monitoring.alerting_enabled = True

# Save configuration
config.save_config()
```

#### 1.2 Initialize Security

```python
from deployment.network_security import initialize_security

# Initialize network security
security = initialize_security()

# Add allowed IPs
security.allow_ip("192.168.1.100")
security.allow_ip("10.0.0.0/8")
```

#### 1.3 Setup Monitoring

```python
from deployment.monitoring import create_monitoring_system
from core.blockchain import Blockchain

# Create blockchain instance
blockchain = Blockchain()

# Initialize monitoring
monitoring = create_monitoring_system(blockchain)
monitoring.start()
```

### 2. Infrastructure Deployment

#### 2.1 Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  worldwidecoin:
    build: .
    ports:
      - "8333:8333"
      - "8332:8332"
      - "9090:9090"
    environment:
      - WWC_ENVIRONMENT=production
      - WWC_NETWORK_ID=1
    volumes:
      - ./data/blockchain:/data/blockchain
      - ./data/utxo:/data/utxo
      - ./logs:/var/log/worldwidecoin
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./data/prometheus:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana:/var/lib/grafana
    restart: unless-stopped
```

Deploy with:

```bash
docker-compose up -d
```

#### 2.2 Kubernetes Deployment

Create namespace and apply manifests:

```bash
# Create namespace
kubectl create namespace worldwidecoin

# Apply configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 3. Security Configuration

#### 3.1 Firewall Rules

```bash
# Allow blockchain P2P traffic
sudo ufw allow 8333/tcp

# Allow API traffic from load balancer
sudo ufw allow from 10.0.0.0/8 to any port 8332

# Allow monitoring
sudo ufw allow from 10.0.0.0/8 to any port 9090

# Default deny
sudo ufw default deny incoming
sudo ufw enable
```

#### 3.2 SSL/TLS Configuration

```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/worldwidecoin.key \
  -out /etc/ssl/certs/worldwidecoin.crt

# Configure nginx/HAProxy with SSL
# (See monitoring/nginx.conf)
```

#### 3.3 Rate Limiting

```python
# Configure rate limiting
from deployment.network_security import NetworkSecurity

security = NetworkSecurity({
    "rate_limiting": {
        "max_requests_per_minute": 100,
        "max_connections_per_ip": 10
    }
})
```

### 4. Monitoring Setup

#### 4.1 Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'worldwidecoin'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### 4.2 Grafana Dashboards

Import pre-configured dashboards:

- Blockchain Overview
- System Performance
- Network Security
- Transaction Metrics

#### 4.3 Alert Rules

Create `monitoring/alerts.yml`:

```yaml
groups:
  - name: worldwidecoin
    rules:
      - alert: HighCPUUsage
        expr: system_cpu_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"

      - alert: BlockchainStalled
        expr: increase(blockchain_height[10m]) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Blockchain height has not changed"
```

### 5. Deployment Automation

#### 5.1 CI/CD Pipeline

```python
from deployment.deployment_automation import setup_deployment_automation

# Setup automation
automation = setup_deployment_automation()

# Run full pipeline
pipeline_result = automation.run_pipeline("manual")
print(f"Pipeline status: {pipeline_result['status']}")
```

#### 5.2 Automated Deployment

```bash
# Deploy new version
python deployment/deployment_automation.py deploy --version v1.2.0

# Rollback if needed
python deployment/deployment_automation.py rollback --to v1.1.0
```

### 6. Health Checks

#### 6.1 Application Health

```bash
# Check application health
curl http://localhost:8080/health

# Check readiness
curl http://localhost:8080/ready

# Check metrics
curl http://localhost:9090/metrics
```

#### 6.2 System Health

```bash
# Check system resources
top
htop
df -h
free -h

# Check network connections
netstat -an | grep :8333
```

### 7. Backup and Recovery

#### 7.1 Automated Backups

```python
from deployment.mainnet_config import MainnetConfig

config = MainnetConfig()

# Enable backups
config.database.backup_enabled = True
config.database.backup_interval = 3600  # 1 hour
config.database.backup_retention_days = 30

config.save_config()
```

#### 7.2 Manual Backup

```bash
# Backup blockchain data
tar -czf backup-$(date +%Y%m%d).tar.gz /data/worldwidecoin/

# Backup configuration
cp -r /etc/worldwidecoin/ backup-config-$(date +%Y%m%d)/
```

#### 7.3 Recovery Procedures

```bash
# Stop services
docker-compose down

# Restore data
tar -xzf backup-20231201.tar.gz -C /

# Start services
docker-compose up -d

# Verify recovery
curl http://localhost:8080/health
```

## Operations

### Daily Tasks

1. **Monitor System Health**
   - Check Grafana dashboards
   - Review alert notifications
   - Verify backup completion

2. **Security Monitoring**
   - Review security logs
   - Check for blocked IPs
   - Monitor DDoS protection

3. **Performance Monitoring**
   - Check CPU/memory usage
   - Monitor network traffic
   - Review blockchain metrics

### Weekly Tasks

1. **Maintenance**
   - Apply security patches
   - Update dependencies
   - Clean old logs and backups

2. **Capacity Planning**
   - Review resource utilization
   - Plan scaling adjustments
   - Update forecasts

### Monthly Tasks

1. **Security Audit**
   - Review access logs
   - Update firewall rules
   - Security scan results

2. **Performance Review**
   - Analyze performance trends
   - Optimize configurations
   - Update monitoring thresholds

## Troubleshooting

### Common Issues

#### High CPU Usage

```bash
# Check processes
top -p $(pgrep -f worldwidecoin)

# Check blockchain metrics
curl http://localhost:9090/metrics | grep cpu

# Restart if needed
docker-compose restart worldwidecoin
```

#### Network Issues

```bash
# Check connectivity
telnet node.example.com 8333

# Check firewall
sudo ufw status

# Check network stats
netstat -i
```

#### Database Issues

```bash
# Check database status
ls -la /data/worldwidecoin/

# Check disk space
df -h /data/

# Repair if needed
python tools/repair_database.py
```

### Emergency Procedures

#### Service Outage

1. **Identify affected services**
   ```bash
   docker-compose ps
   ```

2. **Check logs**
   ```bash
   docker-compose logs worldwidecoin
   ```

3. **Restart services**
   ```bash
   docker-compose restart
   ```

4. **Verify recovery**
   ```bash
   curl http://localhost:8080/health
   ```

#### Security Incident

1. **Isolate affected systems**
   ```bash
   # Block malicious IP
   python deployment/network_security.py block_ip --ip 192.168.1.100
   ```

2. **Enable enhanced monitoring**
   ```bash
   # Increase monitoring frequency
   python deployment/monitoring.py --interval 5
   ```

3. **Review security logs**
   ```bash
   grep "SECURITY" /var/log/worldwidecoin/mainnet.log
   ```

## Scaling

### Horizontal Scaling

```bash
# Scale up
docker-compose up -d --scale worldwidecoin=5

# Scale down
docker-compose up -d --scale worldwidecoin=3
```

### Vertical Scaling

```yaml
# Update docker-compose.yml
services:
  worldwidecoin:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Auto-scaling

```python
# Enable auto-scaling
from deployment.deployment_automation import DeploymentAutomation

automation = DeploymentAutomation()
automation.enable_auto_scaling(
    min_instances=3,
    max_instances=10,
    target_cpu=70.0
)
```

## Security Best Practices

### Network Security

1. **Use VPN for management access**
2. **Implement IP whitelisting**
3. **Enable DDoS protection**
4. **Regular security updates**

### Application Security

1. **Enable authentication**
2. **Use HTTPS everywhere**
3. **Implement rate limiting**
4. **Regular security scanning**

### Data Security

1. **Encrypt sensitive data**
2. **Regular backups**
3. **Access control**
4. **Audit logging**

## Support

### Documentation

- [API Documentation](api_documentation.md)
- [Configuration Guide](configuration_guide.md)
- [Troubleshooting Guide](troubleshooting_guide.md)

### Community

- GitHub Issues: https://github.com/worldwidecoin/issues
- Discord: https://discord.gg/worldwidecoin
- Forum: https://forum.worldwidecoin.org

### Emergency Contact

- Security Team: security@worldwidecoin.org
- Operations Team: ops@worldwidecoin.org
- 24/7 Hotline: +1-555-WWC-HELP

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-01 | Initial mainnet release |
| 1.1.0 | 2024-02-01 | Added enhanced monitoring |
| 1.2.0 | 2024-03-01 | Improved security features |
| 1.3.0 | 2024-04-01 | Auto-scaling support |

---

**Note**: This guide is continuously updated. Check for the latest version before deployment.
