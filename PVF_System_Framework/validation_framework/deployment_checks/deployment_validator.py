#!/usr/bin/env python
"""
Deployment Validator
==================

This module validates that the project is ready for deployment to production.
Tests include:
- CI/CD pipeline configuration
- Environment variable validation
- Build artifact validation
- Static asset optimization
- Docker configuration validation
"""

import os
import logging
import json
import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("DeploymentValidator")

# Patterns for CI/CD config files
CI_CONFIG_PATTERNS = {
    "github": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
    "gitlab": [".gitlab-ci.yml"],
    "azure": ["azure-pipelines.yml"],
    "jenkins": ["Jenkinsfile"],
    "circleci": [".circleci/config.yml"],
    "travis": [".travis.yml"]
}

# Patterns for container config files
CONTAINER_CONFIG_PATTERNS = {
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "kubernetes": ["kubernetes/*.yml", "kubernetes/*.yaml", "k8s/*.yml", "k8s/*.yaml", "*.yaml", "*.yml"]
}

class DeploymentValidator:
    """Validates deployment readiness for production."""
    
    def __init__(self, project_root: str):
        """
        Initialize the deployment validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = os.path.abspath(project_root)
        
    def _find_files(self, patterns: List[str]) -> List[str]:
        """
        Find files matching the given patterns.
        
        Args:
            patterns: List of glob patterns to match
            
        Returns:
            List of matching file paths
        """
        import glob
        
        found_files = []
        for pattern in patterns:
            # Convert to absolute path if not already
            if not os.path.isabs(pattern):
                pattern = os.path.join(self.project_root, pattern)
                
            # Find matching files
            matches = glob.glob(pattern, recursive=True)
            found_files.extend(matches)
            
        return found_files
        
    def check_ci_cd_configuration(self) -> Dict[str, Any]:
        """
        Check if CI/CD configuration exists and is valid.
        
        Returns:
            Dict with validation results
        """
        result = {
            "name": "CI/CD Configuration",
            "passed": False,
            "tests": []
        }
        
        # Check for CI/CD config files
        found_ci_configs = {}
        for ci_type, patterns in CI_CONFIG_PATTERNS.items():
            files = self._find_files(patterns)
            if files:
                found_ci_configs[ci_type] = files
        
        # Test 1: Check if any CI/CD config exists
        has_ci_config = len(found_ci_configs) > 0
        ci_config_test = {
            "name": "CI/CD configuration exists",
            "passed": has_ci_config,
            "message": f"Found configurations for: {', '.join(found_ci_configs.keys())}" if has_ci_config else
                      "No CI/CD configuration found"
        }
        result["tests"].append(ci_config_test)
        
        # Test 2: Check if the CI/CD config has deployment steps
        # This is a heuristic check based on keywords
        deployment_keywords = [
            "deploy", "production", "staging", "release", "publish", "push", "k8s", "kubernetes",
            "heroku", "azure", "aws", "gcp", "firebase", "netlify", "vercel"
        ]
        
        has_deployment_steps = False
        for ci_type, files in found_ci_configs.items():
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                    for keyword in deployment_keywords:
                        if keyword in content:
                            has_deployment_steps = True
                            break
                            
                    if has_deployment_steps:
                        break
                except:
                    pass
                    
            if has_deployment_steps:
                break
        
        deployment_steps_test = {
            "name": "CI/CD has deployment steps",
            "passed": has_deployment_steps,
            "message": "CI/CD configuration contains deployment steps" if has_deployment_steps else
                      "No deployment steps found in CI/CD configuration"
        }
        
        if has_ci_config:  # Only add this test if CI config exists
            result["tests"].append(deployment_steps_test)
        
        # Calculate overall result
        result["passed"] = all(test["passed"] for test in result["tests"])
        return result
    
    def check_container_configuration(self) -> Dict[str, Any]:
        """
        Check if container configuration exists and is valid.
        
        Returns:
            Dict with validation results
        """
        result = {
            "name": "Container Configuration",
            "passed": False,
            "tests": []
        }
        
        # Check for container config files
        found_container_configs = {}
        for container_type, patterns in CONTAINER_CONFIG_PATTERNS.items():
            files = self._find_files(patterns)
            if files:
                found_container_configs[container_type] = files
        
        # Test 1: Check if any container config exists
        has_container_config = len(found_container_configs) > 0
        container_config_test = {
            "name": "Container configuration exists",
            "passed": has_container_config,
            "message": f"Found configurations for: {', '.join(found_container_configs.keys())}" if has_container_config else
                      "No container configuration found"
        }
        result["tests"].append(container_config_test)
        
        # Test 2: If Dockerfile exists, check for basic best practices
        dockerfile_path = None
        for files in found_container_configs.get("docker", []):
            if os.path.basename(files) == "Dockerfile":
                dockerfile_path = files
                break
                
        if dockerfile_path:
            dockerfile_issues = []
            
            try:
                with open(dockerfile_path, 'r', encoding='utf-8') as f:
                    dockerfile_content = f.read()
                
                # Check for FROM instruction
                if not re.search(r'^\s*FROM\s+', dockerfile_content, re.MULTILINE):
                    dockerfile_issues.append("Missing FROM instruction")
                    
                # Check for specific tags (not latest)
                if re.search(r'FROM\s+[^:\s]+:latest', dockerfile_content):
                    dockerfile_issues.append("Using 'latest' tag (should use specific version)")
                    
                # Check for exposed ports
                if not re.search(r'^\s*EXPOSE\s+\d+', dockerfile_content, re.MULTILINE):
                    dockerfile_issues.append("No EXPOSE instruction found")
                    
                # Check for USER instruction (not running as root)
                if not re.search(r'^\s*USER\s+', dockerfile_content, re.MULTILINE):
                    dockerfile_issues.append("No USER instruction found (might be running as root)")
                    
                # Check for HEALTHCHECK
                if not re.search(r'^\s*HEALTHCHECK\s+', dockerfile_content, re.MULTILINE):
                    dockerfile_issues.append("No HEALTHCHECK instruction found")
                
                # Check for Read-Only Filesystem compatibility (Heuristic)
                # If there are lots of writes to non-standard locations
                if re.search(r'RUN\s+chmod\s+777', dockerfile_content):
                    dockerfile_issues.append("Permissive write permissions detected (chmod 777)")

                # Check for Multi-stage build
                if len(re.findall(r'^\s*FROM\s+', dockerfile_content, re.MULTILINE)) < 2:
                    dockerfile_issues.append("Not using multi-stage build (image might be larger than necessary)")

            except Exception as e:
                dockerfile_issues.append(f"Error analyzing Dockerfile: {str(e)}")
                
            dockerfile_test = {
                "name": "Dockerfile best practices",
                "passed": len(dockerfile_issues) == 0,
                "message": "Dockerfile follows best practices" if len(dockerfile_issues) == 0 else
                          f"Dockerfile issues: {', '.join(dockerfile_issues)}"
            }
            result["tests"].append(dockerfile_test)
        
        # Calculate overall result
        result["passed"] = all(test["passed"] for test in result["tests"])
        return result
    
    def check_build_configuration(self) -> Dict[str, Any]:
        """
        Check if build configuration exists and is valid.
        
        Returns:
            Dict with validation results
        """
        result = {
            "name": "Build Configuration",
            "passed": False,
            "tests": []
        }
        
        # Check for common build tools
        build_tools = {
            "npm": ["package.json"],
            "yarn": ["yarn.lock"],
            "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
            "gradle": ["build.gradle"],
            "maven": ["pom.xml"],
            "dotnet": ["*.csproj", "*.sln"]
        }
        
        found_build_tools = {}
        for tool, patterns in build_tools.items():
            files = self._find_files(patterns)
            if files:
                found_build_tools[tool] = files
        
        # Test 1: Check if any build tool config exists
        has_build_config = len(found_build_tools) > 0
        build_config_test = {
            "name": "Build tool configuration exists",
            "passed": has_build_config,
            "message": f"Found configurations for: {', '.join(found_build_tools.keys())}" if has_build_config else
                      "No build tool configuration found"
        }
        result["tests"].append(build_config_test)
        
        # Test 2: Check if package.json has build script (for npm/yarn projects)
        if "npm" in found_build_tools:
            package_json_path = found_build_tools["npm"][0]
            has_build_script = False
            
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                    
                if "scripts" in package_json:
                    build_scripts = [script for script in package_json["scripts"] 
                                  if script in ["build", "prod", "production", "dist"]]
                    has_build_script = len(build_scripts) > 0
            except:
                pass
                
            npm_build_test = {
                "name": "NPM build script exists",
                "passed": has_build_script,
                "message": "package.json has build script" if has_build_script else
                          "package.json is missing build script"
            }
            result["tests"].append(npm_build_test)
            
        # Calculate overall result
        result["passed"] = all(test["passed"] for test in result["tests"])
        return result
    
    def check_static_assets(self) -> Dict[str, Any]:
        """
        Check if static assets are optimized for production.
        
        Returns:
            Dict with validation results
        """
        result = {
            "name": "Static Assets",
            "passed": False,
            "tests": []
        }
        
        # Look for common static asset directories
        static_dirs = [
            "static", "public", "assets", "dist", "build",
            "www", "web", "client/build", "client/dist"
        ]
        
        found_static_dirs = []
        for static_dir in static_dirs:
            full_path = os.path.join(self.project_root, static_dir)
            if os.path.isdir(full_path):
                found_static_dirs.append(static_dir)
        
        # Test 1: Check if static assets directory exists
        has_static_dir = len(found_static_dirs) > 0
        static_dir_test = {
            "name": "Static assets directory exists",
            "passed": has_static_dir,
            "message": f"Found static directories: {', '.join(found_static_dirs)}" if has_static_dir else
                      "No static assets directory found"
        }
        result["tests"].append(static_dir_test)
        
        # If we have static directories, check for minified JS/CSS
        if has_static_dir:
            has_minified_assets = False
            
            for static_dir in found_static_dirs:
                js_files = self._find_files([f"{static_dir}/**/*.js"])
                css_files = self._find_files([f"{static_dir}/**/*.css"])
                
                # Check if any JS/CSS files have .min. in filename
                minified_files = [f for f in js_files + css_files if '.min.' in f]
                
                if minified_files:
                    has_minified_assets = True
                    break
                    
                # Check file content heuristic for minification (lack of newlines/whitespace)
                for f in js_files + css_files:
                    try:
                        with open(f, 'r', encoding='utf-8') as file:
                            content = file.read(1000)  # Read first 1000 chars
                            
                        # Heuristic: if avg line length > 100 chars, probably minified
                        lines = content.split('\n')
                        if lines and sum(len(line) for line in lines) / len(lines) > 100:
                            has_minified_assets = True
                            break
                    except:
                        pass
                        
                if has_minified_assets:
                    break
            
            minified_test = {
                "name": "Minified assets check",
                "passed": has_minified_assets,
                "message": "Project has minified JS/CSS assets" if has_minified_assets else
                          "No minified assets found (consider adding minification to build process)"
            }
            result["tests"].append(minified_test)
        
        # Calculate overall result
        result["passed"] = all(test["passed"] for test in result["tests"])
        return result
    
    def check_environment_config(self) -> Dict[str, Any]:
        """
        Check if environment configuration is properly set up.
        
        Returns:
            Dict with validation results
        """
        result = {
            "name": "Environment Configuration",
            "passed": False,
            "tests": []
        }
        
        # Check for environment config files
        env_files = self._find_files([".env", ".env.example", ".env.template", ".env.production", "env.yml", "config/*.env"])
        
        # Test 1: Check if env file exists
        has_env_file = len(env_files) > 0
        env_file_test = {
            "name": "Environment file exists",
            "passed": has_env_file,
            "message": f"Found environment files: {', '.join([os.path.basename(f) for f in env_files])}" if has_env_file else
                      "No environment configuration file found"
        }
        result["tests"].append(env_file_test)
        
        # Test 2: Check for .env.example if .env exists
        if has_env_file:
            env_path = next((f for f in env_files if os.path.basename(f) == ".env"), None)
            env_example_path = next((f for f in env_files if os.path.basename(f) in [".env.example", ".env.template"]), None)
            
            if env_path and not env_example_path:
                env_example_test = {
                    "name": "Environment example file",
                    "passed": False,
                    "message": "Missing .env.example or .env.template file"
                }
                result["tests"].append(env_example_test)
            
        # Calculate overall result
        result["passed"] = all(test["passed"] for test in result["tests"])
        return result
    
    def validate_deployment_readiness(self) -> Dict[str, Any]:
        """
        Run all deployment validation tests.
        
        Returns:
            Dict with validation results
        """
        results = {
            "passed": False,
            "total": 0,
            "passed_tests": 0,
            "sections": []
        }
        
        # Run all validators
        validators = [
            self.check_ci_cd_configuration,
            self.check_container_configuration,
            self.check_build_configuration,
            self.check_static_assets,
            self.check_environment_config
        ]
        
        for validator in validators:
            section_result = validator()
            results["sections"].append(section_result)
            
            # Count total and passed tests
            section_tests = section_result.get("tests", [])
            results["total"] += len(section_tests)
            results["passed_tests"] += sum(1 for test in section_tests if test.get("passed", False))
        
        # Calculate overall result
        results["passed"] = results["passed_tests"] == results["total"]
        
        return results

def validate_deployment_readiness(project_root: str) -> Dict[str, Any]:
    """
    Run deployment readiness validation tests.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dict with validation results
    """
    validator = DeploymentValidator(project_root)
    return validator.validate_deployment_readiness()

if __name__ == "__main__":
    # Simple standalone test
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate deployment readiness")
    parser.add_argument("--path", "-p", help="Path to project root", default=".")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        result = validate_deployment_readiness(args.path)
        
        print(f"Deployment Readiness Validation:")
        print(f"Overall: {'✓ PASSED' if result.get('passed', False) else '✗ FAILED'}")
        print(f"Tests: {result.get('passed_tests', 0)}/{result.get('total', 0)} passed\n")
        
        for section in result.get("sections", []):
            section_name = section.get("name", "Unknown")
            section_status = "✓" if section.get("passed", False) else "✗"
            
            print(f"{section_status} {section_name}")
            
            for test in section.get("tests", []):
                test_status = "✓" if test.get("passed", False) else "✗"
                print(f"  {test_status} {test.get('name', 'Unknown')}: {test.get('message', '')}")
            
            print("")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
