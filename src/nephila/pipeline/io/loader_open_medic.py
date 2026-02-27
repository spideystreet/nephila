"""Load Open Medic CIP13 CSV into the PostgreSQL raw schema."""

from pathlib import Path

import pandas as pd
from dagster import get_dagster_logger
from sqlalchemy import Engine

# Expected columns in the Open Medic CIP13 CSV (CNAM format, semicolon-separated)
# Source: https://www.assurance-maladie.ameli.fr/content/descriptif-des-variables-de-la-serie-open-medic
OPEN_MEDIC_COLUMNS = [
    "ANR",        # Year
    "CIP13",      # CIP13 code (13 digits)
    "LIB_CIP",    # Drug label at CIP level
    "ATC1",       # ATC level 1 code
    "LIB_ATC1",   # ATC level 1 label
    "ATC2",       # ATC level 2 code
    "LIB_ATC2",   # ATC level 2 label
    "ATC3",       # ATC level 3 code
    "LIB_ATC3",   # ATC level 3 label
    "ATC4",       # ATC level 4 code
    "LIB_ATC4",   # ATC level 4 label
    "ATC5",       # ATC level 5 code
    "LIB_ATC5",   # ATC level 5 label
    "TOP_GEN",    # Generic flag (0=branded, 1=generic)
    "GEN_NUM",    # Generic group number
    "REM",        # Amount reimbursed (€)
    "BSE",        # Reimbursement base amount (€)
    "BOITES",     # Number of boxes dispensed
    "NBC",        # Number of beneficiaries
]


def load_open_medic_to_raw(csv_path: Path, engine: Engine) -> int:
    """
    Read Open Medic CIP13 CSV and load it into raw.open_medic.

    The file uses semicolons as separator and UTF-8 encoding.
    Columns are auto-detected from the header row; unknown columns are kept as-is.
    Returns the number of rows loaded.
    """
    log = get_dagster_logger()

    if not csv_path.exists():
        raise FileNotFoundError(f"Open Medic CSV not found: {csv_path}")

    # Detect separator from first line (handles gzip transparently via pandas)
    import gzip

    open_fn = gzip.open if str(csv_path).endswith(".gz") else open
    with open_fn(csv_path, "rt", encoding="utf-8", errors="replace") as f:
        first_line = f.readline()
    sep = ";" if first_line.count(";") > first_line.count(",") else ","

    df = pd.read_csv(
        csv_path,
        sep=sep,
        encoding="utf-8",
        compression="gzip" if str(csv_path).endswith(".gz") else "infer",
        dtype=str,
        keep_default_na=False,
        on_bad_lines="warn",
    )
    df = df.replace("", None)

    log.info(f"[raw] open_medic — columns detected: {list(df.columns)}")

    df.to_sql(
        "open_medic",
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )
    log.info(f"[raw] open_medic — {len(df):,} rows loaded")
    return len(df)
