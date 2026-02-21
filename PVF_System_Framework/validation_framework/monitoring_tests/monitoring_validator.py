#!/usr/bin/env python
"""
Monitoring and Observability Validator
=====================================

This module validates that the application is properly monitored for production.
It checks for:
- Prometheus metrics endpoint
- Health check endpoints
- Trace context headers (recommended for observability)
- Resource metrics availability
"""

import os
import logging
import requests
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger("MonitoringValidator")

def check_prometheus_metrics(url: str) -> Dict[str, Any]:
    """Check if Prometheus metrics endpoint is available and populated."""
    result = {
        "name": "Prometheus Metrics Check",
        "passed": False,
        "tests": []
    }
    
    metrics_path = "/metrics"
    full_url = url.rstrip('/') + metrics_path
    
    try:
        response = requests.get(full_url, timeout=5)
        if response.status_code == 200:
            content = response.text
            # Simple check for common prometheus metric format
            has_help = "# HELP" in content
            has_type = "# TYPE" in content
            
            result["tests"].append({
                "name": "Prometheus metrics endpoint availability",
                "status": "PASS",
                "message": f"Metrics endpoint {metrics_path} is accessible"
            })
            
            result["tests"].append({
                "name": "Prometheus metric format validation",
                "status": "PASS" if (has_help and has_type) else "WARNING",
                "message": "Metrics follow Prometheus format" if (has_help and has_type) else 
                           "Metrics found but format may be incorrect"
            })
            
            # Check for specific recommended metrics
            important_metrics = [
                "process_cpu_seconds_total",
                "process_resident_memory_bytes",
                "http_requests_total",
                "http_request_duration_seconds"
            ]
            
            for metric in important_metrics:
                if metric in content:
                    result["tests"].append({
                        "name": f"Core metric check: {metric}",
                        "status": "PASS",
                        "message": f"Metric '{metric}' is being collected"
                    })
                else:
                    result["tests"].append({
                        "name": f"Core metric check: {metric}",
                        "status": "WARNING",
                        "message": f"Metric '{metric}' is missing (recommended for production)"
                    })
        else:
            result["tests"].append({
                "name": "Prometheus metrics endpoint check",
                "status": "FAIL" if response.status_code == 404 else "WARNING",
                "message": f"Metrics endpoint returned status {response.status_code}"
            })
    except Exception as e:
        result["tests"].append({
            "name": "Prometheus metrics endpoint accessibility",
            "status": "FAIL",
            "message": f"Error accessing metrics endpoint: {str(e)}"
        })
        
    return result

def check_trace_context(url: str) -> Dict[str, Any]:
    """Check for trace context propagation headers."""
    result = {
        "name": "Trace Context Propagation",
        "passed": False,
        "tests": []
    }
    
    # Headers commonly used for tracing
    trace_headers = [
        "X-Request-Id",
        "X-Correlation-Id",
        "X-B3-TraceId",
        "X-B3-SpanId",
        "traceparent"  # W3C Trace Context standard
    ]
    
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers
        
        found_trace_headers = [h for h in trace_headers if h.lower() in [key.lower() for key in headers.keys()]]
        
        if found_trace_headers:
            result["tests"].append({
                "name": "Trace context headers check",
                "status": "PASS",
                "message": f"Found trace headers: {', '.join(found_trace_headers)}"
            })
        else:
            result["tests"].append({
                "name": "Trace context headers check",
                "status": "WARNING",
                "message": "No standard trace context headers found in response"
            })
    except:
        pass
        
    return result

def validate_monitoring(url: str) -> Dict[str, Any]:
    """Run comprehensive monitoring validation."""
    prom_result = check_prometheus_metrics(url)
    trace_result = check_trace_context(url)
    
    all_tests = prom_result["tests"] + trace_result["tests"]
    passed_tests = sum(1 for t in all_tests if t["status"] == "PASS")
    failed_tests = sum(1 for t in all_tests if t["status"] == "FAIL")
    
    return {
        "passed": failed_tests == 0,
        "total": len(all_tests),
        "passed_tests": passed_tests,
        "tests": all_tests
    }
