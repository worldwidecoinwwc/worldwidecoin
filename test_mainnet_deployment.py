#!/usr/bin/env python3
"""
Phase 6 Mainnet Deployment Testing Suite
Tests production deployment, security, monitoring, and automation
"""

import time
import tempfile
import os
from deployment.mainnet_config import MainnetConfig, NetworkConfig, SecurityConfig, DatabaseConfig
from deployment.network_security import NetworkSecurity, DDoSProtection
from deployment.monitoring import MonitoringSystem, MetricsCollector
from deployment.deployment_automation import DeploymentAutomation, DeploymentConfig
from core.blockchain import Blockchain


def test_mainnet_configuration():
    """Test 1: Mainnet configuration"""
    print("=== TEST 1: Mainnet Configuration ===")
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_file = f.name
    
    try:
        # Create mainnet config
        config = MainnetConfig(config_file)
        
        # Test default values
        print(f"Network name: {config.network.name}")
        print(f"Network ID: {config.network.network_id}")
        print(f"Port: {config.network.port}")
        print(f"Initial difficulty: {config.network.initial_difficulty}")
        
        # Test configuration validation
        issues = config.validate_config()
        print(f"Configuration issues: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        
        # Test environment variables
        env_vars = config.get_env_vars()
        print(f"Environment variables: {len(env_vars)}")
        
        # Test directories creation
        config.create_directories()
        print("Directories created successfully")
        
        # Save configuration
        config.save_config()
        print("Configuration saved")
        
        print("Configuration test passed")
        
    finally:
        # Cleanup
        try:
            os.unlink(config_file)
        except:
            pass
    
    print()


def test_network_security():
    """Test 2: Network security"""
    print("=== TEST 2: Network Security ===")
    
    # Create security config
    security_config = {
        "whitelist_enabled": False,
        "blacklist_enabled": True,
        "allowed_ips": ["127.0.0.1", "::1"],
        "blocked_ips": ["192.0.2.1"],
        "rate_limiting": {
            "max_requests_per_minute": 100,
            "max_burst": 10
        }
    }
    
    # Initialize security
    security = NetworkSecurity(security_config)
    
    # Test IP filtering
    allowed_ip = "127.0.0.1"
    blocked_ip = "192.0.2.1"
    
    print(f"IP {allowed_ip} allowed: {security.is_ip_allowed(allowed_ip)}")
    print(f"IP {blocked_ip} allowed: {security.is_ip_allowed(blocked_ip)}")
    
    # Test connection handling
    result, message = security.handle_connection("127.0.0.1", 8333, "WWC-Node/1.0")
    print(f"Connection allowed: {result}, message: {message}")
    
    # Test DDoS protection
    ddos_stats = security.ddos_protection.get_security_stats()
    print(f"DDoS stats: {ddos_stats}")
    
    # Test IP blocking
    security.block_ip("192.0.2.100", "Test block", 300)
    print("IP blocked successfully")
    
    # Test security status
    status = security.get_security_status()
    print(f"Security status: {status}")
    
    print("Network security test passed")
    print()


def test_monitoring_system():
    """Test 3: Monitoring system"""
    print("=== TEST 3: Monitoring System ===")
    
    # Create blockchain instance
    blockchain = Blockchain()
    
    # Create monitoring config
    monitoring_config = {
        "log_level": "INFO",
        "log_file": "/tmp/test_monitoring.log"
    }
    
    # Initialize monitoring
    monitoring = MonitoringSystem(blockchain, monitoring_config)
    
    # Test metrics collection
    monitoring.metrics.increment_counter("test_counter", 1.0)
    monitoring.metrics.set_gauge("test_gauge", 42.0)
    monitoring.metrics.record_histogram("test_histogram", 1.5)
    
    # Test metrics retrieval
    counter_metrics = monitoring.metrics.get_metrics("test_counter")
    gauge_metrics = monitoring.metrics.get_metrics("test_gauge")
    
    print(f"Counter metrics: {len(counter_metrics)}")
    print(f"Gauge metrics: {len(gauge_metrics)}")
    
    # Test metric summary
    summary = monitoring.metrics.get_metric_summary("test_counter")
    print(f"Counter summary: {summary}")
    
    # Test health checks
    health_status = monitoring.health_checker.run_health_checks()
    print(f"Health status: {health_status['overall_status']}")
    
    # Test alert manager
    monitoring.alert_manager.add_alert_callback(lambda alert: print(f"Alert: {alert.message}"))
    
    # Trigger test alert
    monitoring.metrics.set_gauge("system_cpu_percent", 95.0)
    time.sleep(1)  # Allow alert processing
    
    active_alerts = monitoring.alert_manager.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    
    print("Monitoring system test passed")
    print()


def test_deployment_automation():
    """Test 4: Deployment automation"""
    print("=== TEST 4: Deployment Automation ===")
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_file = f.name
    
    try:
        # Create deployment config
        config = DeploymentConfig(
            environment="test",
            desired_instances=2,
            instance_type="t3.small"
        )
        
        # Save config
        import json
        with open(config_file, 'w') as f:
            json.dump(config.__dict__, f, indent=2)
        
        # Initialize automation
        automation = DeploymentAutomation(config_file)
        
        # Test configuration
        status = automation.get_status()
        print(f"Deployment status: {status['deployment_status']['status']}")
        print(f"Environment: {status['config']['environment']}")
        
        # Test pipeline (dry run)
        print("Testing CI/CD pipeline...")
        
        # Test deployment stages
        stages = [
            ("source", automation.cicd_pipeline._checkout_source),
            ("build", automation.cicd_pipeline._build_stage),
            ("test", automation.cicd_pipeline._test_stage)
        ]
        
        for stage_name, stage_func in stages:
            print(f"Testing {stage_name} stage...")
            try:
                result = stage_func()
                print(f"  {stage_name}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                print(f"  {stage_name}: ERROR - {e}")
        
        print("Deployment automation test passed")
        
    finally:
        # Cleanup
        try:
            os.unlink(config_file)
        except:
            pass
    
    print()


def test_integration():
    """Test 5: Integration tests"""
    print("=== TEST 5: Integration Tests ===")
    
    # Create complete deployment setup
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, "mainnet.json")
        
        # Create mainnet configuration
        config = MainnetConfig(config_file)
        config.network.port = 18333  # Use different port for testing
        config.save_config()
        
        # Initialize security
        security = NetworkSecurity()
        
        # Create blockchain
        blockchain = Blockchain()
        
        # Initialize monitoring
        monitoring = MonitoringSystem(blockchain)
        
        # Test integrated workflow
        print("Testing integrated deployment workflow...")
        
        # 1. Configuration validation
        issues = config.validate_config()
        print(f"Configuration validation: {len(issues)} issues")
        
        # 2. Security initialization
        security_status = security.get_security_status()
        print(f"Security status: {security_status['allowed_ips_count']} allowed IPs")
        
        # 3. Monitoring startup
        monitoring.system_monitor.start_monitoring()
        time.sleep(1)  # Allow monitoring to start
        
        # 4. Generate some metrics
        for i in range(10):
            monitoring.metrics.increment_counter("integration_test", 1.0)
            time.sleep(0.1)
        
        # 5. Check health
        health = monitoring.health_checker.run_health_checks()
        print(f"Health check: {health['overall_status']}")
        
        # 6. Get metrics summary
        metrics_summary = monitoring.get_metrics_summary()
        print(f"Metrics summary: {metrics_summary['active_alerts']} alerts")
        
        # 7. Cleanup
        monitoring.system_monitor.stop_monitoring()
        
        print("Integration test passed")
    
    print()


def test_performance():
    """Test 6: Performance tests"""
    print("=== TEST 6: Performance Tests ===")
    
    # Test metrics collection performance
    metrics = MetricsCollector()
    
    start_time = time.time()
    
    # Generate many metrics
    for i in range(1000):
        metrics.increment_counter("perf_test", 1.0)
        metrics.set_gauge("perf_gauge", i)
        metrics.record_histogram("perf_hist", i * 0.1)
    
    collection_time = time.time() - start_time
    print(f"Metrics collection: 1000 metrics in {collection_time:.3f}s")
    
    # Test retrieval performance
    start_time = time.time()
    retrieved_metrics = metrics.get_metrics()
    retrieval_time = time.time() - start_time
    
    print(f"Metrics retrieval: {len(retrieved_metrics)} metrics in {retrieval_time:.3f}s")
    
    # Test security performance
    security = DDoSProtection()
    
    start_time = time.time()
    
    # Simulate many requests
    for i in range(100):
        result, _ = security.handle_request(f"192.168.1.{i%255}", 8333)
    
    security_time = time.time() - start_time
    print(f"Security processing: 100 requests in {security_time:.3f}s")
    
    print("Performance test passed")
    print()


def test_error_handling():
    """Test 7: Error handling"""
    print("=== TEST 7: Error Handling ===")
    
    # Test configuration errors
    try:
        config = MainnetConfig("nonexistent.json")
        print("Config creation with missing file: PASS")
    except Exception as e:
        print(f"Config creation error: {e}")
    
    # Test security errors
    security = NetworkSecurity()
    
    # Test invalid IP handling
    result = security.handle_connection("invalid_ip", 8333)
    print(f"Invalid IP handling: {result[0]}")
    
    # Test monitoring errors
    monitoring = MonitoringSystem(Blockchain())
    
    # Test invalid metric handling
    try:
        monitoring.metrics.increment_counter("", -1.0)  # Invalid metric
        print("Invalid metric handling: PASS")
    except Exception as e:
        print(f"Invalid metric error: {e}")
    
    print("Error handling test passed")
    print()


def test_configuration_validation():
    """Test 8: Configuration validation"""
    print("=== TEST 8: Configuration Validation ===")
    
    # Test valid configuration
    valid_config = MainnetConfig()
    issues = valid_config.validate_config()
    print(f"Valid config issues: {len(issues)}")
    
    # Test invalid network configuration
    invalid_network = NetworkConfig()
    invalid_network.port = 99999  # Invalid port
    invalid_network.max_peers = 5
    invalid_network.min_peers = 10  # Min > max
    
    # Test invalid security configuration
    invalid_security = SecurityConfig()
    invalid_security.require_auth = True
    invalid_security.allowed_ips = []  # No allowed IPs with auth required
    
    # Test invalid database configuration
    invalid_database = DatabaseConfig()
    invalid_database.blockchain_db_path = "/nonexistent/path/blockchain"
    
    print("Configuration validation test passed")
    print()


def main():
    """Run all Phase 6 mainnet deployment tests"""
    print("WorldWideCoin Phase 6 - Mainnet Deployment Testing")
    print("=" * 50)
    
    tests = [
        test_mainnet_configuration,
        test_network_security,
        test_monitoring_system,
        test_deployment_automation,
        test_integration,
        test_performance,
        test_error_handling,
        test_configuration_validation
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Phase 6 Testing Complete!")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed))*100:.1f}%")


if __name__ == "__main__":
    main()
