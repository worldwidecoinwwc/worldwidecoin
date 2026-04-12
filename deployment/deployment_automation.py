# deployment/deployment_automation.py
import os
import json
import time
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import logging


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: str = "production"
    version: str = "latest"
    region: str = "us-west-2"
    instance_type: str = "t3.medium"
    min_instances: int = 3
    max_instances: int = 10
    desired_instances: int = 5
    
    # Network configuration
    vpc_cidr: str = "10.0.0.0/16"
    subnet_cidrs: List[str] = None
    security_groups: List[str] = None
    
    # Storage configuration
    volume_size_gb: int = 100
    volume_type: str = "gp3"
    backup_retention_days: int = 30
    
    # Monitoring configuration
    monitoring_enabled: bool = True
    log_retention_days: int = 14
    alerting_enabled: bool = True
    
    def __post_init__(self):
        if self.subnet_cidrs is None:
            self.subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
        if self.security_groups is None:
            self.security_groups = ["worldwidecoin-sg"]


class DeploymentManager:
    """Manages deployment automation"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.deployment_log: List[Dict] = []
        self.current_deployment: Optional[Dict] = None
        self.logger = self._setup_logger()
        
        # Deployment state
        self.deployment_id = None
        self.deployment_status = "idle"
        self.start_time = None
        self.end_time = None
        
        print(f"Deployment manager initialized for {config.environment}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup deployment logger"""
        logger = logging.getLogger("worldwidecoin.deployment")
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = "logs/deployments"
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(log_dir, f"deployment_{int(time.time())}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def start_deployment(self, version: str = None) -> str:
        """Start new deployment"""
        if self.deployment_status != "idle":
            raise RuntimeError(f"Deployment already in progress: {self.deployment_status}")
        
        self.deployment_id = f"deploy-{int(time.time())}"
        self.deployment_status = "starting"
        self.start_time = time.time()
        
        deployment_info = {
            "deployment_id": self.deployment_id,
            "version": version or self.config.version,
            "environment": self.config.environment,
            "status": self.deployment_status,
            "start_time": self.start_time,
            "config": asdict(self.config)
        }
        
        self.current_deployment = deployment_info
        self.deployment_log.append(deployment_info)
        
        self.logger.info(f"Starting deployment {self.deployment_id}")
        
        # Start deployment in background thread
        deployment_thread = threading.Thread(target=self._execute_deployment, daemon=True)
        deployment_thread.start()
        
        return self.deployment_id
    
    def _execute_deployment(self):
        """Execute deployment process"""
        try:
            self.deployment_status = "preparing"
            self.logger.info("Preparing deployment...")
            
            # Step 1: Validate environment
            self._validate_environment()
            
            # Step 2: Build application
            self.deployment_status = "building"
            self._build_application()
            
            # Step 3: Run tests
            self.deployment_status = "testing"
            self._run_tests()
            
            # Step 4: Deploy infrastructure
            self.deployment_status = "deploying_infra"
            self._deploy_infrastructure()
            
            # Step 5: Deploy application
            self.deployment_status = "deploying_app"
            self._deploy_application()
            
            # Step 6: Health checks
            self.deployment_status = "verifying"
            self._run_health_checks()
            
            # Step 7: Complete deployment
            self.deployment_status = "completed"
            self.end_time = time.time()
            
            self.logger.info(f"Deployment {self.deployment_id} completed successfully")
            
        except Exception as e:
            self.deployment_status = "failed"
            self.end_time = time.time()
            
            self.logger.error(f"Deployment {self.deployment_id} failed: {e}")
            
            # Rollback on failure
            self._rollback_deployment()
    
    def _validate_environment(self):
        """Validate deployment environment"""
        self.logger.info("Validating environment...")
        
        # Check required tools
        required_tools = ["docker", "git", "python3"]
        for tool in required_tools:
            if not shutil.which(tool):
                raise RuntimeError(f"Required tool not found: {tool}")
        
        # Check environment variables
        required_env_vars = ["WWC_ENVIRONMENT", "WWC_REGION"]
        for var in required_env_vars:
            if var not in os.environ:
                raise RuntimeError(f"Required environment variable not set: {var}")
        
        # Check disk space
        disk_usage = shutil.disk_usage("/")
        free_space_gb = disk_usage.free / (1024**3)
        if free_space_gb < 10:
            raise RuntimeError(f"Insufficient disk space: {free_space_gb:.1f}GB available")
        
        self.logger.info("Environment validation passed")
    
    def _build_application(self):
        """Build application"""
        self.logger.info("Building application...")
        
        # Build Docker image
        build_cmd = [
            "docker", "build",
            "-t", f"worldwidecoin:{self.current_deployment['version']}",
            "."
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Docker build failed: {result.stderr}")
        
        self.logger.info("Application built successfully")
    
    def _run_tests(self):
        """Run deployment tests"""
        self.logger.info("Running deployment tests...")
        
        # Run unit tests
        test_cmd = ["python3", "-m", "pytest", "tests/", "-v"]
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Tests failed: {result.stderr}")
        
        # Run integration tests
        integration_cmd = ["python3", "test_integration.py"]
        result = subprocess.run(integration_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Integration tests failed: {result.stderr}")
        
        self.logger.info("All tests passed")
    
    def _deploy_infrastructure(self):
        """Deploy infrastructure"""
        self.logger.info("Deploying infrastructure...")
        
        # Create infrastructure using Terraform or CloudFormation
        infra_config = {
            "environment": self.config.environment,
            "region": self.config.region,
            "vpc_cidr": self.config.vpc_cidr,
            "subnet_cidrs": self.config.subnet_cidrs,
            "instance_type": self.config.instance_type,
            "min_instances": self.config.min_instances,
            "max_instances": self.config.max_instances,
            "desired_instances": self.config.desired_instances
        }
        
        # Save infrastructure config
        infra_file = f"infrastructure/{self.config.environment}.json"
        os.makedirs(os.path.dirname(infra_file), exist_ok=True)
        
        with open(infra_file, 'w') as f:
            json.dump(infra_config, f, indent=2)
        
        # Apply infrastructure (simplified - would use actual IaC tool)
        self.logger.info("Infrastructure deployed")
    
    def _deploy_application(self):
        """Deploy application"""
        self.logger.info("Deploying application...")
        
        # Create deployment manifest
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"worldwidecoin-{self.config.environment}",
                "labels": {
                    "app": "worldwidecoin",
                    "environment": self.config.environment
                }
            },
            "spec": {
                "replicas": self.config.desired_instances,
                "selector": {
                    "matchLabels": {
                        "app": "worldwidecoin"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "worldwidecoin",
                            "environment": self.config.environment
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "worldwidecoin",
                            "image": f"worldwidecoin:{self.current_deployment['version']}",
                            "ports": [{"containerPort": 8333}],
                            "env": [
                                {"name": "WWC_ENVIRONMENT", "value": self.config.environment},
                                {"name": "WWC_REGION", "value": self.config.region}
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": "500m",
                                    "memory": "1Gi"
                                },
                                "limits": {
                                    "cpu": "1000m",
                                    "memory": "2Gi"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        # Save manifest
        manifest_file = f"k8s/{self.config.environment}-deployment.yaml"
        os.makedirs(os.path.dirname(manifest_file), exist_ok=True)
        
        with open(manifest_file, 'w') as f:
            import yaml
            yaml.dump(manifest, f)
        
        # Apply manifest (simplified - would use kubectl)
        self.logger.info("Application deployed")
    
    def _run_health_checks(self):
        """Run post-deployment health checks"""
        self.logger.info("Running health checks...")
        
        # Wait for deployment to be ready
        time.sleep(30)
        
        # Check health endpoints
        health_checks = [
            ("http://localhost:8080/health", "application"),
            ("http://localhost:8080/ready", "readiness"),
            ("http://localhost:9090/metrics", "monitoring")
        ]
        
        for endpoint, check_name in health_checks:
            try:
                import requests
                response = requests.get(endpoint, timeout=10)
                if response.status_code != 200:
                    raise RuntimeError(f"Health check failed for {check_name}: {response.status_code}")
                
                self.logger.info(f"Health check passed: {check_name}")
                
            except Exception as e:
                raise RuntimeError(f"Health check failed for {check_name}: {e}")
        
        self.logger.info("All health checks passed")
    
    def _rollback_deployment(self):
        """Rollback failed deployment"""
        self.logger.info("Rolling back deployment...")
        
        # Get previous successful deployment
        previous_deployment = self._get_previous_deployment()
        
        if previous_deployment:
            # Rollback to previous version
            rollback_info = {
                "deployment_id": self.deployment_id,
                "rollback_to": previous_deployment["version"],
                "reason": "deployment_failed",
                "timestamp": time.time()
            }
            
            self.deployment_log.append(rollback_info)
            
            # Execute rollback (simplified)
            self.logger.info(f"Rolled back to version {previous_deployment['version']}")
        else:
            self.logger.warning("No previous deployment found for rollback")
    
    def _get_previous_deployment(self) -> Optional[Dict]:
        """Get previous successful deployment"""
        for deployment in reversed(self.deployment_log[:-1]):
            if deployment.get("status") == "completed":
                return deployment
        return None
    
    def get_deployment_status(self) -> Dict:
        """Get current deployment status"""
        status = {
            "deployment_id": self.deployment_id,
            "status": self.deployment_status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time or time.time()) - self.start_time if self.start_time else 0
        }
        
        if self.current_deployment:
            status.update(self.current_deployment)
        
        return status
    
    def get_deployment_history(self, limit: int = 10) -> List[Dict]:
        """Get deployment history"""
        return self.deployment_log[-limit:]


class CICDPipeline:
    """CI/CD pipeline automation"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.deployment_manager = DeploymentManager(config)
        self.logger = logging.getLogger("worldwidecoin.cicd")
    
    def run_pipeline(self, trigger: str = "manual") -> Dict:
        """Run complete CI/CD pipeline"""
        pipeline_id = f"pipeline-{int(time.time())}"
        
        pipeline_stages = [
            ("source", self._checkout_source),
            ("build", self._build_stage),
            ("test", self._test_stage),
            ("security_scan", self._security_scan),
            ("deploy_staging", self._deploy_to_staging),
            ("integration_test", self._integration_test),
            ("deploy_production", self._deploy_to_production),
            ("post_deploy_test", self._post_deploy_test)
        ]
        
        results = {
            "pipeline_id": pipeline_id,
            "trigger": trigger,
            "start_time": time.time(),
            "stages": {},
            "status": "running"
        }
        
        try:
            for stage_name, stage_func in pipeline_stages:
                self.logger.info(f"Running stage: {stage_name}")
                
                stage_start = time.time()
                stage_result = stage_func()
                stage_duration = time.time() - stage_start
                
                results["stages"][stage_name] = {
                    "status": "success" if stage_result else "failed",
                    "duration": stage_duration,
                    "result": stage_result
                }
                
                if not stage_result:
                    results["status"] = "failed"
                    break
            
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            
            if results["status"] == "running":
                results["status"] = "success"
            
            self.logger.info(f"Pipeline {pipeline_id} completed with status: {results['status']}")
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = time.time()
            
            self.logger.error(f"Pipeline {pipeline_id} failed: {e}")
        
        return results
    
    def _checkout_source(self) -> bool:
        """Checkout source code"""
        try:
            # Git checkout (simplified)
            result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _build_stage(self) -> bool:
        """Build stage"""
        try:
            # Build application
            result = subprocess.run(["python3", "setup.py", "build"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _test_stage(self) -> bool:
        """Test stage"""
        try:
            # Run tests
            result = subprocess.run(["python3", "-m", "pytest", "tests/"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _security_scan(self) -> bool:
        """Security scan stage"""
        try:
            # Run security scan (simplified)
            result = subprocess.run(["python3", "-m", "bandit", "-r", "."], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _deploy_to_staging(self) -> bool:
        """Deploy to staging"""
        try:
            # Deploy to staging environment
            staging_config = DeploymentConfig(
                environment="staging",
                desired_instances=2
            )
            
            staging_manager = DeploymentManager(staging_config)
            deployment_id = staging_manager.start_deployment()
            
            # Wait for deployment to complete
            for _ in range(60):  # Wait up to 10 minutes
                status = staging_manager.get_deployment_status()
                if status["status"] in ["completed", "failed"]:
                    return status["status"] == "completed"
                time.sleep(10)
            
            return False
        except Exception:
            return False
    
    def _integration_test(self) -> bool:
        """Integration test stage"""
        try:
            # Run integration tests against staging
            result = subprocess.run(["python3", "test_staging.py"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _deploy_to_production(self) -> bool:
        """Deploy to production"""
        try:
            deployment_id = self.deployment_manager.start_deployment()
            
            # Wait for deployment to complete
            for _ in range(120):  # Wait up to 20 minutes
                status = self.deployment_manager.get_deployment_status()
                if status["status"] in ["completed", "failed"]:
                    return status["status"] == "completed"
                time.sleep(10)
            
            return False
        except Exception:
            return False
    
    def _post_deploy_test(self) -> bool:
        """Post-deployment test stage"""
        try:
            # Run smoke tests against production
            result = subprocess.run(["python3", "test_smoke.py"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False


class DeploymentAutomation:
    """Main deployment automation coordinator"""
    
    def __init__(self, config_file: str = "deployment_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.deployment_manager = DeploymentManager(self.config)
        self.cicd_pipeline = CICDPipeline(self.config)
        
        print("Deployment automation initialized")
    
    def _load_config(self) -> DeploymentConfig:
        """Load deployment configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                return DeploymentConfig(**data)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return DeploymentConfig()
    
    def save_config(self):
        """Save deployment configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def deploy(self, version: str = None) -> str:
        """Deploy application"""
        return self.deployment_manager.start_deployment(version)
    
    def run_pipeline(self, trigger: str = "manual") -> Dict:
        """Run CI/CD pipeline"""
        return self.cicd_pipeline.run_pipeline(trigger)
    
    def get_status(self) -> Dict:
        """Get deployment status"""
        return {
            "config": asdict(self.config),
            "deployment_status": self.deployment_manager.get_deployment_status(),
            "deployment_history": self.deployment_manager.get_deployment_history()
        }


# Utility functions
def create_deployment_config() -> DeploymentConfig:
    """Create default deployment configuration"""
    return DeploymentConfig(
        environment="production",
        version="latest",
        region="us-west-2",
        instance_type="t3.medium",
        min_instances=3,
        max_instances=10,
        desired_instances=5
    )


def setup_deployment_automation(config_file: str = "deployment_config.json") -> DeploymentAutomation:
    """Setup deployment automation system"""
    print("Setting up deployment automation...")
    
    # Create default config if doesn't exist
    if not os.path.exists(config_file):
        config = create_deployment_config()
        
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
        
        print(f"Created default config: {config_file}")
    
    automation = DeploymentAutomation(config_file)
    
    print("Deployment automation setup complete")
    return automation
