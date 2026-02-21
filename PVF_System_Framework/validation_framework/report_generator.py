#!/usr/bin/env python
"""
Report Generator
==============

This module generates HTML and JSON reports for validation results.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

def generate_html_report(results: Dict[str, Any], output_path: str) -> None:
    """
    Generate an HTML report from validation results.
    
    Args:
        results: Validation results dictionary
        output_path: Path to save the HTML report
    """
    summary = results.get("summary", {})
    passed = summary.get("production_ready", False)
    
    # Build the HTML content
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "    <title>Production Readiness Validation Report</title>",
        "    <meta charset='utf-8'>",
        "    <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }",
        "        .container { max-width: 1200px; margin: 0 auto; }",
        "        h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }",
        "        h2 { color: #3498db; margin-top: 30px; }",
        "        h3 { color: #2c3e50; }",
        "        .summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
        "        .section { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }",
        "        .pass { color: #27ae60; }",
        "        .fail { color: #e74c3c; }",
        "        .warning { color: #f39c12; }",
        "        table { width: 100%; border-collapse: collapse; margin-top: 10px; }",
        "        table, th, td { border: 1px solid #ddd; }",
        "        th, td { padding: 10px; text-align: left; }",
        "        th { background-color: #f2f2f2; }",
        "        tr:nth-child(even) { background-color: #f9f9f9; }",
        "        .test-result { display: flex; align-items: center; }",
        "        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; margin-right: 10px; color: white; }",
        "        .badge-pass { background-color: #27ae60; }",
        "        .badge-fail { background-color: #e74c3c; }",
        "        .badge-warning { background-color: #f39c12; }",
        "        .result-icon { font-size: 18px; margin-right: 5px; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class='container'>",
        "        <h1>Production Readiness Validation Report</h1>",
        f"        <div class='summary'>",
        f"            <h2>Summary</h2>",
        f"            <p><strong>Status:</strong> <span class='{'pass' if passed else 'fail'}'>{('✅ PRODUCTION READY' if passed else '❌ NOT PRODUCTION READY')}</span></p>",
        f"            <p><strong>Date:</strong> {summary.get('start_time', datetime.now().isoformat())}</p>",
        f"            <p><strong>Duration:</strong> {summary.get('duration_seconds', 0):.2f} seconds</p>",
        f"            <p><strong>Tests:</strong> {summary.get('tests_passed', 0)}/{summary.get('total_tests', 0)} passed ({summary.get('pass_percentage', 0):.1f}%)</p>",
        f"            <p><strong>Failed:</strong> {summary.get('tests_failed', 0)}, <strong>Warnings:</strong> {summary.get('tests_warned', 0)}</p>",
        "        </div>"
    ]
    
    # Add environment config section
    if "env_config" in results:
        env_config = results["env_config"]
        html.extend([
            "        <div class='section'>",
            "            <h2>Environment Configuration</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if env_config.get('passed', False) else 'fail'}'>{('✅ PASSED' if env_config.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {env_config.get('passed', 0)}/{env_config.get('total', 0)} tests</p>",
            "            <table>",
            "                <tr><th>Test</th><th>Status</th><th>Message</th><th>Remediation Advice</th></tr>"
        ])
        
        for test in env_config.get("tests", []):
            status_class = "pass" if test.get("status") == "PASS" else "fail" if test.get("status") == "FAIL" else "warning"
            status_icon = "✅" if test.get("status") == "PASS" else "❌" if test.get("status") == "FAIL" else "⚠️"
            remediation = test.get("remediation", "-")
            html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon} {test.get('status', '')}</td><td>{test.get('message', '')}</td><td><i>{remediation}</i></td></tr>")
            
        html.append("            </table>")
        html.append("        </div>")
    
    # Add security section
    if "security" in results:
        security = results["security"]
        html.extend([
            "        <div class='section'>",
            "            <h2>Security Tests</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if security.get('passed', False) else 'fail'}'>{('✅ PASSED' if security.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {security.get('passed', 0)}/{security.get('total', 0)} tests</p>",
            "            <table>",
            "                <tr><th>Test</th><th>Status</th><th>Message</th><th>Remediation Advice</th></tr>"
        ])
        
        for test in security.get("tests", []):
            status_class = "pass" if test.get("status") == "PASS" else "fail" if test.get("status") == "FAIL" else "warning"
            status_icon = "✅" if test.get("status") == "PASS" else "❌" if test.get("status") == "FAIL" else "⚠️"
            remediation = test.get("remediation", "-")
            html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon} {test.get('status', '')}</td><td>{test.get('message', '')}</td><td><i>{remediation}</i></td></tr>")
            
        html.append("            </table>")
        html.append("        </div>")
    
    # Add performance section
    if "performance" in results:
        performance = results["performance"]
        html.extend([
            "        <div class='section'>",
            "            <h2>Performance Tests</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if performance.get('passed', False) else 'fail'}'>{('✅ PASSED' if performance.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {performance.get('passed_tests', 0)}/{performance.get('total', 0)} tests</p>",
        ])
        
        # Load test results
        if "load_test" in performance:
            html.append("            <h3>Load Test Results</h3>")
            html.append("            <table>")
            html.append("                <tr><th>Test</th><th>Status</th><th>Message</th></tr>")
            
            for test in performance["load_test"].get("tests", []):
                status_class = "pass" if test.get("status") == "PASS" else "fail" if test.get("status") == "FAIL" else "warning"
                status_icon = "✅" if test.get("status") == "PASS" else "❌" if test.get("status") == "FAIL" else "⚠️"
                html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon} {test.get('status', '')}</td><td>{test.get('message', '')}</td></tr>")
                
            html.append("            </table>")
            
            # Add metrics if available
            if "metrics" in performance["load_test"]:
                metrics = performance["load_test"]["metrics"]
                html.append("            <h4>Performance Metrics</h4>")
                html.append("            <table>")
                html.append("                <tr><th>Metric</th><th>Value</th></tr>")
                
                if "requests" in metrics:
                    html.append(f"                <tr><td>Total Requests</td><td>{metrics['requests']}</td></tr>")
                if "successful" in metrics:
                    html.append(f"                <tr><td>Successful Requests</td><td>{metrics['successful']}</td></tr>")
                if "failed" in metrics:
                    html.append(f"                <tr><td>Failed Requests</td><td>{metrics['failed']}</td></tr>")
                if "success_rate" in metrics:
                    html.append(f"                <tr><td>Success Rate</td><td>{metrics['success_rate']:.1f}%</td></tr>")
                if "avg_response_time" in metrics:
                    html.append(f"                <tr><td>Average Response Time</td><td>{metrics['avg_response_time']:.1f} ms</td></tr>")
                if "p95_response_time" in metrics:
                    html.append(f"                <tr><td>95th Percentile Response Time</td><td>{metrics['p95_response_time']:.1f} ms</td></tr>")
                if "throughput" in metrics:
                    html.append(f"                <tr><td>Throughput</td><td>{metrics['throughput']:.1f} req/sec</td></tr>")
                
                html.append("            </table>")
        
        html.append("        </div>")
    
    # Add API section
    if "api" in results:
        api = results["api"]
        html.extend([
            "        <div class='section'>",
            "            <h2>API Tests</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if api.get('passed', False) else 'fail'}'>{('✅ PASSED' if api.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {api.get('passed_tests', 0)}/{api.get('total', 0)} endpoints</p>",
            "            <h3>Endpoint Results</h3>"
        ])
        
        if "endpoints" in api and "endpoints" in api["endpoints"]:
            for endpoint in api["endpoints"]["endpoints"]:
                endpoint_path = endpoint.get("endpoint", "Unknown")
                method = endpoint.get("method", "GET")
                status = "✅" if endpoint.get("passed", False) else "❌"
                
                html.extend([
                    f"            <h4>{status} [{method}] {endpoint_path}</h4>",
                    "            <table>",
                    "                <tr><th>Test</th><th>Status</th><th>Message</th><th>Remediation Advice</th></tr>"
                ])
                
                for test in endpoint.get("tests", []):
                    status_class = "pass" if test.get("passed", True) else "fail"
                    status_icon = "✅" if test.get("passed", True) else "❌"
                    remediation = test.get("remediation", "-")
                    html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon}</td><td>{test.get('message', '')}</td><td><i>{remediation}</i></td></tr>")
                    
                html.append("            </table>")
        
        html.append("        </div>")
    
    # Add database section
    if "database" in results:
        db = results["database"]
        html.extend([
            "        <div class='section'>",
            "            <h2>Database Tests</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if db.get('passed', False) else 'fail'}'>{('✅ PASSED' if db.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {db.get('passed', 0)}/{db.get('total', 0)} tests</p>",
            "            <table>",
            "                <tr><th>Test</th><th>Status</th><th>Message</th><th>Remediation Advice</th></tr>"
        ])
        
        for test in db.get("tests", []):
            status_class = "pass" if test.get("status") == "PASS" else "fail" if test.get("status") == "FAIL" else "warning"
            status_icon = "✅" if test.get("status") == "PASS" else "❌" if test.get("status") == "FAIL" else "⚠️"
            remediation = test.get("remediation", "-")
            html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon} {test.get('status', '')}</td><td>{test.get('message', '')}</td><td><i>{remediation}</i></td></tr>")
            
        html.append("            </table>")
        html.append("        </div>")
    
    # Add deployment section
    if "deployment" in results:
        deployment = results["deployment"]
        html.extend([
            "        <div class='section'>",
            "            <h2>Deployment Readiness</h2>",
            f"            <p><strong>Status:</strong> <span class='{'pass' if deployment.get('passed', False) else 'fail'}'>{('✅ PASSED' if deployment.get('passed', False) else '❌ FAILED')}</span></p>",
            f"            <p>Passed {deployment.get('passed_tests', 0)}/{deployment.get('total', 0)} tests</p>",
        ])
        
        # Add sections
        for section in deployment.get("sections", []):
            section_name = section.get("name", "Unknown")
            section_status = "✅" if section.get("passed", False) else "❌"
            
            html.extend([
                f"            <h3>{section_status} {section_name}</h3>",
                "            <table>",
                "                <tr><th>Test</th><th>Status</th><th>Message</th><th>Remediation Advice</th></tr>"
            ])
            
            for test in section.get("tests", []):
                status_class = "pass" if test.get("passed", True) else "fail"
                status_icon = "✅" if test.get("passed", True) else "❌"
                remediation = test.get("remediation", "-")
                html.append(f"                <tr><td>{test.get('name', '')}</td><td class='{status_class}'>{status_icon}</td><td>{test.get('message', '')}</td><td><i>{remediation}</i></td></tr>")
                
            html.append("            </table>")
        
        html.append("        </div>")
    
    # Close HTML
    html.extend([
        "    </div>",
        "</body>",
        "</html>"
    ])
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html))

def generate_json_report(results: Dict[str, Any], output_path: str) -> None:
    """
    Generate a JSON report from validation results.
    
    Args:
        results: Validation results dictionary
        output_path: Path to save the JSON report
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate reports from validation results")
    parser.add_argument('--input', required=True, help='Path to the validation results JSON file')
    parser.add_argument('--output', required=True, help='Path to save the HTML report')
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r') as f:
            results = json.load(f)
            
        generate_html_report(results, args.output)
        print(f"Report generated successfully at {args.output}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
