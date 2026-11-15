from pathlib import Path
import os
import re
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Edit these table names to match your PostgreSQL database.
DEFAULT_TABLES = {
    "sales": "fact_sales",
    "customers": "dim_customers",
    "products": "dim_products",
    "stores": "dim_stores",
    "inventory": "stock_condition_log",
    "employees": "dim_employees",
    "prescriptions": "prescriptions_log",
    "categories": "categories",
    "suppliers": "suppliers",
}

CSV_FILES = {
    "customers": ["customers_master.csv", "customers.csv"],
    "products": ["products_catalog.csv", "products.csv"],
    "stores": ["stores.csv"],
    "inventory": ["stock_condition_log.csv"],
    "employees": ["employees.csv"],
    "prescriptions": ["prescriptions_log.csv"],
    "categories": ["categories.csv"],
    "suppliers": ["suppliers.csv"],
}

def _get_secret(section, key, default=None):
    try:
        return st.secrets.get(section, {}).get(key, default)
    except Exception:
        return default

def _database_url():
    url = os.getenv("DATABASE_URL") or _get_secret("postgres", "url")
    if url:
        # Streamlit/Render providers may supply postgres://; SQLAlchemy expects postgresql://
        return url.replace("postgres://", "postgresql://", 1)
    host = os.getenv("PGHOST") or _get_secret("postgres", "host")
    if not host:
        return None
    user = os.getenv("PGUSER") or _get_secret("postgres", "user")
    password = os.getenv("PGPASSWORD") or _get_secret("postgres", "password")
    db = os.getenv("PGDATABASE") or _get_secret("postgres", "database")
    port = os.getenv("PGPORT") or _get_secret("postgres", "port", 5432)
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

def _read_csv_candidates(names):
    for base in (PROCESSED_DIR, RAW_DIR):
        for name in names:
            path = base / name
            if path.exists():
                try:
                    return pd.read_csv(path, low_memory=False), str(path.relative_to(ROOT))
                except Exception as exc:
                    return pd.DataFrame(), f"CSV read failed ({path.name}): {exc}"
    return pd.DataFrame(), "CSV not found"

def _read_csv_sales():
    # Prefer a consolidated cleaned file if one exists.
    consolidated, note = _read_csv_candidates(["fact_sales.csv", "sales_cleaned.csv", "cleaned_sales.csv"])
    if not consolidated.empty:
        return consolidated, note

    frames, found = [], []
    for filename in [
        "sales_group1_storesA.csv",
        "sales_group2_storesB.csv",
        "sales_group3_storesC.csv",
        "sales.csv",
    ]:
        frame, source = _read_csv_candidates([filename])
        if not frame.empty:
            frames.append(frame)
            found.append(source)
    if frames:
        return pd.concat(frames, ignore_index=True, sort=False), "Combined: " + ", ".join(found)
    return pd.DataFrame(), "No sales CSV found"

def _safe_identifier(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)):
        raise ValueError(f"Unsafe SQL table identifier: {name}")
    return name

def _read_postgres_table(engine, table):
    table = _safe_identifier(table)
    # Table name is validated as a simple identifier; schema is public by default.
    return pd.read_sql(text(f'SELECT * FROM public."{table}"'), engine)

def load_project_data(mode):
    datasets, notes = {}, {}
    url = _database_url()
    engine = None
    if mode != "CSV only" and url:
        try:
            engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 8})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            notes["postgres_connection"] = "Connected"
        except Exception as exc:
            notes["postgres_connection"] = f"Connection failed: {exc.__class__.__name__}: {exc}"
            engine = None
    elif mode != "CSV only":
        notes["postgres_connection"] = "Not configured; add credentials to .streamlit/secrets.toml or environment variables."

    table_overrides = {}
    try:
        table_overrides = dict(st.secrets.get("postgres", {}).get("tables", {}))
    except Exception:
        pass
    table_map = {**DEFAULT_TABLES, **table_overrides}

    csv_map = {
        "sales": [],
        **CSV_FILES,
    }

    for key in ["sales", "customers", "products", "stores", "inventory", "employees", "prescriptions", "categories", "suppliers"]:
        frame = pd.DataFrame()
        note = ""
        if engine is not None and mode != "CSV only":
            try:
                frame = _read_postgres_table(engine, table_map[key])
                note = f'PostgreSQL: public.{table_map[key]} ({len(frame):,} rows)'
            except Exception as exc:
                note = f'PostgreSQL table unavailable ({exc.__class__.__name__})'
        if frame.empty and mode != "PostgreSQL only":
            if key == "sales":
                frame, csv_note = _read_csv_sales()
            else:
                frame, csv_note = _read_csv_candidates(csv_map[key])
            note = (note + " | " if note else "") + csv_note
        datasets[key] = frame
        notes[key] = note or "No data loaded"

    if engine is not None:
        engine.dispose()
    return datasets, notes
