import pandas as pd
from fastapi.testclient import TestClient

import app.main as main


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


def test_api_results_returns_filtered_rows(monkeypatch):
    monkeypatch.setattr(main, "load_dataframe", lambda: _sample_df())
    client = TestClient(main.app)

    response = client.get("/api/results", params={"q": "GND1", "chr": "8"})
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
