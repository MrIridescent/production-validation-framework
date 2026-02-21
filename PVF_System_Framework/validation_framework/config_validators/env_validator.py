#!/usr/bin/env python
"""
Environment Configuration Validator
==================================

This module validates that all required environment variables are properly
configured in the .env file for production use.

It checks for:
1. Presence of all required sections
2. Proper formatting of values
3. Security of sensitive values
4. Production readiness of configurations
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dotenv import dotenv_values

logger = logging.getLogger("EnvValidator")

# Validation Schema - Defines types, requirements, and security constraints
ENV_SCHEMA = {
    "CORE PLATFORM CONFIGURATION": {
        "ENVIRONMENT": {"type": "str", "allowed": ["development", "staging", "production"], "required": True},
        "DEBUG": {"type": "bool", "required": True},
        "LOG_LEVEL": {"type": "str", "allowed": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "required": True},
        "PLATFORM_NAME": {"type": "str", "required": True},
        "PLATFORM_VERSION": {"type": "str", "required": True}
    },
    "DATABASE CONFIGURATION": {
        "DATABASE_URL": {"type": "url", "required": True, "no_sqlite_prod": True},
        "DATABASE_ENCRYPTION_KEY": {"type": "secret", "min_len": 32, "required": True}
    },
    "JWT AUTHENTICATION & SECURITY": {
        "JWT_SECRET_KEY": {"type": "secret", "min_len": 32, "required": True},
        "JWT_ALGORITHM": {"type": "str", "allowed": ["HS256", "RS256"], "required": True},
        "JWT_EXPIRATION_HOURS": {"type": "int", "min": 1, "required": True},
        "ENCRYPTION_KEY": {"type": "secret", "min_len": 32, "required": True},
        "SSL_ENABLED": {"type": "bool", "required": False, "default": "false", "prod_require": "true"}
    },
    "WEB SERVER & API CONFIGURATION": {
        "API_HOST": {"type": "str", "required": True},
        "API_PORT": {"type": "int", "min": 1, "max": 65535, "required": True},
        "API_CORS_ORIGINS": {"type": "list", "required": True}
    },
    "EMAIL CONFIGURATION": {
        "SMTP_SERVER": {"type": "str", "required": True},
        "SMTP_PORT": {"type": "int", "min": 1, "max": 65535, "required": True},
        "SMTP_USE_TLS": {"type": "bool", "required": True},
        "SMTP_FROM_EMAIL": {"type": "email", "required": True}
    },
    "BACKUP & MONITORING": {
        "BACKUP_ENABLED": {"type": "bool", "required": True},
        "BACKUP_INTERVAL_HOURS": {"type": "int", "min": 1, "required": True},
        "HEALTH_CHECK_INTERVAL": {"type": "int", "min": 1, "required": True}
    }
}

def is_placeholder(value: str) -> bool:
    """Check if a value is a placeholder or default."""
    placeholders = ["your-secret-here", "REPLACE_ME", "example", "placeholder", "TODO"]
    return any(p.lower() in value.lower() for p in placeholders) or len(set(value)) < 3

def parse_env_sections(content: str) -> List[str]:
    """Parse section headers from .env file comments."""
    sections = []
    lines = content.split('\n')
    for line in lines:
        if line.startswith('#'):
            section = line.lstrip('#').strip()
            if section in ENV_SCHEMA:
                sections.append(section)
    return sections

def validate_type(value: Any, rule: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a value against a specific type rule."""
    v_type = rule.get("type", "str")
    
    if v_type == "bool":
        return value.lower() in ["true", "false", "1", "0", "yes", "no"], f"Must be a boolean value, got '{value}'"
    
    if v_type == "int":
        try:
            val = int(value)
            if "min" in rule and val < rule["min"]:
                return False, f"Value {val} is below minimum {rule['min']}"
            if "max" in rule and val > rule["max"]:
                return False, f"Value {val} is above maximum {rule['max']}"
            return True, ""
        except ValueError:
            return False, f"Must be an integer, got '{value}'"
            
    if v_type == "url":
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        # Some DB URLs don't strictly follow HTTP URL patterns (e.g. postgresql://)
        # So we just check for basic protocol://host structure
        if "://" in value:
            return True, ""
        return False, f"Must be a valid connection URL, got '{value}'"

    if v_type == "email":
        return "@" in value and "." in value.split("@")[1], f"Must be a valid email, got '{value}'"
        
    if v_type == "secret":
        if is_placeholder(value):
            return False, "Value appears to be a placeholder"
        if "min_len" in rule and len(value) < rule["min_len"]:
            return False, f"Secret is too short (min {rule['min_len']} chars)"
        return True, ""
        
    if v_type == "list":
        return len(value.split(",")) > 0, "Must be a comma-separated list"

    if "allowed" in rule and value not in rule["allowed"]:
        return False, f"Value '{value}' not in allowed list: {', '.join(rule['allowed'])}"

    return True, ""

def validate_env_file(env_file_path: str, required_sections: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate the environment file for production readiness using enhanced schema.
    """
    logger.info(f"Validating environment file: {env_file_path}")
    
    if required_sections is None:
        required_sections = list(ENV_SCHEMA.keys())
        
    results = {
        "passed": False,
        "total": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "tests": []
    }
    
    try:
        # Load environment variables
        if not os.path.exists(env_file_path):
            results["tests"].append({
                "name": "File existence check",
                "status": "FAIL",
                "message": f"Environment file {env_file_path} does not exist"
            })
            results["total"] = 1
            results["failed_tests"] = 1
            return results

        env_vars = dotenv_values(env_file_path)
        
        # Read file for section headers check
        with open(env_file_path, 'r') as f:
            content = f.read()
        env_sections = parse_env_sections(content)

        is_production = env_vars.get("ENVIRONMENT", "").lower() == "production"

        for section_name, section_rules in ENV_SCHEMA.items():
            if section_name not in required_sections:
                continue

            # Section header check
            section_present = section_name in env_sections
            results["tests"].append({
                "name": f"Section check: {section_name}",
                "status": "PASS" if section_present else "WARNING",
                "message": f"Section '{section_name}' is documented" if section_present else f"Section header '{section_name}' missing from comments"
            })
            results["total"] += 1
            results["passed_tests"] += 1 # WARNING doesn't fail the build

            for var_name, rule in section_rules.items():
                val = env_vars.get(var_name)
                
                # Presence check
                if val is None or val == "":
                    if rule.get("required", False):
                        results["tests"].append({
                            "name": f"Variable presence: {var_name}",
                            "status": "FAIL",
                            "message": f"Mandatory variable {var_name} is missing"
                        })
                        results["failed_tests"] += 1
                    else:
                        results["tests"].append({
                            "name": f"Variable presence: {var_name}",
                            "status": "PASS",
                            "message": f"Optional variable {var_name} is missing"
                        })
                        results["passed_tests"] += 1
                    results["total"] += 1
                    continue

                # Type and rule validation
                is_valid, msg = validate_type(val, rule)
                
                # Production specific checks
                if is_production:
                    if rule.get("no_sqlite_prod") and "sqlite" in val.lower():
                        is_valid, msg = False, "SQLite is not allowed in production"
                    if "prod_require" in rule and val.lower() != rule["prod_require"].lower():
                        is_valid, msg = False, f"In production, {var_name} must be {rule['prod_require']}"

                results["tests"].append({
                    "name": f"Variable validation: {var_name}",
                    "status": "PASS" if is_valid else "FAIL",
                    "message": f"{var_name} is valid" if is_valid else f"{var_name} invalid: {msg}"
                })
                results["total"] += 1
                if is_valid:
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
        
        # Overall result
        results["passed"] = results["failed_tests"] == 0
        
    except Exception as e:
        logger.error(f"Error validating environment file: {str(e)}")
        results["passed"] = False
        results["error"] = str(e)
        
    return results

def validate_env_config(env_file_path: str) -> Dict[str, Any]:
    """
    Alias for validate_env_file to support legacy calls.
    """
    return validate_env_file(env_file_path)

if __name__ == "__main__":
    # Simple standalone test
    import sys
    if len(sys.argv) > 1:
        env_path = sys.argv[1]
    else:
        env_path = ".env"
        
    logging.basicConfig(level=logging.INFO)
    result = validate_env_file(env_path)
    
    print(f"Environment Validation Results:")
    print(f"Passed: {result['passed']}")
    print(f"Tests: {result['passed_tests']}/{result['total']} passed")
    
    for test in result["tests"]:
        status_symbol = "✓" if test["status"] == "PASS" else "✗"
        print(f"{status_symbol} {test['name']}: {test['message']}")
