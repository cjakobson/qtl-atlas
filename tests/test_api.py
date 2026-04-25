import pandas as pd
from fastapi.testclient import TestClient

import app.main as main
from app.search import SearchQuery


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


def test_api_results_returns_filtered_rows(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)

    response = client.get(
        "/api/results",
        params={"q": "GND1", "chr": "8", "search_mode": "targets"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_hits"] == 1
    assert payload["rows"][0]["protein"] == "YHR183W"


def test_api_results_regulators_mode(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)

    response = client.get(
        "/api/results",
        params={"q": "YHR178W", "search_mode": "regulators"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_hits"] == 1
    assert payload["rows"][0]["protein"] == "YHR183W"


def test_export_csv_returns_download(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)

    response = client.get("/export.csv", params={"sort_by": "pVal", "sort_order": "asc"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=filtered_science_results.csv" == response.headers["content-disposition"]
    assert "protein,commonName" in response.text


def test_sort_href_toggles_order_for_same_column():
    q = SearchQuery(sort_by="pVal", sort_order="desc")
    href = main._sort_href("pVal", q)
    assert "sort_order=asc" in href
    q2 = SearchQuery(sort_by="pVal", sort_order="asc")
    assert "sort_order=desc" in main._sort_href("pVal", q2)


def test_build_volcano_points_drops_invalid_and_keeps_hover_fields():
    df = pd.DataFrame(
        [
            {"beta": 1.0, "pVal": 10.0, "protein": "Y1", "commonName": "A", "gene1": "G1", "gene2": None},
            {"beta": float("nan"), "pVal": 5.0, "protein": "Y2"},
            {"beta": 2.0, "pVal": float("inf"), "protein": "Y3"},
        ]
    )
    pts = main._build_volcano_points(df)
    assert len(pts) == 1
    assert pts[0]["protein"] == "Y1"
    assert pts[0]["beta"] == 1.0
    assert pts[0]["pVal"] == 10.0


def test_index_regulators_renders_volcano_plot(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "protein": "YHR183W",
                "commonName": "GND1",
                "gene1": "YHR178W",
                "gene2": None,
                "common1": "STB5",
                "common2": "",
                "pVal": 15.06,
                "beta": -0.23,
            },
        ]
        * 5
    )
    monkeypatch.setattr(main, "load_dataframe", lambda: df)
    client = TestClient(main.app)
    response = client.get("/", params={"search_mode": "regulators", "q": "YHR178W"})
    assert response.status_code == 200
    assert b"plotly-2.27.0.min.js" in response.content
    assert b"volcano-plot" in response.content


def test_sort_href_new_column_starts_asc():
    q = SearchQuery(sort_by="pVal", sort_order="desc")
    href = main._sort_href("protein", q)
    assert "sort_by=protein" in href
    assert "sort_order=asc" in href


def test_regulator_href_regulators_search_query():
    q = SearchQuery(sort_by="pVal", sort_order="desc", page_size=50)
    href = main._regulator_href("YHR178W", q)
    assert href.startswith("?")
    assert "search_mode=regulators" in href
    assert "q=YHR178W" in href
    assert "page=1" in href


def test_target_href_targets_search_query():
    q = SearchQuery(sort_by="pVal", sort_order="desc", page_size=50)
    href = main._target_href("YHR183W", q)
    assert href.startswith("?")
    assert "search_mode=targets" in href
    assert "q=YHR183W" in href
    assert "page=1" in href


def test_regulator_href_blank_returns_empty():
    q = SearchQuery()
    assert main._regulator_href("", q) == ""
    assert main._regulator_href("   ", q) == ""
    assert main._regulator_href(None, q) == ""


def test_index_gene_columns_use_regulator_links(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)
    response = client.get("/")
    assert response.status_code == 200
    assert b"cell-link-reg" in response.content
    assert b"search_mode=regulators" in response.content
    assert b"cell-link-target" in response.content
    assert b"search_mode=targets" in response.content


def test_empty_numeric_query_values_do_not_422(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)

    response = client.get(
        "/api/results",
        params={
            "pval_min": "",
            "pval_max": "",
            "beta_min": "",
            "beta_max": "",
            "varexp_min": "",
            "varexp_max": "",
            "dist_min": "",
            "dist_max": "",
            "percentage_min": "",
            "percentage_max": "",
        },
    )
    assert response.status_code == 200
