from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple


Category = Literal["blood", "dexa"]


FILENAME_RE = re.compile(r"^(?P<city>.+)_(?P<kind>BLOOD|DEXA)_VALID\.json$", re.IGNORECASE)


@dataclass(frozen=True)
class DatasetKey:
    city: str
    category: Category


def _normalize_city(city: str) -> str:
    # Keep it simple: trim + preserve original casing style for display,
    # but internally compare case-insensitively.
    return city.strip()


def _normalize_category(category: str) -> Category:
    c = category.strip().lower()
    if c not in ("blood", "dexa"):
        raise ValueError(f"Invalid category: {category}")
    return c  # type: ignore[return-value]


def _data_dir() -> Path:
    """
    Data dir strategy:
    - Default: repo_root/data
    - Override with env DATA_DIR if needed (Docker, deployment, etc.)
    """
    env = os.getenv("DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()

    # backend/app/data_store.py -> backend/app -> backend -> repo_root
    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root / "data").resolve()


def discover_datasets() -> List[DatasetKey]:
    keys: List[DatasetKey] = []
    for p in _data_dir().glob("*_VALID.json"):
        m = FILENAME_RE.match(p.name)
        if not m:
            continue
        city = _normalize_city(m.group("city"))
        kind = m.group("kind").lower()
        category: Category = "blood" if kind == "blood" else "dexa"
        keys.append(DatasetKey(city=city, category=category))
    keys.sort(key=lambda k: (k.city.lower(), k.category))
    return keys


@lru_cache(maxsize=128)
def load_dataset(city: str, category: str) -> List[Dict[str, Any]]:
    city_n = _normalize_city(city)
    cat = _normalize_category(category)

    # Find matching file by parsing filenames (case-insensitive city match).
    target_kind = "BLOOD" if cat == "blood" else "DEXA"
    candidates = list(_data_dir().glob(f"*_{target_kind}_VALID.json"))

    target_file: Optional[Path] = None
    for p in candidates:
        m = FILENAME_RE.match(p.name)
        if not m:
            continue
        file_city = _normalize_city(m.group("city"))
        if file_city.lower() == city_n.lower():
            target_file = p
            break

    if not target_file:
        return []

    with target_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Expect list; if not, return empty to avoid frontend breakage.
    return data if isinstance(data, list) else []


def load_all(city: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    keys = discover_datasets()

    out: List[Dict[str, Any]] = []
    for k in keys:
        if city and k.city.lower() != city.strip().lower():
            continue
        if category and k.category != _normalize_category(category):
            continue

        items = load_dataset(k.city, k.category)
        # Add category + city for frontend filtering and marker styling
        for item in items:
            if isinstance(item, dict):
                item = dict(item)
                item["city"] = k.city
                item["category"] = k.category
                out.append(item)

    return out
