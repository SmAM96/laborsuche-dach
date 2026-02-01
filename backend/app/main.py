from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List, Optional, Literal

from .data_store import discover_datasets, load_all, load_dataset


app = FastAPI(
    title="Laborsuche DACH API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/datasets")
def datasets() -> List[Dict[str, str]]:
    """
    Returns which city/category datasets exist based on filenames.
    """
    return [{"city": k.city, "category": k.category} for k in discover_datasets()]


@app.get("/api/providers")
def providers(
    city: Optional[str] = Query(default=None, description="e.g. Berlin, Wien, Zurich"),
    category: Optional[Literal["blood", "dexa"]] = Query(default=None),
    status: Optional[str] = Query(default=None, description="Optional: YES/NO/QUESTIONABLE"),
) -> List[Dict[str, Any]]:
    """
    Unified endpoint for the frontend.
    Returns items with added fields: city, category.
    """
    items = load_all(city=city, category=category)

    if status:
        s = status.strip().upper()
        items = [x for x in items if str(x.get("status", "")).upper() == s]

    return items


@app.get("/api/providers/{city}/{category}")
def providers_by_path(city: str, category: Literal["blood", "dexa"]) -> List[Dict[str, Any]]:
    """
    Direct access if you want it (handy for debugging).
    """
    items = load_dataset(city, category)
    out: List[Dict[str, Any]] = []
    for x in items:
        if isinstance(x, dict):
            y = dict(x)
            y["city"] = city
            y["category"] = category
            out.append(y)
    return out


@app.get("/api/stats")
def stats() -> Dict[str, Any]:
    """
    Quick KPI endpoint for reviewers: counts per city/category.
    """
    keys = discover_datasets()
    result: Dict[str, Dict[str, int]] = {}
    for k in keys:
        city = k.city
        result.setdefault(city, {})
        result[city][k.category] = len(load_dataset(k.city, k.category))
    return result
