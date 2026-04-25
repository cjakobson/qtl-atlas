from __future__ import annotations

from io import StringIO
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.data import load_dataframe
from app.search import SearchQuery, apply_filters, apply_sort, paginate, to_records

app = FastAPI(title="Scientific Paper Search")
templates = Jinja2Templates(directory="app/templates")


def _optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return float(stripped)


def _search_query_from_request(
    q: str = "",
    protein: str = "",
    common_name: str = "",
    gene: str = "",
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
        protein=protein,
        common_name=common_name,
        gene=gene,
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
    columns = load_dataframe().columns.tolist()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "query": query,
            "columns": columns,
            "rows": to_records(result["rows"]),
            "total_hits": result["total_hits"],
            "total_pages": result["total_pages"],
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
