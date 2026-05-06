from __future__ import annotations

from io import StringIO
from typing import Any, Optional
from urllib.parse import urlencode

import numpy as np
import pandas as pd

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.data import load_dataframe
from app.search import (
    SEARCH_MODE_REGULATORS,
    SEARCH_MODE_TARGETS,
    SearchQuery,
    apply_filters,
    apply_sort,
    paginate,
    to_records,
)

app = FastAPI(title="Scientific Paper Search")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def _sort_href(column_key: str, query: SearchQuery) -> str:
    """Build query string for sorting by `column_key` (toggle order if already active)."""
    if query.sort_by == column_key:
        next_order = "asc" if query.sort_order == "desc" else "desc"
    else:
        next_order = "asc"
    params = {
        "q": query.q,
        "search_mode": query.search_mode,
        "sort_by": column_key,
        "sort_order": next_order,
        "page": "1",
        "page_size": str(query.page_size),
    }
    return "?" + urlencode(params)


REGULATOR_LINK_KEYS = frozenset({"gene1", "gene2", "common1", "common2"})
TARGET_LINK_KEYS = frozenset({"protein", "commonName"})


def _symbol_search_href(
    term: str | int | float | None,
    query: SearchQuery,
    search_mode: str,
) -> str:
    """Query string for a keyword search in the given mode (targets or regulators)."""
    if term is None:
        return ""
    t = str(term).strip()
    if not t or t.lower() in ("nan", "none", "<na>"):
        return ""
    params = {
        "q": t,
        "search_mode": search_mode,
        "page": "1",
        "sort_by": query.sort_by,
        "sort_order": query.sort_order,
        "page_size": str(query.page_size),
    }
    return "?" + urlencode(params)


def _regulator_href(term: str | int | float | None, query: SearchQuery) -> str:
    """Regulators search from gene1/gene2/common1/common2 cell values."""
    return _symbol_search_href(term, query, SEARCH_MODE_REGULATORS)


def _target_href(term: str | int | float | None, query: SearchQuery) -> str:
    """Targets search from protein / commonName cell values."""
    return _symbol_search_href(term, query, SEARCH_MODE_TARGETS)


VOLCANO_MAX_POINTS = 12_000
MANHATTAN_MAX_POINTS = 20_000


def _build_volcano_points(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows for regulators-mode volcano: beta (x), pVal (y), plus labels for hover."""
    if df.empty or "beta" not in df.columns or "pVal" not in df.columns:
        return []

    cols = ["beta", "pVal"]
    for optional in ("protein", "commonName", "gene1", "gene2"):
        if optional in df.columns:
            cols.append(optional)

    plot_df = df.loc[:, cols].dropna(subset=["beta", "pVal"])
    if plot_df.empty:
        return []

    if len(plot_df) > VOLCANO_MAX_POINTS:
        plot_df = plot_df.sample(n=VOLCANO_MAX_POINTS, random_state=1)

    clean = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["beta", "pVal"])
    return to_records(clean)


def _build_manhattan_points(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows for targets-mode Manhattan: pVal (y) vs pQTL index (x)."""
    if df.empty or "pVal" not in df.columns:
        return []

    cols = ["pVal"]
    for optional in ("index", "protein", "commonName", "gene1", "gene2", "common1", "common2"):
        if optional in df.columns:
            cols.append(optional)

    plot_df = df.loc[:, cols].replace([np.inf, -np.inf], np.nan).dropna(subset=["pVal"])
    if plot_df.empty:
        return []

    if "index" in plot_df.columns:
        plot_df["plotIndex"] = pd.to_numeric(plot_df["index"], errors="coerce")
    else:
        plot_df["plotIndex"] = np.arange(1, len(plot_df) + 1, dtype=float)

    plot_df = plot_df.dropna(subset=["plotIndex"])
    if plot_df.empty:
        return []

    if len(plot_df) > MANHATTAN_MAX_POINTS:
        plot_df = plot_df.sample(n=MANHATTAN_MAX_POINTS, random_state=1)

    return to_records(plot_df)


DISPLAY_COLUMNS = [
    ("protein", "protein"),
    ("commonName", "common name"),
    ("pVal", "pVal"),
    ("beta", "beta"),
    ("varExp", "varExp"),
    ("isQtn", "isQTN"),
    ("index", "index"),
    ("chr", "chr"),
    ("pos", "pos"),
    ("variantType", "variantType"),
    ("gene1", "gene1"),
    ("gene2", "gene2"),
    ("encoded", "encoded"),
    ("common1", "common1"),
    ("common2", "common2"),
]


def _optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return float(stripped)


def _normalize_search_mode(value: str) -> str:
    v = (value or "").strip().lower()
    if v == SEARCH_MODE_REGULATORS:
        return SEARCH_MODE_REGULATORS
    return SEARCH_MODE_TARGETS


def _search_query_from_request(
    q: str = "",
    search_mode: str = SEARCH_MODE_TARGETS,
    chr_value: str = Query(default="", alias="chr"),
    variant_type: str = "",
    snp_indel: str = "",
    is_qtn: str = "",
    is_tx: str = "",
    promoter: str = "",
    pval_min: Optional[str] = None,
    pval_max: Optional[str] = None,
    beta_min: Optional[str] = None,
    beta_max: Optional[str] = None,
    varexp_min: Optional[str] = None,
    varexp_max: Optional[str] = None,
    dist_min: Optional[str] = None,
    dist_max: Optional[str] = None,
    percentage_min: Optional[str] = None,
    percentage_max: Optional[str] = None,
    sort_by: str = "pVal",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> SearchQuery:
    return SearchQuery(
        q=q,
        search_mode=_normalize_search_mode(search_mode),
        chr_value=chr_value,
        variant_type=variant_type,
        snp_indel=snp_indel,
        is_qtn=is_qtn,
        is_tx=is_tx,
        promoter=promoter,
        pval_min=_optional_float(pval_min),
        pval_max=_optional_float(pval_max),
        beta_min=_optional_float(beta_min),
        beta_max=_optional_float(beta_max),
        varexp_min=_optional_float(varexp_min),
        varexp_max=_optional_float(varexp_max),
        dist_min=_optional_float(dist_min),
        dist_max=_optional_float(dist_max),
        percentage_min=_optional_float(percentage_min),
        percentage_max=_optional_float(percentage_max),
        sort_by=sort_by,
        sort_order=sort_order,
        page=max(page, 1),
        page_size=min(max(page_size, 1), 200),
    )


def _run_query(query: SearchQuery):
    df = load_dataframe()
    filtered = apply_filters(df, query)
    sorted_df = apply_sort(filtered, query.sort_by, query.sort_order)
    page_rows, total_pages = paginate(sorted_df, query.page, query.page_size)
    return {
        "total_hits": len(sorted_df),
        "total_pages": total_pages,
        "rows": page_rows,
        "all_rows": sorted_df,
    }


@app.get("/")
def index(request: Request, query: SearchQuery = Depends(_search_query_from_request)):
    result = _run_query(query)
    available_columns = set(load_dataframe().columns.tolist())
    display_columns = [{"key": key, "label": label} for key, label in DISPLAY_COLUMNS if key in available_columns]
    volcano_points: list[dict[str, Any]] = []
    manhattan_points: list[dict[str, Any]] = []
    if query.search_mode == SEARCH_MODE_REGULATORS:
        volcano_points = _build_volcano_points(result["all_rows"])
    elif query.search_mode == SEARCH_MODE_TARGETS:
        manhattan_points = _build_manhattan_points(result["all_rows"])
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "query": query,
            "display_columns": display_columns,
            "rows": to_records(result["rows"]),
            "total_hits": result["total_hits"],
            "total_pages": result["total_pages"],
            "sort_href": lambda k: _sort_href(k, query),
            "regulator_href": lambda t: _regulator_href(t, query),
            "regulator_link_keys": REGULATOR_LINK_KEYS,
            "target_href": lambda t: _target_href(t, query),
            "target_link_keys": TARGET_LINK_KEYS,
            "volcano_points": volcano_points,
            "manhattan_points": manhattan_points,
        },
    )


@app.get("/api/results")
def api_results(query: SearchQuery = Depends(_search_query_from_request)):
    result = _run_query(query)
    payload = {
        "total_hits": result["total_hits"],
        "total_pages": result["total_pages"],
        "page": query.page,
        "page_size": query.page_size,
        "rows": to_records(result["rows"]),
    }
    return JSONResponse(payload)


@app.get("/export.csv")
def export_csv(query: SearchQuery = Depends(_search_query_from_request)):
    result = _run_query(query)
    csv_buffer = StringIO()
    result["all_rows"].to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    headers = {"Content-Disposition": "attachment; filename=filtered_science_results.csv"}
    return StreamingResponse(iter([csv_buffer.getvalue()]), media_type="text/csv", headers=headers)
