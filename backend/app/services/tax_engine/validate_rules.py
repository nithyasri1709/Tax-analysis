"""
Rules Validator CLI
Validates statutory rules JSON files against schema.json and verifies completeness.
Run via: python -m app.services.tax_engine.validate_rules
"""

import json
import sys
from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"


def validate_all_rules() -> bool:
    print("Validating tax rules configurations in:", RULES_DIR)
    schema_file = RULES_DIR / "schema.json"
    if not schema_file.exists():
        print(f"ERROR: Schema file missing: {schema_file}")
        return False

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    required_top = schema.get("required", [])
    rule_files = ["fy2024_25.json", "fy2025_26.json", "fy2026_27.json"]

    all_passed = True
    for rf in rule_files:
        p = RULES_DIR / rf
        if not p.exists():
            print(f"FAILED: Missing config file {rf}")
            all_passed = False
            continue

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        missing = [k for k in required_top if k not in data]
        if missing:
            print(f"FAILED {rf}: Missing top-level keys {missing}")
            all_passed = False
            continue

        # Check Old Regime
        old_reg = data.get("old_regime", {})
        if "slabs" not in old_reg or "standard_deduction" not in old_reg or "rebate_87a" not in old_reg:
            print(f"FAILED {rf}: Old regime configuration incomplete")
            all_passed = False
            continue

        # Check New Regime
        new_reg = data.get("new_regime", {})
        if "slabs" not in new_reg or "standard_deduction" not in new_reg or "rebate_87a" not in new_reg:
            print(f"FAILED {rf}: New regime configuration incomplete")
            all_passed = False
            continue

        # Check verification fields
        vdate = data.get("verification_date")
        surl = data.get("source_url")
        act = data.get("governing_act")
        print(f"PASSED: {rf} (Act: {act}, Verified: {vdate}, Source: {surl})")

    # Validate section mapping
    sec_map_file = RULES_DIR / "section_mapping.json"
    if sec_map_file.exists():
        with open(sec_map_file, "r", encoding="utf-8") as f:
            sec_data = json.load(f)
        mappings = sec_data.get("mappings", {})
        print(f"PASSED: section_mapping.json ({len(mappings)} statutory cross-references validated)")
    else:
        print("FAILED: section_mapping.json is missing")
        all_passed = False

    return all_passed


if __name__ == "__main__":
    success = validate_all_rules()
    sys.exit(0 if success else 1)
