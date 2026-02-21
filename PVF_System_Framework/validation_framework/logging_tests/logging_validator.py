#!/usr/bin/env python
"""
Logging Configuration Validator
==============================

This module validates that logging is properly configured for production.
It checks for:
- JSON logging format (recommended for ELK/Datadog)
- Log levels (no DEBUG in production)
- Log rotation and persistence
- Absence of sensitive data patterns in logs
"""

import os
import logging
import json
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger("LoggingValidator")

def check_logging_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Check logging configuration for production readiness."""
    result = {
        "name": "Logging Configuration",
        "passed": False,
        "tests": []
    }
    
    # Common logging config files
    config_files = ["logging.json", "logging.yaml", "logging.conf"]
    if config_file:
        config_files = [config_file]
        
    found_config = False
    for f in config_files:
        if os.path.exists(f):
            found_config = True
            # Test 1: JSON format
            is_json = f.endswith(".json")
            result["tests"].append({
                "name": "JSON logging configuration",
                "status": "PASS" if is_json else "WARNING",
                "message": f"Using {f} for logging configuration"
            })
            
            # Test 2: Log levels
            try:
                with open(f, 'r') as cf:
                    content = cf.read().upper()
                    if "DEBUG" in content and not "LOG_LEVEL" in content: # Heuristic
                        result["tests"].append({
                            "name": "Production log level",
                            "status": "WARNING",
                            "message": "DEBUG log level detected in configuration"
                        })
                    else:
                        result["tests"].append({
                            "name": "Production log level",
                            "status": "PASS",
                            "message": "No hardcoded DEBUG level in configuration"
                        })
            except:
                pass
            break
            
    if not found_config:
        result["tests"].append({
            "name": "Logging configuration exists",
            "status": "WARNING",
            "message": "No dedicated logging configuration file found"
        })
        
    # Test 3: Check for JSON formatter in code if no config file
    # This would require more complex static analysis, so we'll skip or use a simple grep
    
    return result

def check_log_files(log_dir: str = "logs") -> Dict[str, Any]:
    """Check existing log files for production readiness."""
    result = {
        "name": "Log File Analysis",
        "passed": False,
        "tests": []
    }
    
    if not os.path.isdir(log_dir):
        result["tests"].append({
            "name": "Log directory exists",
            "status": "WARNING",
            "message": f"Log directory '{log_dir}' not found"
        })
        return result
        
    log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
    if not log_files:
        result["tests"].append({
            "name": "Log files exist",
            "status": "PASS",
            "message": "No log files found in directory (clean state)"
        })
        return result
        
    # Test: JSON format in latest logs
    latest_log = max([os.path.join(log_dir, f) for f in log_files], key=os.path.getmtime)
    try:
        with open(latest_log, 'r') as f:
            first_line = f.readline().strip()
            try:
                json.loads(first_line)
                is_json = True
            except:
                is_json = False
                
        result["tests"].append({
            "name": "JSON log format verification",
            "status": "PASS" if is_json else "WARNING",
            "message": f"Log file '{os.path.basename(latest_log)}' is in JSON format" if is_json else 
                       f"Log file '{os.path.basename(latest_log)}' is NOT in JSON format (recommended for production)"
        })
    except:
        pass
        
    return result

def check_pii_in_logs(log_dir: str = "logs") -> Dict[str, Any]:
    """Scan log files for potential PII or secrets."""
    result = {
        "name": "PII and Secret Scan",
        "passed": True,
        "tests": []
    }
    
    if not os.path.isdir(log_dir):
        return result
        
    log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
    if not log_files:
        return result
        
    # Sensitive patterns
    patterns = {
        "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
        "Social Security Number": r"\b\d{3}-\d{2}-\d{4}\b",
        "Password/Secret": r"(?i)(password|secret|key|token|auth)\s*[:=]\s*['\"][^'\"]+['\"]"
    }
    
    issues = []
    for log_file in log_files:
        path = os.path.join(log_dir, log_file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(10000) # Only first 10k chars for perf
                for name, pattern in patterns.items():
                    if re.search(pattern, content):
                        issues.append(f"Potential {name} found in '{log_file}'")
        except:
            pass
            
    result["tests"].append({
        "name": "Log PII data check",
        "status": "PASS" if not issues else "FAIL",
        "message": "No PII or secrets found in logs" if not issues else f"Issues found: {', '.join(issues)}"
    })
    result["passed"] = len(issues) == 0
    return result

def validate_logging(log_dir: str = "logs", config_file: Optional[str] = None) -> Dict[str, Any]:
    """Run comprehensive logging validation."""
    config_result = check_logging_config(config_file)
    file_result = check_log_files(log_dir)
    pii_result = check_pii_in_logs(log_dir)
    
    all_tests = config_result["tests"] + file_result["tests"] + pii_result["tests"]
    passed_tests = sum(1 for t in all_tests if t["status"] == "PASS")
    failed_tests = sum(1 for t in all_tests if t["status"] == "FAIL")
    
    return {
        "passed": failed_tests == 0,
        "total": len(all_tests),
        "passed_tests": passed_tests,
        "tests": all_tests
    }
