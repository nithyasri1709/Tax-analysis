"""
TaxRulesProvider
Loads and caches statutory tax rules from versioned JSON files.
Ensures zero hardcoded constants in business logic.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional


class TaxRulesProvider:
    _instance: Optional[TaxRulesProvider] = None
    _rules_cache: Dict[str, Dict[str, Any]] = {}
    _section_mapping_cache: Optional[Dict[str, Any]] = None

    def __init__(self, rules_dir: Optional[Path] = None):
        if rules_dir is None:
            self.rules_dir = Path(__file__).parent / "rules"
        else:
            self.rules_dir = Path(rules_dir)

    @classmethod
    def get_instance(cls, rules_dir: Optional[Path] = None) -> TaxRulesProvider:
        if cls._instance is None:
            cls._instance = TaxRulesProvider(rules_dir)
        return cls._instance

    @classmethod
    def reset_cache(cls) -> None:
        cls._rules_cache.clear()
        cls._section_mapping_cache = None

    def _normalize_fy(self, fy: str) -> str:
        # Accepts '2024-25', '2024-2025', 'fy2024_25', '24-25'
        clean = fy.lower().replace("fy", "").replace("_", "-").strip()
        if "/" in clean:
            clean = clean.replace("/", "-")
        parts = clean.split("-")
        if len(parts) == 2:
            start_yr = parts[0]
            end_yr = parts[1]
            if len(start_yr) == 4 and len(end_yr) == 2:
                return f"{start_yr}-{end_yr}"
            if len(start_yr) == 4 and len(end_yr) == 4:
                return f"{start_yr}-{end_yr[2:]}"
        return clean

    def get_rules_for_fy(self, fy: str) -> Dict[str, Any]:
        norm_fy = self._normalize_fy(fy)
        filename_map = {
            "2024-25": "fy2024_25.json",
            "2025-26": "fy2025_26.json",
            "2026-27": "fy2026_27.json",
        }

        if norm_fy not in filename_map:
            available = list(filename_map.keys())
            raise ValueError(f"Unsupported Financial Year '{fy}'. Available FYs: {available}")

        if norm_fy in self._rules_cache:
            return self._rules_cache[norm_fy]

        file_path = self.rules_dir / filename_map[norm_fy]
        if not file_path.exists():
            raise FileNotFoundError(f"Tax rules file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._rules_cache[norm_fy] = data
        return data

    def get_section_mapping(self) -> Dict[str, Any]:
        if self._section_mapping_cache is not None:
            return self._section_mapping_cache

        file_path = self.rules_dir / "section_mapping.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Section mapping file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._section_mapping_cache = data
        return data

    def get_available_financial_years(self) -> list[str]:
        return ["2024-25", "2025-26", "2026-27"]
