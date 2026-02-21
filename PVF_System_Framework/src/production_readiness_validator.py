#!/usr/bin/env python3
"""
🚀 PRODUCTION READINESS VALIDATOR - MASTER ENTRY POINT
=====================================================
Author: David Akpoviroro Oke (MrIridescent)

This is the main entry point for the Production Validation Framework.
It orchestrates all specialized validators to provide a final readiness score.
"""

import sys
import os
from validation_framework.validate_production_readiness import main as validator_main

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.append(os.getcwd())
    
    # Run the core validation suite
    print("🚀 INITIALIZING MASTER PRODUCTION READINESS VALIDATOR...")
    print("=" * 60)
    
    try:
        validator_main()
    except Exception as e:
        print(f"❌ Critical Error during validation: {e}")
        sys.exit(1)
