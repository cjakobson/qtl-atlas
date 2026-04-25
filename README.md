# qtl-atlas

Simple FastAPI web server for searching and exporting scientific paper results from:

`science.adu3198_data_s4.csv`

## Features

- Single keyword field with mode `search_mode`: **targets** (`protein`, `commonName`) or **regulators** (`gene1`, `gene2`, `common1`, `common2`). In **regulators** mode the UI shows a **volcano plot** (pVal vs β) for every row in the filtered result set (not only the current page), beside the table.
- The web UI shows keyword, search mode, and **rows per page**; click any **column header** to sort (click again to flip ascending / descending). **Page number and extra filters** are still available via query parameters or `/api/results` / `/export.csv`
- Sortable results and pagination
- CSV export of the currently filtered/sorted dataset
- JSON endpoint for programmatic access

## Setup

1. Create and activate a virtual environment:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
2. Install dependencies:
  - `pip install -r requirements.txt`
3. Configure data path (optional if using the default absolute path):
  - `cp .env.example .env`
  - `export DATA_CSV_PATH="/path/to/science.adu3198_data_s4.csv"`

## Run

`uvicorn app.main:app --reload`

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Test

`pytest`

## Endpoints

- `GET /` - HTML search UI
- `GET /api/results` - JSON response using same query params
- `GET /export.csv` - CSV download using same query params

## Example query params

- `q=GND1&search_mode=targets`
- `q=YHR178W&search_mode=regulators`
- `chr=8`
- `variant_type=missense_variant`
- `pval_min=10&pval_max=20`
- `sort_by=pVal&sort_order=desc&page=1&page_size=50`