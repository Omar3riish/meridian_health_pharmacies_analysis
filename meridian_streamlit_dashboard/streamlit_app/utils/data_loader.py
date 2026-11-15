from pathlib import Path
import os
import re

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


def _find_project_root():
    """Find the dashboard folder regardless of Streamlit's working directory."""
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        if (parent / "data" / "raw").is_dir() or (parent / "data" / "processed").is_dir():
            return parent
    # data_loader.py lives in streamlit_app/utils/ in this repository.
    return current_file.parents[2]


ROOT = _find_project_root()
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

DEFAULT_TABLES = {
    "sales": "fact_sales",
    "customers": "dim_customers",
    "products": "dim_products",
    "stores": "dim_stores",
    "inventory": "fact_stock_log",
    "employees": "dim_employees",
    "prescriptions": "fact_prescriptions",
    "categories": "dim_categories",
    "suppliers": "dim_suppliers",
}

# Processed dimensions are preferred; raw source files remain supported.
CSV_FILES = {
    "customers": ["dim_customers.csv", "customers_master.csv", "customers.csv"],
    "products": ["dim_products.csv", "products_catalog.csv", "products.csv"],
    "stores": ["dim_stores.csv", "stores.csv"],
    "inventory": ["fact_stock_log.csv", "stock_condition_log.csv"],
    "employees": ["dim_employees.csv", "employees.csv"],
    "prescriptions": ["fact_prescriptions.csv", "prescriptions_log.csv"],
    "categories": ["dim_categories.csv", "categories.csv"],
    "suppliers": ["dim_suppliers.csv", "suppliers.csv"],
}


def _get_secret(section, key, default=None):
    try:
        return st.secrets.get(section, {}).get(key, default)
    except Exception:
        return default


def _database_url():
    url = os.getenv("DATABASE_URL") or _get_secret("postgres", "url")
    if url:
        url = str(url)
        return url.replace("postgres://", "postgresql://", 1)

    host = os.getenv("PGHOST") or _get_secret("postgres", "host")
    if not host:
        return None

    user = os.getenv("PGUSER") or _get_secret("postgres", "user")
    password = os.getenv("PGPASSWORD") or _get_secret("postgres", "password")
    database = os.getenv("PGDATABASE") or _get_secret("postgres", "database")
    port = os.getenv("PGPORT") or _get_secret("postgres", "port", 5432)

    if not all([user, password, database]):
        return None

    from urllib.parse import quote_plus
    return (
        f"postgresql+psycopg://{quote_plus(str(user))}:"
        f"{quote_plus(str(password))}@{host}:{port}/{database}"
    )


def _read_csv_candidates(names):
    errors = []
    for base in (PROCESSED_DIR, RAW_DIR):
        for name in names:
            path = base / name
            if not path.is_file():
                continue
            try:
                frame = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
                if frame.empty:
                    errors.append(f"{path.relative_to(ROOT)} is empty")
                    continue
                return frame, f"{path.relative_to(ROOT)} ({len(frame):,} rows)"
            except Exception as exc:
                errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")

    if errors:
        return pd.DataFrame(), "CSV read problem: " + " | ".join(errors)
    return pd.DataFrame(), f"CSV not found. Checked: {', '.join(names)}"


def _read_csv_sales():
    consolidated, note = _read_csv_candidates(
        ["fact_sales.csv", "sales_cleaned.csv", "cleaned_sales.csv"]
    )
    if not consolidated.empty:
        return consolidated, note

    # Group 1 is day/month/year; groups 2 and 3 are month/day/year.
    sales_files = [
        ("sales_group1_storesA.csv", True),
        ("sales_group2_storesB.csv", False),
        ("sales_group3_storesC.csv", False),
        ("sales.csv", True),
    ]

    frames, found, errors = [], [], []
    for filename, dayfirst in sales_files:
        frame, source = _read_csv_candidates([filename])
        if frame.empty:
            if "not found" not in source.lower():
                errors.append(source)
            continue

        date_col = next(
            (c for c in frame.columns if str(c).strip().lower() in {"sale_date", "transaction_date", "order_date", "date"}),
            None,
        )
        if date_col:
            frame[date_col] = pd.to_datetime(
                frame[date_col], errors="coerce", dayfirst=dayfirst
            )

        frames.append(frame)
        found.append(source)

    if frames:
        combined = pd.concat(frames, ignore_index=True, sort=False)
        return combined, f"Combined {len(frames)} sales file(s): " + "; ".join(found)

    detail = " | ".join(errors) if errors else "No matching sales CSV files were found."
    return pd.DataFrame(), detail


def _safe_identifier(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(name)):
        raise ValueError(f"Unsafe SQL table identifier: {name}")
    return name


def _read_postgres_table(engine, table):
    table = _safe_identifier(table)
    return pd.read_sql(text(f'SELECT * FROM public."{table}"'), engine)


def _join_product_categories(products, categories):
    if products.empty or categories.empty:
        return products

    p = products.copy()
    c = categories.copy()
    p.columns = [str(col).strip().lower().replace(" ", "_") for col in p.columns]
    c.columns = [str(col).strip().lower().replace(" ", "_") for col in c.columns]

    if {"category_id", "category_name"}.issubset(c.columns) and "category_id" in p.columns:
        lookup = c[["category_id", "category_name"]].drop_duplicates("category_id")
        if "category_name" not in p.columns:
            p = p.merge(lookup, on="category_id", how="left", validate="many_to_one")
        if "category_name" in p.columns and "product_category" not in p.columns:
            p = p.rename(columns={"category_name": "product_category"})
    return p


def load_project_data(mode):
    datasets = {}
    notes = {}
    engine = None
    url = _database_url()

    if mode != "CSV only" and url:
        try:
            engine = create_engine(
                url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 8},
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            notes["postgres_connection"] = "Connected"
        except Exception as exc:
            notes["postgres_connection"] = (
                f"Connection failed: {type(exc).__name__}: {exc}"
            )
            if engine is not None:
                engine.dispose()
            engine = None
    elif mode != "CSV only":
        notes["postgres_connection"] = (
            "Not configured. CSV fallback is available in the recommended mode."
        )

    table_overrides = {}
    try:
        table_overrides = dict(st.secrets.get("postgres", {}).get("tables", {}))
    except Exception:
        pass
    table_map = {**DEFAULT_TABLES, **table_overrides}

    csv_map = {"sales": [], **CSV_FILES}
    keys = [
        "sales", "customers", "products", "stores", "inventory",
        "employees", "prescriptions", "categories", "suppliers",
    ]

    try:
        for key in keys:
            frame = pd.DataFrame()
            note = ""

            if engine is not None and mode != "CSV only":
                try:
                    frame = _read_postgres_table(engine, table_map[key])
                    note = (
                        f"PostgreSQL public.{table_map[key]} "
                        f"({len(frame):,} rows)"
                    )
                except Exception as exc:
                    note = (
                        f"PostgreSQL table unavailable "
                        f"({type(exc).__name__}: {exc})"
                    )

            # In the recommended mode, an empty/missing DB table also falls
            # back to CSV rather than blocking the dashboard.
            if frame.empty and mode != "PostgreSQL only":
                if key == "sales":
                    frame, csv_note = _read_csv_sales()
                else:
                    frame, csv_note = _read_csv_candidates(csv_map[key])
                note = (note + " | " if note else "") + csv_note

            datasets[key] = frame
            notes[key] = note or "No data loaded"

        datasets["products"] = _join_product_categories(
            datasets.get("products", pd.DataFrame()),
            datasets.get("categories", pd.DataFrame()),
        )
        notes["project_root"] = str(ROOT)
        notes["raw_data_directory"] = (
            f"{RAW_DIR} (exists: {RAW_DIR.is_dir()})"
        )
        notes["processed_data_directory"] = (
            f"{PROCESSED_DIR} (exists: {PROCESSED_DIR.is_dir()})"
        )
    finally:
        if engine is not None:
            engine.dispose()

    return datasets, notes
