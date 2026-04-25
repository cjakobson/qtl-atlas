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
                "common1": "STB5",
                "common2": "",
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
                "common1": "",
                "common2": "",
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
    query = SearchQuery(q="gnd1", chr_value="8", pval_min=10, pval_max=20, search_mode="targets")
    filtered = apply_filters(df, query)
    assert len(filtered) == 1
    assert filtered.iloc[0]["protein"] == "YHR183W"


def test_keyword_regulators_searches_gene_and_common_fields():
    df = _sample_df()
    query = SearchQuery(q="YHR178W", search_mode="regulators")
    filtered = apply_filters(df, query)
    assert len(filtered) == 1
    assert filtered.iloc[0]["protein"] == "YHR183W"

    query_common = SearchQuery(q="STB5", search_mode="regulators")
    filtered2 = apply_filters(df, query_common)
    assert len(filtered2) == 1


def test_keyword_targets_does_not_match_regulator_only_fields():
    df = _sample_df()
    query = SearchQuery(q="YHR178W", search_mode="targets")
    filtered = apply_filters(df, query)
    assert len(filtered) == 0


def test_sort_descending_by_pval():
    df = _sample_df()
    sorted_df = apply_sort(df, sort_by="pVal", sort_order="desc")
    assert sorted_df.iloc[0]["pVal"] == 26.34


def test_sort_by_common_name():
    df = _sample_df()
    sorted_df = apply_sort(df, sort_by="commonName", sort_order="asc")
    assert sorted_df.iloc[0]["commonName"] == "GND1"


def test_paginate_caps_and_reports_total_pages():
    df = pd.concat([_sample_df()] * 3, ignore_index=True)
    page_df, total_pages = paginate(df, page=2, page_size=2)
    assert len(page_df) == 2
    assert total_pages == 3
