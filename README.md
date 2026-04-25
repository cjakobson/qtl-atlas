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
2. Install dependencies (includes tests):
  - `pip install -r requirements-dev.txt`
3. Configure data path (optional if using the default absolute path):
  - `cp .env.example .env`
  - `export DATA_CSV_PATH="/path/to/science.adu3198_data_s4.csv"`

## Run

`uvicorn app.main:app --reload`

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Test

`pytest` (install with `pip install -r requirements-dev.txt` if needed)

## Docker

1. Place `science.adu3198_data_s4.csv` on the host (for example in `./data/`) and point compose at that folder:
  - Create `./data` and copy the file as `data/science.adu3198_data_s4.csv`, or set `DATA_DIR` to a directory that contains the file.
2. Build and run:
  - `docker compose up --build`
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

**Health check:** `GET /health` returns `{"status":"ok"}` (used by the compose `healthcheck`).

**Build image only:** `docker build -t qtl-atlas .`

**Run with custom CSV path in container:** set `DATA_CSV_PATH` and mount the file, for example:
`docker run --rm -e DATA_CSV_PATH=/data/my.csv -v /path/on/host/file.csv:/data/my.csv:ro -p 8000:8000 qtl-atlas`

### Render Disk seeding (optional)

If your Render disk path (`DATA_CSV_PATH`) is empty at startup, you can seed it automatically:

- `DATA_CSV_PATH=/var/data/science.adu3198_data_s4.csv`
- `DATA_CSV_SOURCE_PATH=/opt/render/project/src/data/science.adu3198_data_s4.csv` (or any readable in-container source path)

On first startup, the app will copy `DATA_CSV_SOURCE_PATH` to `DATA_CSV_PATH` if the target file is missing.

## Endpoints

- `GET /health` - liveness (for load balancers / Docker)
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

