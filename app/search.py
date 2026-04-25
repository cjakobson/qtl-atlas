from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Optional, Tuple

import numpy as np
import pandas as pd

CATEGORICAL_FILTERS = ["chr", "variantType", "snpIndel", "isQtn", "isTx", "promoter"]
NUMERIC_FILTERS = ["pVal", "beta", "varExp", "dist", "percentage"]
SORTABLE_COLUMNS = ["pVal", "beta", "varExp", "dist", "percentage", "protein"]


@dataclass
class SearchQuery:
    q: str = ""
    protein: str = ""
    common_name: str = ""
    gene: str = ""
    chr_value: str = ""
    variant_type: str = ""
    snp_indel: str = ""
    is_qtn: str = ""
    is_tx: str = ""
    promoter: str = ""
    pval_min: Optional[float] = None
    pval_max: Optional[float] = None
    beta_min: Optional[float] = None
    beta_max: Optional[float] = None
    varexp_min: Optional[float] = None
    varexp_max: Optional[float] = None
    dist_min: Optional[float] = None
    dist_max: Optional[float] = None
    percentage_min: Optional[float] = None
    percentage_max: Optional[float] = None
    sort_by: str = "pVal"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 50


def _contains(series: pd.Series, term: str) -> pd.Series:
    return series.fillna("").astype(str).str.contains(term, case=False, na=False, regex=False)


def _apply_keyword(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    if not keyword:
        return df

    masks = [_contains(df[col], keyword) for col in df.columns]
    if not masks:
        return df

    combined = masks[0]
    for mask in masks[1:]:
        combined = combined | mask
    return df[combined]


def _apply_partial_match(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if not value or column not in df.columns:
        return df
    return df[_contains(df[column], value)]


def _apply_exact_match(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if not value or column not in df.columns:
        return df
    return df[df[column].fillna("").astype(str) == value]


def _apply_range(df: pd.DataFrame, column: str, min_value: Optional[float], max_value: Optional[float]) -> pd.DataFrame:
    if column not in df.columns:
        return df

    out = df
    if min_value is not None:
        out = out[out[column] >= min_value]
    if max_value is not None:
        out = out[out[column] <= max_value]
    return out


def apply_filters(df: pd.DataFrame, query: SearchQuery) -> pd.DataFrame:
    filtered = _apply_keyword(df, query.q.strip())
    filtered = _apply_partial_match(filtered, "protein", query.protein.strip())
    filtered = _apply_partial_match(filtered, "commonName", query.common_name.strip())

    if query.gene.strip():
        gene_term = query.gene.strip()
        gene_mask = pd.Series(False, index=filtered.index)
        for column in ["gene1", "gene2"]:
            if column in filtered.columns:
                gene_mask = gene_mask | _contains(filtered[column], gene_term)
        filtered = filtered[gene_mask]

    filtered = _apply_exact_match(filtered, "chr", query.chr_value.strip())
    filtered = _apply_exact_match(filtered, "variantType", query.variant_type.strip())
    filtered = _apply_exact_match(filtered, "snpIndel", query.snp_indel.strip())
    filtered = _apply_exact_match(filtered, "isQtn", query.is_qtn.strip())
    filtered = _apply_exact_match(filtered, "isTx", query.is_tx.strip())
    filtered = _apply_exact_match(filtered, "promoter", query.promoter.strip())

    filtered = _apply_range(filtered, "pVal", query.pval_min, query.pval_max)
    filtered = _apply_range(filtered, "beta", query.beta_min, query.beta_max)
    filtered = _apply_range(filtered, "varExp", query.varexp_min, query.varexp_max)
    filtered = _apply_range(filtered, "dist", query.dist_min, query.dist_max)
    filtered = _apply_range(filtered, "percentage", query.percentage_min, query.percentage_max)

    return filtered


def apply_sort(df: pd.DataFrame, sort_by: str, sort_order: str) -> pd.DataFrame:
    column = sort_by if sort_by in SORTABLE_COLUMNS and sort_by in df.columns else "pVal"
    ascending = sort_order != "desc"
    return df.sort_values(by=column, ascending=ascending, na_position="last")


def paginate(df: pd.DataFrame, page: int, page_size: int) -> Tuple[pd.DataFrame, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    total_pages = max(1, ceil(len(df) / page_size))
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    return df.iloc[start:end], total_pages


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    clean = df.replace([np.inf, -np.inf], pd.NA)
    clean = clean.astype(object).where(pd.notna(clean), None)
    return clean.to_dict(orient="records")
