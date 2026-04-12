# deployment/staging_deployment.py
import os
import json
import time
import subprocess
import threading
from typing import Dict, List, Optional
from deployment.staging_config import StagingConfig, create_staging_config
from deployment.network_security import NetworkSecurity
from deployment.monitoring import MonitoringSystem
from core.blockchain import Blockchain


class StagingDeployment:
    """Staging environment deployment manager"""
    
    def __init__(self, config_file: str = "staging.json"):
        self.config = create_staging_config()
        self.deployment_status = "idle"
        self.deployment_log: List[Dict] = []
        self.services: Dict[str, Dict] = {}
        self.health_checks: Dict[str, Dict] = {}
        
        print("Staging deployment manager initialized")
    
    def deploy_staging_environment(self) -> bool:
        """Deploy complete staging environment"""
        print("Starting staging environment deployment...")
        
        try:
            # Step 1: Validate configuration
            if not self._validate_configuration():
                return False
            
            # Step 2: Setup infrastructure
            if not self._setup_infrastructure():
                return False
            
            # Step 3: Deploy services
            if not self._deploy_services():
                return False
            
            # Step 4: Start monitoring
            if not self._start_monitoring():
                return False
            
            # Step 5: Run health checks
            if not self._run_health_checks():
                return False
            
            print("Staging deployment completed successfully")
            return True
            
        except Exception as e:
            print(f"Staging deployment failed: {e}")
            self._cleanup_deployment()
            return False
    
    def _validate_configuration(self) -> bool:
        """Validate staging configuration"""
        print("Validating staging configuration...")
        
        issues = self.config.validate_config()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        print("Configuration validation passed")
        return True
    
    def _setup_infrastructure(self) -> bool:
        """Setup staging infrastructure"""
        print("Setting up staging infrastructure...")
        
        try:
            # Create Docker Compose file
            compose_content = self.config.get_docker_compose()
            with open("docker-compose.staging.yml", "w") as f:
                f.write(compose_content)
            
            # Create monitoring configuration
            self._create_monitoring_configs()
            
            # Create test scripts
            self._create_test_scripts()
            
            print("Infrastructure setup completed")
            return True
            
        except Exception as e:
            print(f"Infrastructure setup failed: {e}")
            return False
    
    def _create_monitoring_configs(self):
        """Create monitoring configurations"""
        os.makedirs("monitoring", exist_ok=True)
        
        # Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "worldwidecoin-staging",
                    "static_configs": [
                        {"targets": [f"localhost:{self.config.monitoring.metrics_port}"]}
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "10s"
                },
                {
                    "job_name": "node-exporter",
                    "static_configs": [
                        {"targets": ["localhost:9100"]}
                    ]
                }
            ],
            "rule_files": ["staging-alerts.yml"]
        }
        
        with open("monitoring/staging-prometheus.yml", "w") as f:
            import yaml
            yaml.dump(prometheus_config, f)
        
        # Alert rules
        alert_rules = {
            "groups": [
                {
                    "name": "staging",
                    "rules": [
                        {
                            "alert": "StagingServiceDown",
                            "expr": "up == 0",
                            "for": "1m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "Staging service is down",
                                "description": "Staging service {{ $labels.instance }} has been down for more than 1 minute"
                            }
                        },
                        {
                            "alert": "StagingHighCPU",
                            "expr": "system_cpu_percent > 90",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High CPU usage in staging",
                                "description": "CPU usage is {{ $value }}% in staging environment"
                            }
                        }
                    ]
                }
            ]
        }
        
        with open("monitoring/staging-alerts.yml", "w") as f:
            yaml.dump(alert_rules, f)
        
        print("Monitoring configurations created")
    
    def _create_test_scripts(self):
        """Create test scripts for staging"""
        test_script = """#!/usr/bin/env python3
import requests
import time
import sys

def test_basic_connectivity():
    \"\"\"Test basic node connectivity\"\"\"
    try:
        response = requests.get("http://localhost:18332/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_blockchain_sync():
    \"\"\"Test blockchain synchronization\"\"\"
    try:
        response = requests.get("http://localhost:18332/blockchain/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("height", 0) > 0
    except:
        pass
    return False

def test_mining():
    \"\"\"Test mining functionality\"\"\"
    try:
        response = requests.post("http://localhost:18332/mine", 
                              json={"blocks": 1}, timeout=30)
        return response.status_code == 200
    except:
        return False

def test_api_endpoints():
    \"\"\"Test API endpoints\"\"\"
    endpoints = [
        "/health",
        "/blockchain/info",
        "/mempool/info",
        "/peers/info"
    ]
    
    base_url = "http://localhost:18332"
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code != 200:
                return False
        except:
            return False
    
    return True

def main():
    test_name = sys.argv[1] if len(sys.argv) > 1 else "basic_connectivity"
    
    tests = {
        "basic_connectivity": test_basic_connectivity,
        "blockchain_sync": test_blockchain_sync,
        "mining": test_mining,
        "api_endpoints": test_api_endpoints
    }
    
    if test_name not in tests:
        print(f"Unknown test: {test_name}")
        sys.exit(1)
    
    success = tests[test_name]()
    print(f"Test {test_name}: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
        
        with open("test_staging.py", "w") as f:
            f.write(test_script)
        
        os.chmod("test_staging.py", 0o755)
        print("Test scripts created")
    
    def _deploy_services(self) -> bool:
        """Deploy staging services"""
        print("Deploying staging services...")
        
        try:
            # Start services with Docker Compose
            cmd = ["docker-compose", "-f", "docker-compose.staging.yml", "up", "-d"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Docker Compose failed: {result.stderr}")
                return False
            
            print("Docker Compose services started")
            
            # Wait for services to be ready
            print("Waiting for services to be ready...")
            time.sleep(30)
            
            # Check if services are running
            cmd = ["docker-compose", "-f", "docker-compose.staging.yml", "ps"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            print("Service status:")
            print(result.stdout)
            
            return True
            
        except Exception as e:
            print(f"Service deployment failed: {e}")
            return False
    
    def _start_monitoring(self) -> bool:
        """Start monitoring for staging"""
        print("Starting staging monitoring...")
        
        try:
            # Create blockchain instance
            blockchain = Blockchain()
            
            # Initialize monitoring system
            monitoring_config = {
                "log_level": "DEBUG",
                "log_file": self.config.monitoring.log_file,
                "metrics_enabled": True,
                "metrics_port": self.config.monitoring.metrics_port
            }
            
            self.monitoring = MonitoringSystem(blockchain, monitoring_config)
            self.monitoring.start()
            
            # Start health checker
            self.health_checker = self.monitoring.health_checker
            
            print("Staging monitoring started")
            return True
            
        except Exception as e:
            print(f"Monitoring startup failed: {e}")
            return False
    
    def _run_health_checks(self) -> bool:
        """Run staging health checks"""
        print("Running staging health checks...")
        
        tests = self.config.get_staging_tests()
        all_passed = True
        
        for test in tests:
            print(f"Running {test['name']}...")
            
            try:
                # Run test script
                cmd = ["python3", "test_staging.py", test['name']]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=test['timeout'])
                
                success = result.returncode == 0
                
                self.health_checks[test['name']] = {
                    "status": "pass" if success else "fail",
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                    "timestamp": time.time()
                }
                
                print(f"  {test['name']}: {'PASS' if success else 'FAIL'}")
                
                if not success and test['critical']:
                    print(f"  Critical test failed: {test['name']}")
                    all_passed = False
                
            except subprocess.TimeoutExpired:
                print(f"  {test['name']}: TIMEOUT")
                self.health_checks[test['name']] = {
                    "status": "timeout",
                    "error": f"Test timed out after {test['timeout']} seconds",
                    "timestamp": time.time()
                }
                
                if test['critical']:
                    all_passed = False
            
            except Exception as e:
                print(f"  {test['name']}: ERROR - {e}")
                self.health_checks[test['name']] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }
                
                if test['critical']:
                    all_passed = False
        
        print(f"Health checks completed: {'PASS' if all_passed else 'FAIL'}")
        return all_passed
    
    def get_deployment_status(self) -> Dict:
        """Get current deployment status"""
        return {
            "status": self.deployment_status,
            "config": {
                "environment": self.config.deployment.environment,
                "network_id": self.config.network.network_id,
                "port": self.config.network.port
            },
            "services": self.services,
            "health_checks": self.health_checks,
            "timestamp": time.time()
        }
    
    def run_stress_test(self, duration_minutes: int = 10) -> Dict:
        """Run stress test on staging environment"""
        print(f"Running stress test for {duration_minutes} minutes...")
        
        stress_results = {
            "start_time": time.time(),
            "duration_minutes": duration_minutes,
            "metrics": {},
            "errors": []
        }
        
        try:
            # Start stress testing
            end_time = time.time() + (duration_minutes * 60)
            
            while time.time() < end_time:
                # Generate test transactions
                self._generate_test_transactions()
                
                # Check system metrics
                if hasattr(self, 'monitoring'):
                    metrics = self.monitoring.get_metrics_summary()
                    stress_results["metrics"][int(time.time())] = metrics
                
                # Check service health
                health = self._check_service_health()
                if not health:
                    stress_results["errors"].append({
                        "timestamp": time.time(),
                        "error": "Service health check failed"
                    })
                
                time.sleep(30)  # Check every 30 seconds
            
            stress_results["end_time"] = time.time()
            stress_results["success"] = len(stress_results["errors"]) == 0
            
            print(f"Stress test completed: {'PASS' if stress_results['success'] else 'FAIL'}")
            
        except Exception as e:
            stress_results["error"] = str(e)
            stress_results["success"] = False
        
        return stress_results
    
    def _generate_test_transactions(self):
        """Generate test transactions for stress testing"""
        try:
            import requests
            
            # Generate multiple transactions
            for i in range(10):
                tx_data = {
                    "from": f"test_addr_{i}",
                    "to": f"test_addr_{i+1}",
                    "amount": 1.0,
                    "fee": 0.01
                }
                
                response = requests.post(
                    "http://localhost:18332/transaction",
                    json=tx_data,
                    timeout=5
                )
                
                if response.status_code != 200:
                    print(f"Failed to create transaction {i}: {response.status_code}")
        
        except Exception as e:
            print(f"Error generating test transactions: {e}")
    
    def _check_service_health(self) -> bool:
        """Check if staging services are healthy"""
        try:
            import requests
            
            response = requests.get("http://localhost:18332/health", timeout=5)
            return response.status_code == 200
            
        except:
            return False
    
    def _cleanup_deployment(self):
        """Clean up staging deployment"""
        print("Cleaning up staging deployment...")
        
        try:
            # Stop services
            cmd = ["docker-compose", "-f", "docker-compose.staging.yml", "down"]
            subprocess.run(cmd, capture_output=True, text=True)
            
            # Stop monitoring
            if hasattr(self, 'monitoring'):
                self.monitoring.stop()
            
            print("Staging deployment cleaned up")
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def stop_staging(self):
        """Stop staging environment"""
        print("Stopping staging environment...")
        self._cleanup_deployment()
        self.deployment_status = "stopped"


def deploy_staging_environment() -> StagingDeployment:
    """Deploy complete staging environment"""
    print("Deploying WorldWideCoin staging environment...")
    
    deployment = StagingDeployment()
    
    if deployment.deploy_staging_environment():
        print("Staging environment deployed successfully")
        
        # Run initial stress test
        stress_results = deployment.run_stress_test(5)  # 5 minutes
        
        if stress_results["success"]:
            print("Stress test passed")
        else:
            print(f"Stress test failed: {len(stress_results['errors'])} errors")
        
        return deployment
    else:
        print("Staging deployment failed")
        return None


if __name__ == "__main__":
    deployment = deploy_staging_environment()
    
    if deployment:
        print("\nStaging deployment status:")
        status = deployment.get_deployment_status()
        print(json.dumps(status, indent=2))
        
        print("\nTo stop staging: python staging_deployment.py stop")
        
        # Keep running for demonstration
        try:
            while True:
                time.sleep(60)
                health = deployment._check_service_health()
                print(f"Health check: {'OK' if health else 'FAILED'}")
        except KeyboardInterrupt:
            print("\nStopping staging...")
            deployment.stop_staging()
