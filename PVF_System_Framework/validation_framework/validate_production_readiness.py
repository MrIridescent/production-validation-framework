#!/usr/bin/env python
"""
Production Readiness Validation Framework
========================================

This script runs a comprehensive suite of validation tests to ensure a project
is production-ready. It checks configuration, security, performance, API endpoints,
and deployment readiness.

Usage:
    python validate_production_readiness.py [--config CONFIG_PATH] [--report-path REPORT_PATH]

Example:
    python validate_production_readiness.py --config ./config/validation_config.json --report-path ./reports

Author: Enterprise Platform Team
Date: July 11, 2025
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Add validators and test modules
try:
    from .config_validators import env_validator, db_validator
    from .security_tests import security_scanner
    from .performance_tests import load_tester
    from .api_tests import api_validator
    from .deployment_checks import deployment_validator
    from .logging_tests import logging_validator
    from .monitoring_tests import monitoring_validator
    from .report_generator import generate_html_report
except ImportError:
    from config_validators import env_validator, db_validator
    from security_tests import security_scanner
    from performance_tests import load_tester
    from api_tests import api_validator
    from deployment_checks import deployment_validator
    from logging_tests import logging_validator
    from monitoring_tests import monitoring_validator
    from report_generator import generate_html_report

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "validation.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("ProductionValidator")

class ProductionValidator:
    """Main class for validating production readiness."""
    
    def __init__(self, config_path: str = "validation_framework/validation_config.json"):
        """Initialize the validator with configuration settings."""
        self.start_time = time.time()
        self.config = self._load_config(config_path)
        self.results: Dict[str, Dict[str, Any]] = {}
        self.passed_tests = 0
        self.failed_tests = 0
        self.warning_tests = 0
        self.total_tests = 0
        
        logger.info(f"Initialized Production Validator with config from {config_path}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from the specified JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            logger.info("Using default configuration")
            return {
                "env_file_path": ".env",
                "api_base_url": "http://localhost:8000",
                "test_timeout": 30,
                "db_connection_string": "postgresql://username:password@localhost:5432/enterprise_platform",
                "required_services": ["database", "cache", "storage"],
                "validate_sections": [
                    "env_config", "security", "performance", 
                    "api_endpoints", "database", "deployment",
                    "logging", "monitoring"
                ],
                "log_dir": "logs",
                "performance": {
                    "load_test_users": 50,
                    "load_test_duration": 60,
                    "max_response_time": 500,  # ms
                    "max_cpu_usage": 80,  # percentage
                    "max_memory_usage": 80  # percentage
                },
                "security": {
                    "scan_severity": "high",
                    "check_ssl": True,
                    "check_headers": True,
                    "check_auth": True
                }
            }

    def run_validations(self) -> Dict[str, Dict[str, Any]]:
        """Run all validation tests based on the configuration."""
        logger.info("Starting production validation suite")
        
        if "env_config" in self.config["validate_sections"]:
            self._run_env_validation()
            
        if "security" in self.config["validate_sections"]:
            self._run_security_tests()
            
        if "performance" in self.config["validate_sections"]:
            self._run_performance_tests()
            
        if "api_endpoints" in self.config["validate_sections"]:
            self._run_api_tests()
            
        if "database" in self.config["validate_sections"]:
            self._run_database_tests()
            
        if "deployment" in self.config["validate_sections"]:
            self._run_deployment_checks()
            
        if "logging" in self.config["validate_sections"]:
            self._run_logging_tests()
            
        if "monitoring" in self.config["validate_sections"]:
            self._run_monitoring_tests()
            
        duration = time.time() - self.start_time
        logger.info(f"Validation suite completed in {duration:.2f} seconds")
        logger.info(f"Results: {self.passed_tests} passed, {self.failed_tests} failed, {self.warning_tests} warnings")
        
        self._add_summary()
        return self.results
    
    def _add_summary(self):
        """Add summary statistics to the results."""
        self.results["summary"] = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "duration_seconds": time.time() - self.start_time,
            "tests_passed": self.passed_tests,
            "tests_failed": self.failed_tests,
            "tests_warned": self.warning_tests,
            "total_tests": self.total_tests,
            "pass_percentage": (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0,
            "production_ready": self.failed_tests == 0
        }

    def _run_env_validation(self):
        """Validate environment variables configuration."""
        logger.info("Validating environment configuration")
        
        env_results = env_validator.validate_env_file(
            self.config["env_file_path"],
            required_sections=[
                "CORE PLATFORM CONFIGURATION",
                "DATABASE CONFIGURATION",
                "JWT AUTHENTICATION & SECURITY"
            ]
        )
        
        self.results["env_config"] = env_results
        self._update_test_counts(env_results["tests"])
        
        logger.info(f"Environment validation complete: {env_results['passed']}/{env_results['total']} checks passed")

    def _run_security_tests(self):
        """Run security tests on the application."""
        logger.info("Running security tests")
        
        security_results = security_scanner.run_security_scan(
            base_url=self.config["api_base_url"],
            scan_severity=self.config["security"]["scan_severity"],
            check_ssl=self.config["security"]["check_ssl"],
            check_headers=self.config["security"]["check_headers"],
            check_auth=self.config["security"]["check_auth"]
        )
        
        self.results["security"] = security_results
        self._update_test_counts(security_results["tests"])
        
        logger.info(f"Security tests complete: {security_results['passed']}/{security_results['total']} checks passed")

    def _run_performance_tests(self):
        """Run performance tests on the application."""
        logger.info("Running performance tests")
        
        # Load testing
        load_test_results = load_tester.run_load_test(
            base_url=self.config["api_base_url"],
            num_users=self.config["performance"]["load_test_users"],
            duration=self.config["performance"]["load_test_duration"],
            max_response_time=self.config["performance"]["max_response_time"]
        )
        
        self.results["performance"] = {
            "load_test": load_test_results,
            "passed": load_test_results["passed"],
            "total": load_test_results["total"],
            "passed_tests": load_test_results["passed_tests"]
        }
        
        self._update_test_counts(load_test_results["tests"])
        
        logger.info(f"Performance tests complete: {self.results['performance']['passed_tests']}/{self.results['performance']['total']} checks passed")

    def _run_api_tests(self):
        """Validate API endpoints and integrations."""
        logger.info("Validating API endpoints")
        
        # API validation using our new validator
        api_results = api_validator.validate_api_endpoints(
            base_url=self.config["api_base_url"],
            auto_discover=True
        )
        
        self.results["api"] = {
            "endpoints": api_results,
            "passed": api_results["passed"],
            "total": api_results["total"],
            "passed_tests": api_results["passed_endpoints"]
        }
        
        # Add tests from each endpoint to the test count
        for endpoint_result in api_results.get("endpoints", []):
            self._update_test_counts(endpoint_result.get("tests", []))
        
        logger.info(f"API validation complete: {self.results['api']['passed_tests']}/{self.results['api']['total']} checks passed")

    def _run_database_tests(self):
        """Run database validation tests."""
        logger.info("Validating database configuration")
        
        db_results = db_validator.validate_database(
            connection_string=self.config["db_connection_string"]
        )
        
        self.results["database"] = db_results
        self._update_test_counts(db_results["tests"])
        
        logger.info(f"Database validation complete: {db_results['passed']}/{db_results['total']} checks passed")

    def _run_deployment_checks(self):
        """Run deployment readiness checks."""
        logger.info("Checking deployment readiness")
        
        deployment_results = deployment_validator.validate_deployment_readiness(
            project_root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Extract tests from sections
        for section in deployment_results.get("sections", []):
            self._update_test_counts(section.get("tests", []))
        
        self.results["deployment"] = deployment_results
        
        logger.info(f"Deployment checks complete: {deployment_results['passed_tests']}/{deployment_results['total']} checks passed")

    def _run_logging_tests(self):
        """Run logging validation tests."""
        logger.info("Validating logging configuration")
        
        logging_results = logging_validator.validate_logging(
            log_dir=self.config.get("log_dir", "logs"),
            config_file=self.config.get("logging_config_file")
        )
        
        self.results["logging"] = logging_results
        self._update_test_counts(logging_results["tests"])
        
        logger.info(f"Logging validation complete: {logging_results['passed_tests']}/{logging_results['total']} checks passed")

    def _run_monitoring_tests(self):
        """Run monitoring and observability tests."""
        logger.info("Validating monitoring configuration")
        
        monitoring_results = monitoring_validator.validate_monitoring(
            url=self.config["api_base_url"]
        )
        
        self.results["monitoring"] = monitoring_results
        self._update_test_counts(monitoring_results["tests"])
        
        logger.info(f"Monitoring validation complete: {monitoring_results['passed_tests']}/{monitoring_results['total']} checks passed")

    def _get_remediation(self, test_name: str, message: str) -> str:
        """Provide actionable advice for failed production checks."""
        advice_map = {
            "Database Table check": "Initialize database schema using the migration system or setup scripts.",
            "Production log level": "Set LOG_LEVEL to INFO or WARN in production environment configuration.",
            "JSON log format verification": "Configure a JSON formatter (e.g. python-json-logger) for easier log aggregation.",
            "SLA Response time": "Investigate bottleneck using a profiler. Consider caching, indexing, or horizontal scaling.",
            "Critical security header": "Add the missing header in your web server (Nginx/Apache) or application middleware.",
            "Dockerfile best practices": "Review the Dockerfile to use specific version tags, non-root users, and multi-stage builds.",
            "PII and Secret Scan": "Ensure secrets are not logged and implement log masking for sensitive data.",
            "Schema validation": "Verify that API response body matches the contract. Update models or documentation.",
            "Tracking ID support": "Ensure 'X-Request-ID' is accepted and echoed in responses for distributed tracing."
        }
        for key, advice in advice_map.items():
            if key in test_name:
                return advice
        return "Refer to internal architectural standards for production readiness."

    def _update_test_counts(self, tests: List[Dict[str, Any]]):
        """Update the overall test counts based on test results."""
        for test in tests:
            self.total_tests += 1
            status = test.get("status")
            passed = test.get("passed")
            
            if status == "PASS" or passed is True:
                self.passed_tests += 1
            elif status == "FAIL" or passed is False:
                self.failed_tests += 1
                test["remediation"] = self._get_remediation(test.get("name", ""), test.get("message", ""))
            elif status == "WARNING":
                self.warning_tests += 1
                test["remediation"] = self._get_remediation(test.get("name", ""), test.get("message", ""))

    def generate_report(self, report_path: str) -> str:
        """Generate a detailed HTML and JSON report of validation results."""
        if not os.path.exists(report_path):
            os.makedirs(report_path)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(report_path, f"validation_report_{timestamp}.json")
        html_path = os.path.join(report_path, f"validation_report_{timestamp}.html")
        
        # Save JSON report
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        # Generate HTML report
        generate_html_report(self.results, html_path)
        
        logger.info(f"Reports generated at {json_path} and {html_path}")
        return html_path

def main():
    """Main function to run the validation suite."""
    parser = argparse.ArgumentParser(description="Validate production readiness of the application")
    parser.add_argument('--config', default='validation_config.json', help='Path to the validation configuration file')
    parser.add_argument('--report-path', default='./validation_reports', help='Directory to save the validation reports')
    args = parser.parse_args()
    
    validator = ProductionValidator(args.config)
    results = validator.run_validations()
    report_path = validator.generate_report(args.report_path)
    
    if results["summary"]["production_ready"]:
        logger.info("✅ Application is PRODUCTION READY!")
        logger.info(f"Detailed report available at: {report_path}")
        sys.exit(0)
    else:
        logger.error("❌ Application is NOT PRODUCTION READY. Please fix the failed tests.")
        logger.info(f"Detailed report available at: {report_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
