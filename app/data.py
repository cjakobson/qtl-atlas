import os
import shutil
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


def _candidate_seed_sources() -> list[Path]:
    """
    Ordered fallback locations for a seed CSV that may ship with the repo/image.
    """
    candidates: list[Path] = []

    env_source = os.getenv("DATA_CSV_SOURCE_PATH", "").strip()
    if env_source:
        candidates.append(Path(env_source))

    # Typical Render build/runtime checkout paths, plus local project paths.
    candidates.extend(
        [
            Path("/opt/render/project/src/data/science.adu3198_data_s4.csv"),
            Path("/opt/render/project/src/science.adu3198_data_s4.csv"),
            Path.cwd() / "data" / "science.adu3198_data_s4.csv",
            Path.cwd() / "science.adu3198_data_s4.csv",
        ]
    )

    # De-duplicate while preserving order.
    deduped: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if key not in seen:
            deduped.append(p)
            seen.add(key)
    return deduped


def _maybe_copy_seed_csv(data_path: Path) -> None:
    """
    Optionally seed the runtime CSV path by copying from a source file.

    Useful on Render: if DATA_CSV_PATH points at a mounted disk and the file
    is absent, set DATA_CSV_SOURCE_PATH to a readable source file path.
    """
    if data_path.exists():
        return

    source_path = next((p for p in _candidate_seed_sources() if p.exists()), None)
    if source_path is None:
        return

    data_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, data_path)


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    data_path = get_data_path()
    _maybe_copy_seed_csv(data_path)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {data_path}. "
            "Set DATA_CSV_PATH to an existing file, or provide a seed CSV via "
            "DATA_CSV_SOURCE_PATH. If a repo file exists at "
            "`data/science.adu3198_data_s4.csv`, startup will auto-copy it into "
            "DATA_CSV_PATH."
        )

    dataframe = pd.read_csv(data_path)
    return _normalize_dataframe(dataframe)
