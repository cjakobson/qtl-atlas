import pandas as pd

from app.search import SearchQuery, apply_filters, apply_sort, paginate


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "protein": "YHR183W",
                "commonName": "GND1",
                "gene1": "YHR178W",
                "gene2": None,
                "variantType": "missense_variant",
                "context": "OD600",
                "chr": "8",
                "snpIndel": "SNP",
                "isQtn": "1",
                "isTx": "1",
                "promoter": "",
                "pVal": 15.06,
                "beta": -0.23,
                "varExp": 0.02,
                "dist": 11237,
                "percentage": 0.02,
            },
            {
                "protein": "YAL016W",
                "commonName": "TPD3",
                "gene1": "",
                "gene2": "",
                "variantType": "",
                "context": "OD600",
                "chr": "1",
                "snpIndel": "",
                "isQtn": "0",
                "isTx": "0",
                "promoter": "",
                "pVal": 26.34,
                "beta": 1.23,
                "varExp": 0.20,
                "dist": None,
                "percentage": 0.40,
            },
        ]
    )


def test_keyword_and_numeric_filters_reduce_results():
    df = _sample_df()
    query = SearchQuery(q="gnd1", chr_value="8", pval_min=10, pval_max=20)
    filtered = apply_filters(df, query)
    assert len(filtered) == 1
    assert filtered.iloc[0]["protein"] == "YHR183W"


def test_sort_descending_by_pval():
    df = _sample_df()
    sorted_df = apply_sort(df, sort_by="pVal", sort_order="desc")
    assert sorted_df.iloc[0]["pVal"] == 26.34


def test_paginate_caps_and_reports_total_pages():
    df = pd.concat([_sample_df()] * 3, ignore_index=True)
    page_df, total_pages = paginate(df, page=2, page_size=2)
    assert len(page_df) == 2
    assert total_pages == 3
