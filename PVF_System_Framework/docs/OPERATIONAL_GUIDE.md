# 🛠️ OPERATIONAL GUIDE: Production Validation Framework
## Version 1.0.0 | Date: 2026-02-19
### Author: David Akpoviroro Oke (MrIridescent)

---

## 1. Quick Start (Turnkey Setup)
The framework is designed for **"Noob-friendly"** immediate use. Follow these steps:

1. **Clone the repository** to your local environment.
2. **Run the Setup Wizard**:
   ```bash
   python setup_wizard.py
   ```
3. **Follow the on-screen prompts**. The wizard will:
   - Install all required dependencies.
   - Initialize the validation framework.
   - Perform a smoke test to ensure everything is ready.

## 2. Core Operational Commands

### 2.1 The Master Validation Suite
To run the complete **AAA+++ Excellence Validation**:
```bash
python AAA_PLUS_READINESS_VALIDATION.py
```

### 2.2 Comprehensive Readiness Check
To perform a deep-dive production readiness audit:
```bash
python validation_framework/validate_production_readiness.py
```

### 2.3 Individual Validator Execution
You can run specific tests using `pytest`:
```bash
# Run API validation
pytest tests/test_api_complete.py

# Run full system tests
pytest tests/comprehensive_system_test.py
```

## 3. Configuration Management
All framework settings are centralized in `validation_framework/validation_config.json`. Key configuration areas include:
- **API Endpoints**: Target URLs and auth headers.
- **Database Connection**: Connection strings and schema expectations.
- **Environment Variables**: Required keys and secret policies.
- **Performance Thresholds**: Target response times and resource limits.

## 4. Understanding Reports
After each validation run, reports are generated in the project root:
- **`AAA_PLUS_READINESS_REPORT.json`**: Machine-readable status for CI/CD pipelines.
- **`TECHNICAL_VALIDATION_INVESTOR_REPORT.json`**: Comprehensive assessment for stakeholders.
- **`validation.log`**: Detailed execution logs for debugging.

## 5. Troubleshooting
- **Missing Dependencies**: Re-run `pip install -r requirements-testing.txt`.
- **API Connection Errors**: Verify the target services are running and accessible.
- **Validation Failures**: Check `validation.log` for specific error messages and remediation steps.

---
*© 2026 David Akpoviroro Oke. All Rights Reserved.*
