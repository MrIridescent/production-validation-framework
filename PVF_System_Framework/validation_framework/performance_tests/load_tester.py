#!/usr/bin/env python
"""
Load Tester Module
=================

This module performs load testing on the application to ensure it can
handle production-level traffic. Tests include:
- Response time under load
- Throughput capacity
- Concurrent connection handling
- Stability under sustained load
"""

import logging
import json
import time
import threading
import statistics
import requests
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("LoadTester")

# Common API endpoints to test
DEFAULT_TEST_ENDPOINTS = [
    "/",
    "/api/health",
    "/api/status"
]

def get_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile from a list of values (Python 3.7 compatible)."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    
    idx = (n - 1) * (percentile / 100.0)
    lower = int(idx)
    upper = lower + 1
    weight = idx - lower
    
    if upper >= n:
        return sorted_data[lower]
    return sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight

class LoadTestWorker:
    """Worker class to make repeated requests to an endpoint."""
    
    def __init__(self, base_url: str, endpoints: List[str], headers: Optional[Dict[str, str]] = None):
        """Initialize the worker with configuration."""
        self.base_url = base_url.rstrip('/')
        self.endpoints = endpoints
        self.headers = headers or {}
        self.results = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "errors": []
        }
        
    def run(self, duration: int, request_interval: float = 0.1):
        """Run the load test for the specified duration."""
        end_time = time.time() + duration
        
        while time.time() < end_time:
            for endpoint in self.endpoints:
                url = f"{self.base_url}{endpoint}"
                try:
                    start_time = time.time()
                    response = requests.get(url, headers=self.headers, timeout=5)
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    self.results["requests"] += 1
                    self.results["response_times"].append(response_time)
                    
                    if response.status_code < 400:
                        self.results["successful"] += 1
                    else:
                        self.results["failed"] += 1
                        self.results["errors"].append({
                            "url": url,
                            "status_code": response.status_code,
                            "response": response.text[:200]  # Truncate long responses
                        })
                        
                except requests.RequestException as e:
                    self.results["requests"] += 1
                    self.results["failed"] += 1
                    self.results["errors"].append({
                        "url": url,
                        "error": str(e)
                    })
                
                # Sleep for the request interval
                if time.time() < end_time:
                    time.sleep(request_interval)
                else:
                    break
                    
        # Calculate statistics
        if self.results["response_times"]:
            self.results["min_response_time"] = min(self.results["response_times"])
            self.results["max_response_time"] = max(self.results["response_times"])
            self.results["avg_response_time"] = statistics.mean(self.results["response_times"])
            self.results["std_dev"] = statistics.stdev(self.results["response_times"]) if len(self.results["response_times"]) > 1 else 0
            self.results["median_response_time"] = statistics.median(self.results["response_times"])
            self.results["p95_response_time"] = get_percentile(self.results["response_times"], 95)
            self.results["p99_response_time"] = get_percentile(self.results["response_times"], 99)
        
        return self.results

def discover_endpoints(base_url: str) -> List[str]:
    """Attempt to discover API endpoints by checking common paths."""
    discovered = []
    common_paths = [
        "/api",
        "/api/v1",
        "/api/health",
        "/api/status",
        "/health",
        "/status",
        "/api/users",
        "/api/customers",
        "/api/products"
    ]
    
    for path in common_paths:
        try:
            response = requests.head(f"{base_url.rstrip('/')}{path}", timeout=2)
            if response.status_code < 400:
                discovered.append(path)
        except:
            pass
    
    # Always include root path if we haven't discovered anything
    if not discovered:
        discovered.append("/")
        
    return discovered

def run_load_test(
    base_url: str,
    num_users: int = 10,
    duration: int = 30,
    max_response_time: int = 500,
    endpoints: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run a load test on the application.
    
    Args:
        base_url: Base URL of the application
        num_users: Number of concurrent users to simulate
        duration: Duration of the test in seconds
        max_response_time: Maximum acceptable response time in ms
        endpoints: List of endpoints to test (if None, will attempt to discover)
        
    Returns:
        Dict with load test results
    """
    logger.info(f"Starting load test against {base_url} with {num_users} users for {duration} seconds")
    
    results = {
        "passed": False,
        "total": 0,
        "passed_tests": 0,
        "tests": []
    }
    
    try:
        # Check if base URL is accessible
        try:
            requests.get(base_url, timeout=5)
        except requests.RequestException as e:
            test_result = {
                "name": "Base URL accessibility check",
                "status": "FAIL",
                "message": f"Base URL is not accessible: {str(e)}"
            }
            results["tests"].append(test_result)
            results["total"] += 1
            return results
        
        # Discover or use provided endpoints
        test_endpoints = endpoints if endpoints else discover_endpoints(base_url)
        logger.info(f"Testing endpoints: {test_endpoints}")
        
        # Initialize workers in a thread pool
        workers = []
        for _ in range(num_users):
            workers.append(LoadTestWorker(base_url, test_endpoints))
        
        # Start and collect results
        all_results = []
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            future_to_worker = {
                executor.submit(worker.run, duration): worker for worker in workers
            }
            for future in as_completed(future_to_worker):
                try:
                    worker_result = future.result()
                    all_results.append(worker_result)
                except Exception as e:
                    logger.error(f"Worker error: {str(e)}")
        
        # Combine results
        combined = {
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "errors": []
        }
        
        for worker_result in all_results:
            combined["requests"] += worker_result["requests"]
            combined["successful"] += worker_result["successful"]
            combined["failed"] += worker_result["failed"]
            combined["response_times"].extend(worker_result["response_times"])
            combined["errors"].extend(worker_result["errors"])
        
        # Calculate final statistics
        if combined["response_times"]:
            combined["min_response_time"] = min(combined["response_times"])
            combined["max_response_time"] = max(combined["response_times"])
            combined["avg_response_time"] = statistics.mean(combined["response_times"])
            combined["std_dev"] = statistics.stdev(combined["response_times"]) if len(combined["response_times"]) > 1 else 0
            combined["median_response_time"] = statistics.median(combined["response_times"])
            combined["p95_response_time"] = get_percentile(combined["response_times"], 95)
            combined["p99_response_time"] = get_percentile(combined["response_times"], 99)
        
        # Calculate throughput (requests per second)
        combined["throughput"] = combined["requests"] / duration
        
        # Calculate success rate
        if combined["requests"] > 0:
            combined["success_rate"] = (combined["successful"] / combined["requests"]) * 100
        else:
            combined["success_rate"] = 0
        
        # Add test results based on metrics
        
        # 1. Test for success rate
        success_rate = combined["success_rate"]
        test_result = {
            "name": "Request success rate",
            "status": "PASS" if success_rate >= 95 else "FAIL",
            "message": f"Success rate: {success_rate:.1f}%"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
            
        # 2. Test for average response time
        avg_response_time = combined.get("avg_response_time", 0)
        test_result = {
            "name": "Average response time",
            "status": "PASS" if avg_response_time <= max_response_time else "FAIL",
            "message": f"Average response time: {avg_response_time:.1f} ms (Max allowed: {max_response_time} ms)"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
            
        # 3. Test for p95 response time
        p95_response_time = combined.get("p95_response_time", 0)
        test_result = {
            "name": "95th percentile response time",
            "status": "PASS" if p95_response_time <= max_response_time * 1.5 else "FAIL",
            "message": f"95th percentile response time: {p95_response_time:.1f} ms (Max allowed: {max_response_time * 1.5} ms)"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
            
        # 4. Test for throughput
        min_throughput = num_users / 2  # Expect at least half the number of users as throughput
        test_result = {
            "name": "Throughput (requests per second)",
            "status": "PASS" if combined["throughput"] >= min_throughput else "FAIL",
            "message": f"Throughput: {combined['throughput']:.1f} requests/sec (Min expected: {min_throughput})"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
        
        # Overall result
        results["passed"] = results["passed_tests"] == results["total"]
        results["metrics"] = combined
        
    except Exception as e:
        logger.error(f"Error during load test: {str(e)}")
        results["passed"] = False
        results["error"] = str(e)
        
    return results

if __name__ == "__main__":
    # Simple standalone test
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "http://localhost:8000"
        
    logging.basicConfig(level=logging.INFO)
    result = run_load_test(url, num_users=5, duration=10)
    
    print(f"Load Test Results for {url}:")
    print(f"Passed: {result.get('passed', False)}")
    print(f"Tests: {result.get('passed_tests', 0)}/{result.get('total', 0)} passed")
    
    for test in result.get("tests", []):
        if test["status"] == "PASS":
            status_symbol = "✓"
        else:
            status_symbol = "✗"
        print(f"{status_symbol} {test['name']}: {test['message']}")
        
    if "metrics" in result:
        print("\nMetrics:")
        print(f"Total Requests: {result['metrics']['requests']}")
        print(f"Successful: {result['metrics']['successful']} ({result['metrics']['success_rate']:.1f}%)")
        print(f"Failed: {result['metrics']['failed']}")
        print(f"Avg Response Time: {result['metrics'].get('avg_response_time', 0):.1f} ms")
        print(f"Median Response Time: {result['metrics'].get('median_response_time', 0):.1f} ms")
        print(f"95th Percentile: {result['metrics'].get('p95_response_time', 0):.1f} ms")
        print(f"Throughput: {result['metrics'].get('throughput', 0):.1f} requests/sec")
