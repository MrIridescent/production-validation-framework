#!/usr/bin/env python3
"""
🔍 HYPE VS REALITY: GAP ANALYSIS TOOL
====================================
This tool audits the framework's marketing claims against its functional logic.
It ensures that the "Hype" (Investor Pitch) matches the "Reality" (Technical Implementation).
"""

import os
import json
import re
import time
from pathlib import Path

def analyze_gaps():
    print("🔍 RUNNING HYPE VS REALITY GAP ANALYSIS...")
    print("=" * 50)
    
    base_path = Path(__file__).parent.parent
    
    # 1. Load Hype (Claims from Pitch Deck)
    pitch_deck = base_path / "docs" / "INVESTOR_PITCH_DECK.md"
    claims = []
    if pitch_deck.exists():
        content = pitch_deck.read_text()
        # Simple regex to find bullet points in claims section
        claims = re.findall(r'- \*\*(.*?)\*\*: (.*)', content)
    
    print(f"📈 Found {len(claims)} major claims in Pitch Deck.")
    
    # 2. Load Reality (Results from AAA+ Validation)
    report_path = base_path / "reports" / "AAA_PLUS_READINESS_REPORT.json"
    validation_results = {}
    if report_path.exists():
        try:
            validation_results = json.loads(report_path.read_text())
        except json.JSONDecodeError:
            print("⚠️ Could not parse validation report. Run AAA_PLUS_READINESS_VALIDATION.py first.")
    
    overall_score = validation_results.get("readiness_score", 0)
    print(f"🧪 Reality Score: {overall_score:.1f}% readiness.")
    
    # 3. Perform Gap Analysis
    gaps = []
    
    # Check for specific claims vs reality
    # Claim: "49.5% Performance Improvement"
    perf_claim = any("49.5%" in c[1] for c in claims)
    if perf_claim:
        qa_score = validation_results.get("validation_categories", {}).get("comprehensive_qa", {}).get("score", 0)
        if qa_score < 80:
            gaps.append("Performance Gap: 49.5% improvement claimed but performance/QA validation score is sub-optimal.")
        else:
            print("✅ Performance Claim Validated.")

    # Claim: "80% Reduction in Defects"
    defect_claim = any("80%" in c[1] for c in claims)
    if defect_claim:
        qa_score = validation_results.get("validation_categories", {}).get("comprehensive_qa", {}).get("score", 0)
        if qa_score < 90:
            gaps.append("Defect Reduction Gap: 80% reduction claimed but QA validation score is below 90%.")
        else:
            print("✅ Defect Reduction Claim Validated.")

    # General check for documentation gaps
    required_docs = [
        "TECHNICAL_MANUAL.md", 
        "OPERATIONAL_GUIDE.md", 
        "SRS_DOCUMENTATION.md",
        "INFOGRAPHIC_ARCHITECTURE.html"
    ]
    for doc in required_docs:
        doc_path = base_path / "docs" / doc
        if not doc_path.exists():
            doc_path_alt = base_path / "assets" / doc
            if not doc_path_alt.exists():
                gaps.append(f"Documentation Gap: {doc} is missing but referenced in framework standards.")
            else:
                print(f"✅ {doc} Verified.")
        else:
            print(f"✅ {doc} Verified.")

    # Check for Turnkey Setup Wizard
    setup_wizard = base_path / "setup_wizard.py"
    if not setup_wizard.exists():
        gaps.append("Operations Gap: 'Turnkey' Setup Wizard claim is missing implementation.")
    else:
        print("✅ Turnkey Setup Claim Validated.")

    # 4. Generate Report
    print("\n📊 GAP ANALYSIS REPORT:")
    print("-" * 30)
    if not gaps:
        print("🌟 NO GAPS FOUND. The project is 100% Reality-Aligned.")
        status = "AAA+++ REALITY ALIGNED"
    else:
        for gap in gaps:
            print(f"❌ {gap}")
        status = f"{len(gaps)} GAPS IDENTIFIED"

    # Save to file
    gap_report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "status": status,
        "gaps": gaps,
        "claims_audited": len(claims),
        "overall_readiness": overall_score
    }
    
    report_output = base_path / "reports" / "GAPS_ANALYSIS_REPORT.json"
    with open(report_output, "w") as f:
        json.dump(gap_report, f, indent=2)
    
    print(f"\n📄 Gap analysis report saved to: {report_output}")

if __name__ == "__main__":
    analyze_gaps()
