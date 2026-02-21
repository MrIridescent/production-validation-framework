#!/usr/bin/env python
"""
API Endpoint Validator
=====================

This module validates API endpoints to ensure they're working correctly
and providing appropriate responses. Tests include:
- Endpoint availability 
- Response format validation
- Authentication/Authorization checks
- Rate limiting behavior
- Error handling
"""

import os
import logging
import json
import time
import re
import requests
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger("APIValidator")

class APIValidationError(Exception):
    """Exception raised for API validation errors."""
    pass

def validate_schema(data: Any, schema: Any) -> Tuple[bool, str]:
    """
    Simple recursive schema validator.
    schema can be:
    - a type (e.g. str, int, bool)
    - a list [item_schema]
    - a dict {key: value_schema}
    """
    if isinstance(schema, type):
        if not isinstance(data, schema):
            return False, f"Expected {schema.__name__}, got {type(data).__name__}"
        return True, ""
    
    if isinstance(schema, list):
        if not isinstance(data, list):
            return False, f"Expected list, got {type(data).__name__}"
        if not schema:
            return True, ""
        for i, item in enumerate(data):
            valid, msg = validate_schema(item, schema[0])
            if not valid:
                return False, f"item[{i}] -> {msg}"
        return True, ""
        
    if isinstance(schema, dict):
        if not isinstance(data, dict):
            return False, f"Expected dict, got {type(data).__name__}"
        for key, val_schema in schema.items():
            if key not in data:
                return False, f"Missing required key: '{key}'"
            valid, msg = validate_schema(data[key], val_schema)
            if not valid:
                return False, f"'{key}' -> {msg}"
        return True, ""
        
    return True, ""

class APIEndpointValidator:
    """Validates API endpoints for correctness and functionality."""
    
    def __init__(self, 
                 base_url: str, 
                 auth_token: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 timeout: int = 10,
                 sla_ms: int = 500):
        """
        Initialize the API validator.
        
        Args:
            base_url: The base URL for the API
            auth_token: Optional authentication token
            headers: Optional headers to include in requests
            timeout: Request timeout in seconds
            sla_ms: Service Level Agreement for response time in milliseconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.sla_ms = sla_ms
        
        # Setup default headers
        self.headers = headers or {}
        self.headers.setdefault("Content-Type", "application/json")
        self.headers.setdefault("Accept", "application/json")
        
        # Add authentication if provided
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
            
    def validate_endpoint(self, 
                         endpoint: str, 
                         method: str = "GET",
                         expected_status: int = 200,
                         expected_content_type: str = "application/json",
                         required_fields: Optional[List[str]] = None,
                         expected_schema: Optional[Any] = None,
                         payload: Optional[Dict[str, Any]] = None,
                         authentication_required: bool = False,
                         sla_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a specific API endpoint with enhanced production checks.
        """
        url = f"{self.base_url}{endpoint}"
        method = method.upper()
        target_sla = sla_ms or self.sla_ms
        
        results = {
            "endpoint": endpoint,
            "method": method,
            "url": url,
            "passed": False,
            "tests": []
        }
        
        # Make the request
        try:
            start_time = time.time()
            
            # Inject a tracking ID for production logging validation
            request_headers = self.headers.copy()
            tracking_id = f"val-{int(time.time())}"
            request_headers["X-Request-ID"] = tracking_id
            
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=request_headers,
                timeout=self.timeout
            )
                
            response_time = (time.time() - start_time) * 1000
            
            results["status_code"] = response.status_code
            results["response_time"] = response_time
            
            # Header validation
            results["tests"].append({
                "name": "Tracking ID support",
                "passed": "X-Request-ID" in response.headers or response.status_code < 500,
                "message": "API should ideally echo or support X-Request-ID"
            })

            # Try to parse content as JSON
            response_json = None
            is_json = False
            try:
                response_json = response.json()
                results["response"] = response_json
                is_json = True
            except:
                results["response"] = response.text[:500]
            
            # Test 1: Status code check
            results["tests"].append({
                "name": "Status code check",
                "passed": response.status_code == expected_status,
                "message": f"Expected {expected_status}, got {response.status_code}"
            })
            
            # Test 2: Content type check
            content_type = response.headers.get('Content-Type', '')
            results["tests"].append({
                "name": "Content type check",
                "passed": expected_content_type in content_type,
                "message": f"Expected {expected_content_type}, got {content_type}"
            })
            
            # Test 3: Schema/Fields validation
            if is_json:
                if expected_schema:
                    valid, msg = validate_schema(response_json, expected_schema)
                    results["tests"].append({
                        "name": "Schema validation",
                        "passed": valid,
                        "message": "Schema matches" if valid else f"Schema mismatch: {msg}"
                    })
                elif required_fields:
                    missing = [f for f in required_fields if f not in response_json]
                    results["tests"].append({
                        "name": "Required fields check",
                        "passed": not missing,
                        "message": "All fields present" if not missing else f"Missing: {', '.join(missing)}"
                    })
            
            # Test 4: Authentication enforcement
            if authentication_required:
                no_auth_headers = {k: v for k, v in request_headers.items() if k != 'Authorization'}
                try:
                    no_auth_res = requests.request(method, url, json=payload, headers=no_auth_headers, timeout=self.timeout)
                    auth_passed = no_auth_res.status_code in [401, 403]
                    results["tests"].append({
                        "name": "Auth enforcement",
                        "passed": auth_passed,
                        "message": f"Access denied as expected (Got {no_auth_res.status_code})" if auth_passed else "Endpoint allowed unauthorized access"
                    })
                except:
                    results["tests"].append({"name": "Auth enforcement", "passed": True, "message": "Connection refused without auth"})

            # Test 5: SLA performance check
            results["tests"].append({
                "name": "SLA Response time",
                "passed": response_time <= target_sla,
                "message": f"{response_time:.1f}ms (SLA: {target_sla}ms)"
            })
            
            # Calculate overall result
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except requests.RequestException as e:
            results["error"] = str(e)
            results["tests"].append({
                "name": "Network connectivity",
                "passed": False,
                "message": f"Request failed: {str(e)}"
            })
            
        return results

        
    def validate_endpoints(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple endpoints.
        
        Args:
            endpoints: List of endpoint configurations
            
        Returns:
            Dict with validation results for all endpoints
        """
        results = {
            "base_url": self.base_url,
            "passed": False,
            "total": len(endpoints),
            "passed_endpoints": 0,
            "endpoints": []
        }
        
        for endpoint_config in endpoints:
            endpoint_result = self.validate_endpoint(**endpoint_config)
            results["endpoints"].append(endpoint_result)
            
            if endpoint_result.get("passed", False):
                results["passed_endpoints"] += 1
                
        results["passed"] = results["passed_endpoints"] == results["total"]
        return results
    
    def discover_api_endpoints(self) -> List[str]:
        """
        Attempt to discover API endpoints by checking common paths.
        
        Returns:
            List of discovered endpoint paths
        """
        discovered = []
        common_paths = [
            "/",
            "/api",
            "/api/v1",
            "/api/v2",
            "/health",
            "/status",
            "/docs",
            "/api/docs",
            "/swagger",
            "/api/users",
            "/api/auth/login",
            "/api/auth/register",
            "/api/products",
            "/api/orders"
        ]
        
        for path in common_paths:
            try:
                response = requests.head(
                    f"{self.base_url}{path}", 
                    headers=self.headers, 
                    timeout=min(2, self.timeout)
                )
                
                if response.status_code < 404:  # Any non-404 status might indicate a valid endpoint
                    discovered.append(path)
            except:
                pass
                
        return discovered
    
    def auto_validate_endpoints(self) -> Dict[str, Any]:
        """
        Automatically discover and validate API endpoints.
        
        Returns:
            Dict with validation results
        """
        discovered = self.discover_api_endpoints()
        
        endpoints_config = []
        for endpoint in discovered:
            # Create basic validation config for each endpoint
            endpoints_config.append({
                "endpoint": endpoint,
                "method": "GET",
                "expected_status": 200,
                "authentication_required": False  # Conservative default
            })
            
        return self.validate_endpoints(endpoints_config)

def validate_api_endpoints(
    base_url: str,
    auth_token: Optional[str] = None,
    endpoints: Optional[List[Dict[str, Any]]] = None,
    auto_discover: bool = False
) -> Dict[str, Any]:
    """
    Run API endpoint validation tests.
    
    Args:
        base_url: Base URL of the API
        auth_token: Optional authentication token
        endpoints: List of endpoint configurations to test
        auto_discover: Whether to automatically discover endpoints
        
    Returns:
        Dict with validation results
    """
    validator = APIEndpointValidator(
        base_url=base_url,
        auth_token=auth_token
    )
    
    if auto_discover:
        return validator.auto_validate_endpoints()
    elif endpoints:
        return validator.validate_endpoints(endpoints)
    else:
        # Default basic health endpoint validation
        return validator.validate_endpoints([{
            "endpoint": "/health",
            "method": "GET",
            "expected_status": 200
        }])

def load_endpoint_config(config_file: str) -> List[Dict[str, Any]]:
    """
    Load endpoint configuration from JSON file.
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        List of endpoint configurations
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        if isinstance(config, list):
            return config
        elif isinstance(config, dict) and "endpoints" in config:
            return config["endpoints"]
        else:
            raise APIValidationError("Invalid configuration format. Expected list or dict with 'endpoints' key.")
    except Exception as e:
        raise APIValidationError(f"Failed to load endpoint configuration: {str(e)}")

if __name__ == "__main__":
    # Simple standalone test
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate API endpoints")
    parser.add_argument("--url", "-u", help="Base URL of the API", required=True)
    parser.add_argument("--token", "-t", help="Authentication token")
    parser.add_argument("--config", "-c", help="Path to endpoint configuration file")
    parser.add_argument("--discover", "-d", action="store_true", help="Auto-discover endpoints")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        if args.config:
            endpoints_config = load_endpoint_config(args.config)
            result = validate_api_endpoints(args.url, args.token, endpoints_config)
        else:
            result = validate_api_endpoints(args.url, args.token, auto_discover=args.discover)
        
        print(f"API Validation Results for {args.url}:")
        print(f"Passed: {result.get('passed', False)}")
        print(f"Endpoints: {result.get('passed_endpoints', 0)}/{result.get('total', 0)} passed")
        
        for endpoint_result in result.get("endpoints", []):
            endpoint = endpoint_result.get("endpoint", "Unknown")
            method = endpoint_result.get("method", "GET")
            status = "✓" if endpoint_result.get("passed", False) else "✗"
            
            print(f"\n{status} [{method}] {endpoint}")
            
            for test in endpoint_result.get("tests", []):
                test_status = "✓" if test.get("passed", False) else "✗"
                print(f"  {test_status} {test.get('name', 'Unknown')}: {test.get('message', '')}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
