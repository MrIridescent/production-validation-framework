#!/usr/bin/env python
"""
Security Scanner Module
======================

This module performs security scans on the application, including:
- SSL/TLS configuration
- Security headers
- Authentication mechanisms
- CORS configuration
- Rate limiting
- Input validation vulnerabilities
"""

import logging
import json
import ssl
import socket
import re
import time
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger("SecurityScanner")

# Security headers that should be present
RECOMMENDED_SECURITY_HEADERS = {
    'Strict-Transport-Security': True,  # HSTS header
    'Content-Security-Policy': True,  # CSP header
    'X-Content-Type-Options': True,  # Prevents MIME type sniffing
    'X-Frame-Options': True,  # Clickjacking protection
    'X-XSS-Protection': True,  # XSS protection
    'Referrer-Policy': True,  # Referrer policy
    'Feature-Policy': False,  # Optional feature policy
    'Permissions-Policy': False  # Modern replacement for Feature-Policy
}

# Test API endpoint patterns
AUTH_TEST_ENDPOINTS = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/reset-password",
    "/api/users",
    "/api/customers"
]

def check_ssl_tls(url: str) -> Dict[str, Any]:
    """Check SSL/TLS configuration for security issues."""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    result = {
        "secure": False,
        "protocol": None,
        "cipher": None,
        "cert_expiration": None,
        "issues": []
    }
    
    # Skip if not HTTPS
    if parsed_url.scheme != 'https':
        result["issues"].append("Not using HTTPS")
        return result
    
    try:
        # Create SSL context with high security
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Disable old TLS
        
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate and connection info
                cert = ssock.getpeercert()
                result["protocol"] = ssock.version()
                result["cipher"] = ssock.cipher()
                
                # Check certificate expiration
                import datetime
                exp_date = datetime.datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                remaining_days = (exp_date - datetime.datetime.now()).days
                result["cert_expiration"] = {
                    "date": exp_date.isoformat(),
                    "days_remaining": remaining_days
                }
                
                if remaining_days < 30:
                    result["issues"].append(f"Certificate expires in {remaining_days} days")
                
                # Check protocol version
                if result["protocol"] in ['TLSv1', 'TLSv1.1']:
                    result["issues"].append(f"Outdated TLS version: {result['protocol']}")
        
        # If we made it here, the connection is secure
        result["secure"] = len(result["issues"]) == 0
        
    except ssl.SSLError as e:
        result["issues"].append(f"SSL Error: {str(e)}")
    except socket.error as e:
        result["issues"].append(f"Connection Error: {str(e)}")
    except Exception as e:
        result["issues"].append(f"Error: {str(e)}")
        
    return result

def check_security_headers(url: str) -> Dict[str, Any]:
    """Check for recommended security headers."""
    result = {
        "headers_present": {},
        "missing_headers": [],
        "score": 0,
        "max_score": 0
    }
    
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        headers = response.headers
        
        for header, required in RECOMMENDED_SECURITY_HEADERS.items():
            result["max_score"] += 1 if required else 0.5  # Required headers worth more
            
            if header.lower() in [h.lower() for h in headers.keys()]:
                result["headers_present"][header] = headers.get(header)
                result["score"] += 1 if required else 0.5
            else:
                if required:
                    result["missing_headers"].append(header)
        
        # Normalize score to percentage
        if result["max_score"] > 0:
            result["score_percentage"] = (result["score"] / result["max_score"]) * 100
        else:
            result["score_percentage"] = 0
        
    except requests.RequestException as e:
        result["error"] = str(e)
        
    return result

def check_cors_configuration(url: str) -> Dict[str, Any]:
    """Check CORS configuration for security issues."""
    result = {
        "secure": False,
        "issues": []
    }
    
    try:
        # Make an OPTIONS request to check CORS headers
        headers = {
            'Origin': 'https://attacker-example.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(url, headers=headers, timeout=10)
        
        # Check for overly permissive CORS headers
        access_control_allow_origin = response.headers.get('Access-Control-Allow-Origin')
        if access_control_allow_origin == '*':
            result["issues"].append("CORS allows any origin (*)")
        
        access_control_allow_headers = response.headers.get('Access-Control-Allow-Headers')
        if access_control_allow_headers and access_control_allow_headers.lower() == '*':
            result["issues"].append("CORS allows any headers (*)")
        
        # Result is secure if no issues found
        result["secure"] = len(result["issues"]) == 0
        result["headers"] = {
            'Access-Control-Allow-Origin': access_control_allow_origin,
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': access_control_allow_headers,
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
    except requests.RequestException as e:
        result["error"] = str(e)
        
    return result

def check_auth_endpoints(base_url: str) -> Dict[str, Any]:
    """Test authentication endpoints for common security issues."""
    result = {
        "secure": False,
        "endpoints_tested": 0,
        "issues": []
    }
    
    try:
        endpoints_found = 0
        
        for endpoint in AUTH_TEST_ENDPOINTS:
            url = base_url.rstrip('/') + endpoint
            
            # Check if endpoint exists
            head_response = requests.head(url, allow_redirects=False, timeout=5)
            if head_response.status_code not in [404, 405]:  # 405 is Method Not Allowed, which means endpoint exists
                endpoints_found += 1
                
                # Test rate limiting
                start_time = time.time()
                request_count = 0
                for _ in range(10):  # Make 10 requests in quick succession
                    requests.get(url, timeout=5)
                    request_count += 1
                end_time = time.time()
                
                # If all 10 requests succeeded without delay, there might be no rate limiting
                if request_count == 10 and (end_time - start_time) < 2.0:
                    result["issues"].append(f"Endpoint {endpoint} may lack rate limiting")
                
                # Test for basic auth bypass by sending JSON with empty fields
                try:
                    if "/login" in endpoint or "/auth" in endpoint:
                        auth_response = requests.post(url, json={
                            "username": "",
                            "email": "",
                            "password": ""
                        }, timeout=5)
                        
                        # Check if it returns 200 OK with empty credentials
                        if auth_response.status_code == 200:
                            result["issues"].append(f"Endpoint {endpoint} may accept empty credentials")
                except:
                    pass
        
        result["endpoints_tested"] = endpoints_found
        result["secure"] = len(result["issues"]) == 0
        
    except requests.RequestException as e:
        result["error"] = str(e)
        
    return result

def check_cookie_security(url: str) -> Dict[str, Any]:
    """Check if cookies have secure flags (HttpOnly, Secure, SameSite)."""
    result = {
        "secure": True,
        "issues": [],
        "cookies": []
    }
    try:
        response = requests.get(url, timeout=10, verify=False)
        for cookie in response.cookies:
            c_info = {
                "name": cookie.name,
                "httponly": cookie.has_nonstandard_attr('HttpOnly') or 'HttpOnly' in str(cookie),
                "secure": cookie.secure,
                "samesite": cookie.get_nonstandard_attr('SameSite')
            }
            if not c_info["httponly"]:
                result["issues"].append(f"Cookie '{cookie.name}' missing HttpOnly flag")
            if not c_info["secure"] and url.startswith("https"):
                result["issues"].append(f"Cookie '{cookie.name}' missing Secure flag")
            result["cookies"].append(c_info)
        
        result["secure"] = len(result["issues"]) == 0
    except Exception as e:
        result["error"] = str(e)
    return result

def check_sensitive_info_exposure(url: str) -> Dict[str, Any]:
    """Check for information disclosure in headers and response body."""
    result = {
        "secure": True,
        "issues": []
    }
    sensitive_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version', 'X-Runtime']
    # Patterns for common secrets
    secret_patterns = {
        "AWS Key": r"AKIA[0-9A-Z]{16}",
        "Generic Secret": r"(?i)(password|secret|key|token|auth)\s*[:=]\s*['\"][^'\"]+['\"]",
        "Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
    }

    try:
        response = requests.get(url, timeout=10, verify=False)
        # Check headers
        for h in sensitive_headers:
            if h in response.headers:
                val = response.headers[h]
                # If it's too specific (contains version numbers)
                if re.search(r'\d', val):
                    result["issues"].append(f"Verbose header exposure: {h}: {val}")
        
        # Check body
        content = response.text
        for name, pattern in secret_patterns.items():
            if re.search(pattern, content):
                result["issues"].append(f"Potential {name} exposed in response body")
                
        result["secure"] = len(result["issues"]) == 0
    except Exception as e:
        result["error"] = str(e)
    return result

def run_security_scan(
    base_url: str,
    scan_severity: str = "medium",
    check_ssl: bool = True,
    check_headers: bool = True,
    check_auth: bool = True
) -> Dict[str, Any]:
    """
    Run a comprehensive security scan on the application.
    
    Args:
        base_url: Base URL of the application
        scan_severity: Severity level of the scan (low, medium, high)
        check_ssl: Whether to check SSL/TLS configuration
        check_headers: Whether to check security headers
        check_auth: Whether to check authentication endpoints
        
    Returns:
        Dict with scan results
    """
    logger.info(f"Running security scan against {base_url} with severity {scan_severity}")
    
    results = {
        "passed": False,
        "total": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "tests": []
    }
    
    try:
        # Check if URL is reachable
        try:
            requests.head(base_url, timeout=10)
        except requests.RequestException as e:
            test_result = {
                "name": "Base URL accessibility check",
                "status": "FAIL",
                "message": f"Base URL is not accessible: {str(e)}"
            }
            results["tests"].append(test_result)
            results["total"] += 1
            results["failed_tests"] += 1
            results["passed"] = False
            return results
        
        # Base URL is accessible
        test_result = {
            "name": "Base URL accessibility check",
            "status": "PASS",
            "message": "Base URL is accessible"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        results["passed_tests"] += 1
        
        # Check SSL/TLS configuration
        if check_ssl:
            ssl_results = check_ssl_tls(base_url)
            
            if base_url.startswith("https://"):
                test_result = {
                    "name": "HTTPS check",
                    "status": "PASS",
                    "message": "Application is using HTTPS"
                }
            else:
                test_result = {
                    "name": "HTTPS check",
                    "status": "FAIL",
                    "message": "Application is not using HTTPS"
                }
                
            results["tests"].append(test_result)
            results["total"] += 1
            if test_result["status"] == "PASS":
                results["passed_tests"] += 1
            else:
                results["failed_tests"] += 1
            
            if base_url.startswith("https://"):
                # Check if SSL/TLS is properly configured
                test_result = {
                    "name": "SSL/TLS configuration",
                    "status": "PASS" if ssl_results.get("secure") else "FAIL",
                    "message": "SSL/TLS is properly configured" if ssl_results.get("secure") else 
                              f"SSL/TLS has issues: {', '.join(ssl_results.get('issues', []))}"
                }
                results["tests"].append(test_result)
                results["total"] += 1
                if test_result["status"] == "PASS":
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
                
                # Check certificate expiration
                if ssl_results.get("cert_expiration"):
                    days_remaining = ssl_results["cert_expiration"]["days_remaining"]
                    test_result = {
                        "name": "SSL certificate expiration",
                        "status": "PASS" if days_remaining >= 30 else "WARNING" if days_remaining >= 7 else "FAIL",
                        "message": f"Certificate expires in {days_remaining} days"
                    }
                    results["tests"].append(test_result)
                    results["total"] += 1
                    if test_result["status"] == "PASS":
                        results["passed_tests"] += 1
                    elif test_result["status"] == "FAIL":
                        results["failed_tests"] += 1
        
        # Check security headers
        if check_headers:
            header_results = check_security_headers(base_url)
            
            # Calculate a grade based on the score percentage
            score_percentage = header_results.get("score_percentage", 0)
            if score_percentage >= 90:
                grade = "A"
                status = "PASS"
            elif score_percentage >= 70:
                grade = "B"
                status = "WARNING" if scan_severity == "high" else "PASS"
            elif score_percentage >= 50:
                grade = "C"
                status = "WARNING"
            else:
                grade = "F"
                status = "FAIL"
                
            test_result = {
                "name": "Security headers check",
                "status": status,
                "message": f"Security headers score: {score_percentage:.1f}% (Grade {grade})"
            }
            results["tests"].append(test_result)
            results["total"] += 1
            if test_result["status"] == "PASS":
                results["passed_tests"] += 1
            elif test_result["status"] == "FAIL":
                results["failed_tests"] += 1
            
            # Check for critical headers separately
            critical_headers = ["Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options"]
            for header in critical_headers:
                if header not in header_results.get("headers_present", {}):
                    test_result = {
                        "name": f"Critical security header: {header}",
                        "status": "FAIL" if scan_severity in ["medium", "high"] else "WARNING",
                        "message": f"Critical security header '{header}' is missing"
                    }
                    results["tests"].append(test_result)
                    results["total"] += 1
                    if test_result["status"] == "FAIL":
                        results["failed_tests"] += 1
            
            # Check CORS configuration
            cors_results = check_cors_configuration(base_url)
            test_result = {
                "name": "CORS configuration check",
                "status": "PASS" if cors_results.get("secure") else "WARNING",
                "message": "CORS is properly configured" if cors_results.get("secure") else 
                          f"CORS configuration issues: {', '.join(cors_results.get('issues', []))}"
            }
            results["tests"].append(test_result)
            results["total"] += 1
            if test_result["status"] == "PASS":
                results["passed_tests"] += 1
        
        # Check authentication endpoints
        if check_auth:
            auth_results = check_auth_endpoints(base_url)
            
            if auth_results.get("endpoints_tested", 0) > 0:
                test_result = {
                    "name": "Authentication endpoints check",
                    "status": "PASS" if auth_results.get("secure") else "FAIL",
                    "message": f"Tested {auth_results.get('endpoints_tested')} auth endpoints, all secure" 
                              if auth_results.get("secure") else 
                              f"Found {len(auth_results.get('issues', []))} issues in auth endpoints"
                }
                results["tests"].append(test_result)
                results["total"] += 1
                if test_result["status"] == "PASS":
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
                
                # Add specific issues
                for issue in auth_results.get("issues", []):
                    test_result = {
                        "name": "Authentication security issue",
                        "status": "FAIL",
                        "message": issue
                    }
                    results["tests"].append(test_result)
                    results["total"] += 1
                    results["failed_tests"] += 1

        # Cookie security
        cookie_results = check_cookie_security(base_url)
        test_result = {
            "name": "Cookie security flags",
            "status": "PASS" if cookie_results.get("secure") else "WARNING",
            "message": "Cookies are securely configured" if cookie_results.get("secure") else 
                      f"Cookie issues: {', '.join(cookie_results.get('issues', []))}"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1

        # Sensitive info exposure
        exposure_results = check_sensitive_info_exposure(base_url)
        test_result = {
            "name": "Information disclosure scan",
            "status": "PASS" if exposure_results.get("secure") else "FAIL",
            "message": "No sensitive info exposure detected" if exposure_results.get("secure") else 
                      f"Exposure issues: {', '.join(exposure_results.get('issues', []))}"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
        else:
            results["failed_tests"] += 1
        
        # Overall result
        results["passed"] = results["failed_tests"] == 0
        
    except Exception as e:
        logger.error(f"Error during security scan: {str(e)}")
        results["passed"] = False
        results["error"] = str(e)
        
    return results

if __name__ == "__main__":
    # Simple standalone test
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://example.com"
        
    logging.basicConfig(level=logging.INFO)
    result = run_security_scan(url)
    
    print(f"Security Scan Results for {url}:")
    print(f"Passed: {result['passed']}")
    print(f"Tests: {result['passed_tests']}/{result['total']} passed")
    
    for test in result["tests"]:
        if test["status"] == "PASS":
            status_symbol = "✓"
        elif test["status"] == "WARNING":
            status_symbol = "⚠"
        else:
            status_symbol = "✗"
        print(f"{status_symbol} {test['name']}: {test['message']}")
