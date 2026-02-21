#!/usr/bin/env python
"""
Documentation Generator
=====================

This module generates documentation for the validation framework including:
- Architecture overview
- Usage instructions
- Validator descriptions
- Example configurations
"""

import os
import re
import inspect
import importlib.util
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("DocsGenerator")

def _extract_module_docstring(module_path: str) -> str:
    """
    Extract the docstring from a Python module.
    
    Args:
        module_path: Path to the module
        
    Returns:
        Docstring content or empty string
    """
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract docstring between triple quotes
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        
        return ""
    except Exception as e:
        logger.error(f"Error extracting docstring from {module_path}: {str(e)}")
        return ""

def _load_module(module_path: str) -> Optional[Any]:
    """
    Load a Python module from file path.
    
    Args:
        module_path: Path to the module
        
    Returns:
        Loaded module or None
    """
    try:
        module_name = os.path.basename(module_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        
        if spec is None or spec.loader is None:
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error loading module {module_path}: {str(e)}")
        return None

def _find_validator_files(framework_root: str) -> Dict[str, List[str]]:
    """
    Find all validator files in the framework.
    
    Args:
        framework_root: Root directory of the validation framework
        
    Returns:
        Dict mapping validator type to list of files
    """
    validators = {
        "config": [],
        "api": [],
        "security": [],
        "performance": [],
        "deployment": []
    }
    
    # Directory mappings
    dir_mappings = {
        "config_validators": "config",
        "api_tests": "api",
        "security_tests": "security",
        "performance_tests": "performance",
        "deployment_checks": "deployment"
    }
    
    # Find Python files
    for subdir, validator_type in dir_mappings.items():
        dir_path = os.path.join(framework_root, subdir)
        
        if not os.path.isdir(dir_path):
            continue
            
        for filename in os.listdir(dir_path):
            if filename.endswith('.py'):
                validators[validator_type].append(os.path.join(dir_path, filename))
                
    # Add main validator
    main_validator = os.path.join(framework_root, 'validate_production_readiness.py')
    if os.path.isfile(main_validator):
        validators["main"] = [main_validator]
        
    return validators

def generate_readme(framework_root: str) -> str:
    """
    Generate README.md for the validation framework.
    
    Args:
        framework_root: Root directory of the validation framework
        
    Returns:
        README content
    """
    validator_files = _find_validator_files(framework_root)
    
    # Extract main validator docstring
    main_description = ""
    if "main" in validator_files and validator_files["main"]:
        main_path = validator_files["main"][0]
        main_description = _extract_module_docstring(main_path)
    
    # Generate README
    sections = []
    
    # Header
    sections.append("# Production Readiness Validation Framework\n")
    
    # Description
    if main_description:
        sections.append(main_description + "\n")
    else:
        sections.append(
            "A comprehensive framework for validating production readiness of applications.\n"
            "This framework checks configuration, API endpoints, security, performance, and deployment readiness.\n"
        )
    
    # Table of Contents
    sections.append("## Table of Contents\n")
    sections.append("1. [Overview](#overview)")
    sections.append("2. [Installation](#installation)")
    sections.append("3. [Usage](#usage)")
    sections.append("4. [Validators](#validators)")
    sections.append("   - [Configuration Validators](#configuration-validators)")
    sections.append("   - [API Validators](#api-validators)")
    sections.append("   - [Security Tests](#security-tests)")
    sections.append("   - [Performance Tests](#performance-tests)")
    sections.append("   - [Deployment Checks](#deployment-checks)")
    sections.append("5. [Example Configurations](#example-configurations)")
    sections.append("6. [Extending the Framework](#extending-the-framework)")
    sections.append("")
    
    # Overview
    sections.append("## Overview\n")
    sections.append(
        "This validation framework helps ensure your application is ready for production deployment "
        "by running a series of tests and checks across various aspects of your system. "
        "It can validate environment configurations, database connectivity, API endpoints, "
        "security measures, performance under load, and deployment readiness.\n"
    )
    
    # Installation
    sections.append("## Installation\n")
    sections.append("To use this framework in your project:\n")
    sections.append("1. Clone or copy the `validation_framework` directory into your project")
    sections.append("2. Install required dependencies:")
    sections.append("```bash")
    sections.append("pip install requests pytest psutil dnspython python-dotenv")
    sections.append("```\n")
    
    # Usage
    sections.append("## Usage\n")
    sections.append("Run the main validation script from your project root:\n")
    sections.append("```bash")
    sections.append("python validation_framework/validate_production_readiness.py")
    sections.append("```\n")
    
    sections.append("Or run specific validators:\n")
    sections.append("```bash")
    sections.append("# Validate environment configuration")
    sections.append("python validation_framework/config_validators/env_validator.py")
    sections.append("")
    sections.append("# Check API endpoints")
    sections.append("python validation_framework/api_tests/api_validator.py --url https://api.example.com")
    sections.append("")
    sections.append("# Run load tests")
    sections.append("python validation_framework/performance_tests/load_tester.py --url https://example.com")
    sections.append("```\n")
    
    # Add validator descriptions
    sections.append("## Validators\n")
    
    # Configuration validators
    sections.append("### Configuration Validators\n")
    for file_path in validator_files.get("config", []):
        file_name = os.path.basename(file_path)
        docstring = _extract_module_docstring(file_path)
        
        sections.append(f"#### {file_name}\n")
        if docstring:
            sections.append(docstring + "\n")
            
        # Try to extract functions
        module = _load_module(file_path)
        if module:
            functions = [name for name, obj in inspect.getmembers(module) 
                        if inspect.isfunction(obj) and not name.startswith('_')]
            
            if functions:
                sections.append("**Functions:**\n")
                for func_name in functions:
                    sections.append(f"- `{func_name}`")
                sections.append("")
    
    # API validators
    sections.append("### API Validators\n")
    for file_path in validator_files.get("api", []):
        file_name = os.path.basename(file_path)
        docstring = _extract_module_docstring(file_path)
        
        sections.append(f"#### {file_name}\n")
        if docstring:
            sections.append(docstring + "\n")
    
    # Security tests
    sections.append("### Security Tests\n")
    for file_path in validator_files.get("security", []):
        file_name = os.path.basename(file_path)
        docstring = _extract_module_docstring(file_path)
        
        sections.append(f"#### {file_name}\n")
        if docstring:
            sections.append(docstring + "\n")
    
    # Performance tests
    sections.append("### Performance Tests\n")
    for file_path in validator_files.get("performance", []):
        file_name = os.path.basename(file_path)
        docstring = _extract_module_docstring(file_path)
        
        sections.append(f"#### {file_name}\n")
        if docstring:
            sections.append(docstring + "\n")
    
    # Deployment checks
    sections.append("### Deployment Checks\n")
    for file_path in validator_files.get("deployment", []):
        file_name = os.path.basename(file_path)
        docstring = _extract_module_docstring(file_path)
        
        sections.append(f"#### {file_name}\n")
        if docstring:
            sections.append(docstring + "\n")
    
    # Example configurations
    sections.append("## Example Configurations\n")
    
    # API validator example
    sections.append("### API Validator Configuration\n")
    sections.append("Create a JSON file with API endpoints to validate:\n")
    sections.append("```json")
    sections.append("""{
  "endpoints": [
    {
      "endpoint": "/api/health",
      "method": "GET",
      "expected_status": 200,
      "required_fields": ["status", "version"]
    },
    {
      "endpoint": "/api/users",
      "method": "GET",
      "expected_status": 200,
      "expected_content_type": "application/json",
      "authentication_required": true
    },
    {
      "endpoint": "/api/login",
      "method": "POST",
      "expected_status": 200,
      "payload": {
        "username": "test_user",
        "password": "password123"
      },
      "required_fields": ["token", "user_id"]
    }
  ]
}""")
    sections.append("```\n")
    
    # Load tester example
    sections.append("### Load Tester Configuration\n")
    sections.append("Example of running load tests:\n")
    sections.append("```bash")
    sections.append("python validation_framework/performance_tests/load_tester.py \\")
    sections.append("    --url https://api.example.com \\")
    sections.append("    --users 50 \\")
    sections.append("    --duration 60 \\")
    sections.append("    --max-response-time 500")
    sections.append("```\n")
    
    # Extending the framework
    sections.append("## Extending the Framework\n")
    sections.append(
        "You can extend this framework with your own custom validators:\n\n"
        "1. Create a new Python file in the appropriate subdirectory\n"
        "2. Implement your validation logic\n"
        "3. Include a main section that allows it to be run standalone\n"
        "4. Add the validator to the main `validate_production_readiness.py` file\n\n"
        "Example of a custom validator:\n"
    )
    
    sections.append("```python")
    sections.append('''#!/usr/bin/env python
"""
Custom Validator
==============

This validator checks [describe what it validates].
"""

def validate_something(config_value):
    """
    Validates something important.
    
    Args:
        config_value: The value to validate
        
    Returns:
        Dict with validation results
    """
    result = {
        "name": "My Custom Validator",
        "passed": False,
        "tests": []
    }
    
    # Your validation logic here
    # ...
    
    return result

if __name__ == "__main__":
    # Standalone execution
    import sys
    
    try:
        result = validate_something("test_value")
        print(f"Custom Validation: {'PASSED' if result['passed'] else 'FAILED'}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)''')
    sections.append("```\n")
    
    return "\n".join(sections)

def generate_example_config(config_type: str) -> str:
    """
    Generate example configuration file.
    
    Args:
        config_type: Type of configuration to generate
        
    Returns:
        Configuration file content
    """
    if config_type == "api":
        return """{
  "endpoints": [
    {
      "endpoint": "/",
      "method": "GET",
      "expected_status": 200
    },
    {
      "endpoint": "/api/health",
      "method": "GET",
      "expected_status": 200,
      "required_fields": ["status", "version", "timestamp"]
    },
    {
      "endpoint": "/api/users",
      "method": "GET",
      "expected_status": 200,
      "expected_content_type": "application/json",
      "authentication_required": true
    },
    {
      "endpoint": "/api/auth/login",
      "method": "POST",
      "expected_status": 200,
      "expected_content_type": "application/json",
      "payload": {
        "username": "test_user",
        "password": "test_password"
      },
      "required_fields": ["token", "user", "expires_at"]
    },
    {
      "endpoint": "/api/products",
      "method": "GET",
      "expected_status": 200,
      "expected_content_type": "application/json",
      "required_fields": ["products", "total", "page"]
    }
  ]
}"""
    elif config_type == "env":
        return """# Required environment variables
REQUIRED_ENV_VARS = [
    # Database
    "DATABASE_URL",
    "DATABASE_USERNAME",
    "DATABASE_PASSWORD",
    
    # API keys
    "API_KEY",
    "SECRET_KEY",
    
    # Application settings
    "PORT",
    "NODE_ENV",
    "LOG_LEVEL"
]

# Production-only environment variables
PRODUCTION_ENV_VARS = [
    "SENTRY_DSN",
    "PROMETHEUS_ENDPOINT",
    "REDIS_URL",
    "CDN_URL"
]

# Security-sensitive environment variables that should be checked
SECURITY_ENV_VARS = [
    "JWT_SECRET",
    "ENCRYPTION_KEY",
    "API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "DATABASE_PASSWORD"
]"""
    elif config_type == "load":
        return '''#!/usr/bin/env python
""" 
Load Test Configuration
===================

Example configuration for load testing.
"""

# Target API configuration
BASE_URL = "https://api.example.com"
AUTH_TOKEN = "your_auth_token_here"  # Optional

# Test parameters
NUM_USERS = 50          # Number of concurrent users to simulate
DURATION = 60           # Test duration in seconds
REQUEST_INTERVAL = 0.1  # Interval between requests (per user)
MAX_RESPONSE_TIME = 500  # Maximum acceptable response time in ms

# API endpoints to test
TEST_ENDPOINTS = [
    "/api/health",
    "/api/users?page=1&limit=10",
    "/api/products"
]'''
    else:
        return "# Example configuration not available for this type"

def generate_docs(framework_root: str) -> None:
    """
    Generate documentation for the validation framework.
    
    Args:
        framework_root: Root directory of the validation framework
    """
    try:
        # Create docs directory if it doesn't exist
        docs_dir = os.path.join(framework_root, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Generate README
        readme_content = generate_readme(framework_root)
        readme_path = os.path.join(framework_root, "README.md")
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Generate example configurations
        examples_dir = os.path.join(docs_dir, "examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        # API validator example
        api_example = generate_example_config("api")
        api_example_path = os.path.join(examples_dir, "api_endpoints.json")
        
        with open(api_example_path, 'w', encoding='utf-8') as f:
            f.write(api_example)
        
        # Environment validator example
        env_example = generate_example_config("env")
        env_example_path = os.path.join(examples_dir, "env_config.py")
        
        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write(env_example)
        
        # Load tester example
        load_example = generate_example_config("load")
        load_example_path = os.path.join(examples_dir, "load_test_config.py")
        
        with open(load_example_path, 'w', encoding='utf-8') as f:
            f.write(load_example)
            
        logger.info(f"Documentation generated successfully in {framework_root}")
        
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate documentation for the validation framework")
    parser.add_argument("--path", "-p", help="Path to validation framework root", required=True)
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        generate_docs(args.path)
        print("Documentation generated successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
