import os
from functools import lru_cache
from pathlib import Path

import pandas as pd


DEFAULT_DATA_PATH = (
    "/Users/christopherjakobson/Dropbox/JaroszLab/qtl-server-data/"
    "science.adu3198_data_s1_to_s6/science.adu3198_data_s4.csv"
)

NUMERIC_COLUMNS = [
    "pVal",
    "beta",
    "varExp",
    "dist",
    "percentage",
    "orfStart",
    "orfEnd",
    "pos",
]


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].replace({"": pd.NA, "Inf": pd.NA, "-Inf": pd.NA})

    for column in NUMERIC_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


def get_data_path() -> Path:
    return Path(os.getenv("DATA_CSV_PATH", DEFAULT_DATA_PATH))


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    data_path = get_data_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    dataframe = pd.read_csv(data_path)
    return _normalize_dataframe(dataframe)
