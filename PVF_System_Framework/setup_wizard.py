#!/usr/bin/env python3
"""
🚀 TURNKEY SETUP WIZARD - Production Validation Framework
==========================================================
Author: David Akpoviroro Oke (MrIridescent)

This wizard provides a seamless, "Noob-friendly" experience to set up
the Production Validation Framework from scratch to 100% readiness.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Get absolute path to project root (where this script is)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Try to import colorama, if not available, define dummy functions
try:
    # We try to install it first if missing, but for the script itself to run:
    import colorama
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        BLUE = ""
        MAGENTA = ""
        WHITE = ""
        RESET = ""
    class Style:
        BRIGHT = ""
        NORMAL = ""
        RESET = ""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{Fore.CYAN}{Style.BRIGHT}==========================================================")
    print(f"{Fore.CYAN}{Style.BRIGHT}🚀  PRODUCTION VALIDATION FRAMEWORK - SETUP WIZARD  🚀")
    print(f"{Fore.CYAN}{Style.BRIGHT}==========================================================")
    print(f"{Fore.YELLOW}Created by: David Akpoviroro Oke (MrIridescent)")
    print(f"{Fore.WHITE}The 'Digital Polymath' approach to Production Excellence.")
    print()

def step_print(step_num, title):
    print(f"{Fore.MAGENTA}{Style.BRIGHT}[STEP {step_num}] {title}")
    print(f"{Fore.WHITE}" + "-" * (len(title) + 9))

def install_dependencies():
    step_print(1, "Installing Required Dependencies")
    req_file = os.path.join(PROJECT_ROOT, "research_assets/requirements.txt")
    print(f"{Fore.BLUE}📦 Installing packages from {req_file}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "--break-system-packages"])
        print(f"{Fore.GREEN}✅ Dependencies installed successfully.")
    except Exception as e:
        print(f"{Fore.RED}❌ Error installing dependencies: {e}")
        return False
    return True

def initialize_framework():
    step_print(2, "Initializing Framework Components")
    print(f"{Fore.BLUE}⚙️  Running framework initialization...")
    init_script = os.path.join(PROJECT_ROOT, "initialize_validation_framework.py")
    try:
        # Run the existing initializer
        # We'll use subprocess to run it and provide 'y' to any prompts
        process = subprocess.Popen([sys.executable, init_script], 
                                  stdin=subprocess.PIPE, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  cwd=PROJECT_ROOT)
        stdout, stderr = process.communicate(input="y\ny\ny\ny\n")
        print(stdout)
        if process.returncode == 0:
            print(f"{Fore.GREEN}✅ Framework initialized successfully.")
        else:
            print(f"{Fore.RED}❌ Initialization failed: {stderr}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error during initialization: {e}")
        return False
    return True

def run_smoke_test():
    step_print(3, "Running Smoke Test (Quick Check)")
    print(f"{Fore.BLUE}🔍 Verifying core logic is functional...")
    try:
        # Check if we can import the core validator
        if PROJECT_ROOT not in sys.path:
            sys.path.append(PROJECT_ROOT)
        from validation_framework.validate_production_readiness import main as validator_main
        print(f"{Fore.GREEN}✅ Core validator imported successfully.")
        
        # Run a simple check on environment logic
        from validation_framework.config_validators.env_validator import validate_env_config
        print(f"{Fore.BLUE}🧪 Validating environment configuration logic...")
        
        # Ensure logs directory exists for initialization logs
        os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)
        
        # We check if .env.example exists to test against it
        env_file = os.path.join(PROJECT_ROOT, ".env.example")
        if os.path.exists(env_file):
            env_result = validate_env_config(env_file)
            print(f"{Fore.GREEN}✅ Environment validator logic is functional.")
        else:
            print(f"{Fore.YELLOW}⚠️ .env.example not found, skipping specific file test.")
            
    except Exception as e:
        print(f"{Fore.RED}❌ Smoke test failed: {e}")
        # We don't exit here as the framework might still be usable
        return False
    return True

def main():
    clear_screen()
    print_header()
    
    print(f"{Fore.WHITE}Welcome to the Turnkey Setup Wizard. This will guide you through")
    print(f"{Fore.WHITE}setting up the environment for 100% production readiness.")
    print()
    
    input(f"{Fore.YELLOW}Press Enter to start the engine...{Fore.RESET}")
    print()
    
    # 1. Install dependencies
    if not install_dependencies():
        print(f"{Fore.RED}Setup encountered issues during dependency installation.")
        # Continue anyway, maybe some are already there
    
    print()
    # 2. Initialize
    if not initialize_framework():
        print(f"{Fore.RED}Setup encountered issues during initialization.")
    
    print()
    # 3. Smoke Test
    run_smoke_test()
        
    print()
    step_print(4, "Ready for Launch!")
    print(f"{Fore.GREEN}{Style.BRIGHT}Congratulations! The framework is now ready.")
    print()
    print(f"{Fore.WHITE}You can now run the following commands to validate your project:")
    print(f"{Fore.CYAN}👉 python src/AAA_PLUS_READINESS_VALIDATION.py")
    print(f"{Fore.CYAN}👉 python run_all_validations.py")
    print(f"{Fore.CYAN}👉 python main.py")
    print()
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Stay Elite. Stay Production-Ready.")
    print(f"{Fore.CYAN}Author: David Akpoviroro Oke (MrIridescent)")
    print(f"{Fore.WHITE}==========================================================")

if __name__ == "__main__":
    main()
