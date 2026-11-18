from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Optional PostgreSQL support. The app remains fully usable without it.
try:
    from sqlalchemy import create_engine, text
except Exception:
    create_engine = None
    text = None




from pathlib import Path


# ---------------------------------------------------------------------
# CSV Data Loader
# ---------------------------------------------------------------------

TABLES = [
    "fact_sales",
    "fact_stock_log",
    "fact_prescriptions",
    "dim_products",
    "dim_stores",
    "dim_customers",
    "dim_categories",
    "dim_employees",
    "dim_suppliers",
]


def find_csv_file(filename: str) -> Path | None:
    """
    Search common project locations for a CSV file.

    Optional:
    Set MERIDIAN_DATA_DIR to the folder containing your CSV files.
    """

    app_dir = Path(__file__).resolve().parent
    project_dir = app_dir.parent
    working_dir = Path.cwd()

    search_dirs = []

    # Optional custom data folder from environment variable
    custom_dir = os.getenv("MERIDIAN_DATA_DIR", "").strip()
    if custom_dir:
        search_dirs.append(Path(custom_dir).expanduser())

    # Common locations
    search_dirs.extend([
        app_dir,
        app_dir / "data",
        project_dir,
        project_dir / "data",
        working_dir,
        working_dir / "data",
    ])

    # Remove duplicate directories
    unique_dirs = []
    seen = set()

    for folder in search_dirs:
        folder = folder.resolve()

        if folder not in seen:
            seen.add(folder)
            unique_dirs.append(folder)

    # Search the expected locations first
    for folder in unique_dirs:
        candidate = folder / filename

        if candidate.is_file():
            return candidate

    # As a fallback, search inside the app and project directories
    for root in [app_dir, project_dir]:
        if root.exists():
            for candidate in root.rglob(filename):
                if candidate.is_file():
                    return candidate

    return None


@st.cache_data(show_spinner="Loading Meridian data from CSV files...")
def load_csv_data() -> Dict[str, pd.DataFrame]:

    frames = {}
    missing_files = []

    for table in TABLES:
        filename = f"{table}.csv"
        file_path = find_csv_file(filename)

        if file_path is None:
            missing_files.append(filename)
            continue

        try:
            frames[table] = pd.read_csv(file_path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not read {filename} from {file_path}: {exc}"
            ) from exc

    if missing_files:
        missing_list = "\n".join(
            f"- {filename}" for filename in missing_files
        )

        raise FileNotFoundError(
            "The following required CSV files could not be found:\n"
            f"{missing_list}\n\n"
            "Expected locations include the app folder, project folder, "
            "or their data folders.\n"
            "Check that the files are uploaded to your GitHub repository "
            "and that their names match exactly."
        )

    return frames

# ---------------------------------------------------------------------
# Configuration and Digitera design system
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Meridian Health | Executive BI Suite",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

INDIGO = "#1B199E"
AMBER = "#F59E0B"
PALETTE = [INDIGO, AMBER, "#3B82F6", "#10B981", "#6366F1", "#F97316"]
BG = "#F4F5F7"
MUTED = "#64748B"
INK = "#1E293B"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
:root { --digitera-indigo:#1B199E; --digitera-amber:#F59E0B; }
html, body, [class*="css"] { font-family:'Inter',sans-serif; color:#1E293B; }
.stApp { background:#F4F5F7; }
[data-testid="stHeader"] { background:rgba(244,245,247,.92); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #E8EAF0; }
[data-testid="stSidebar"] * { color:#1E293B; }
.block-container { padding-top:1.25rem; padding-bottom:2.5rem; max-width:1600px; }
.brand-banner {
  background:#fff; border-radius:16px; padding:18px 24px; margin-bottom:22px;
  box-shadow:0 4px 12px rgba(27,25,158,.06); border-left:4px solid #1B199E;
  display:flex; align-items:center; justify-content:space-between; gap:16px;
}
.brand-name { color:#1B199E; font-family:'Plus Jakarta Sans',sans-serif; font-weight:800;
  font-size:20px; letter-spacing:-.5px; }
.brand-spark { color:#F59E0B; font-size:30px; margin-right:10px; vertical-align:-2px; }
.brand-sub { color:#64748B; font-size:11px; margin-top:4px; letter-spacing:.3px; }
.page-eyebrow { color:#F59E0B; font-size:11px; font-weight:800; letter-spacing:1.7px; text-transform:uppercase; }
.page-title { color:#1B199E; font-family:'Plus Jakarta Sans',sans-serif; font-weight:800;
  font-size:29px; letter-spacing:-.8px; margin:2px 0 4px 0; }
.page-desc { color:#64748B; font-size:13px; margin-bottom:20px; }
.kpi-card {
  background:#fff; border-radius:12px; padding:17px 18px 15px 18px;
  box-shadow:0 4px 12px rgba(27,25,158,.06); border-top:4px solid #1B199E;
  min-height:122px;
}
.kpi-card.amber { border-top-color:#F59E0B; }
.kpi-label { color:#64748B; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.7px; }
.kpi-value { color:#1B199E; font-family:'Plus Jakarta Sans',sans-serif; font-size:25px; font-weight:800; margin-top:8px; }
.kpi-delta { color:#64748B; font-size:11px; margin-top:5px; }
.section-head { color:#1B199E; font-family:'Plus Jakarta Sans',sans-serif; font-size:16px; font-weight:800; margin:14px 0 8px; }
.panel { background:#fff; border-radius:12px; padding:16px 18px; box-shadow:0 4px 12px rgba(27,25,158,.06); }
.status-pill { display:inline-block; padding:5px 10px; border-radius:20px; background:#ECFDF5; color:#047857;
  font-size:10px; font-weight:800; letter-spacing:.4px; }
div[data-testid="stMetric"] { background:#fff; border-radius:12px; padding:14px; box-shadow:0 4px 12px rgba(27,25,158,.06); border-top:3px solid #1B199E; }
div[data-testid="stMetric"] label { color:#64748B !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#1B199E; font-weight:800; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { background:#fff; border-radius:8px 8px 0 0; }
.stButton>button, .stDownloadButton>button { border-radius:8px; border:1px solid #1B199E; color:#1B199E; font-weight:700; }
.stButton>button:hover { background:#1B199E; color:#fff; }
small, .muted { color:#64748B; }
hr { border-color:#E8EAF0; }
</style>
""", unsafe_allow_html=True)

def brand_header():
    st.markdown("""
    <div class="brand-banner">
      <div><span class="brand-spark">✦</span><span class="brand-name">Meridian Health | Executive BI Suite</span>
      <div class="brand-sub">Powered by JMDR Digital Solutions · Business Intelligence &amp; Web Solutions</div></div>
      <div style="text-align:right"><span class="status-pill">● ANALYTICS ONLINE</span><div class="brand-sub">DIGITERA DESIGN SYSTEM</div></div>
    </div>""", unsafe_allow_html=True)

def page_heading(section: str, title: str, desc: str):
    st.markdown(f'<div class="page-eyebrow">{section}</div><div class="page-title">{title}</div><div class="page-desc">{desc}</div>', unsafe_allow_html=True)

def money(v):
    return f"${v:,.0f}" if pd.notna(v) else "—"

def pct(v):
    return f"{v:,.1f}%" if pd.notna(v) else "—"

def kpi(label, value, delta=None, accent=False):
    d = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    cls = "kpi-card amber" if accent else "kpi-card"
    st.markdown(f'<div class="{cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{d}</div>', unsafe_allow_html=True)

def chart_theme(fig, height=None):
    # Preserve chart-specific height/margins unless a caller explicitly overrides height.
    layout = dict(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=INK, size=11),
        colorway=PALETTE, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="#fff", font_color=INK),
    )
    if height is not None:
        layout["height"] = height
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#E9ECF2", zeroline=False)
    return fig

def show_chart(fig, key=None, height=None):
    st.plotly_chart(chart_theme(fig, height=height), use_container_width=True, config={"displaylogo": False}, key=key)

# ---------------------------------------------------------------------
# Synthetic star-schema generator and database loader
# ---------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def synthetic_data(seed: int = 42) -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n_stores, n_products, n_customers, n_employees = 12, 55, 950, 72
    regions = ["North", "South", "East", "West", "Central"]
    cities = {
        "North": ["Alexandria", "Tanta"], "South": ["Aswan", "Luxor"],
        "East": ["Ismailia", "Suez"], "West": ["Giza", "6th of October"],
        "Central": ["Cairo", "New Cairo"],
    }
    stores = []
    for i in range(n_stores):
        region = regions[i % len(regions)]
        stores.append([i+1, f"Meridian {cities[region][i % 2]} {i+1:02d}",
                       cities[region][i % 2], region])
    dim_stores = pd.DataFrame(stores, columns=["store_id","store_name","city","region"])

    cats = ["Prescription", "OTC", "Vitamins", "Personal Care", "Medical Devices", "Baby Care"]
    dim_categories = pd.DataFrame({"category_id": range(1, len(cats)+1), "category_name": cats})
    dim_suppliers = pd.DataFrame({
        "supplier_id": range(1, 16),
        "supplier_name": [f"Meridian Supplier {i:02d}" for i in range(1, 16)],
    })
    products = []
    for i in range(n_products):
        cat = int(rng.integers(1, len(cats)+1))
        price = float(rng.uniform(45, 950))
        products.append([i+1, f"{cats[cat-1]} Product {i+1:02d}", cat,
                         int(rng.integers(1, 16)), round(price,2), round(price*rng.uniform(.48,.78),2)])
    dim_products = pd.DataFrame(products, columns=["product_id","product_name","category_id","supplier_id","unit_price","cost_price"])
    dim_customers = pd.DataFrame({
        "customer_id": range(1,n_customers+1),
        "full_name": [f"Customer {i:04d}" for i in range(1,n_customers+1)],
        "customer_segment": rng.choice(["Platinum","Gold","Silver","Others"], n_customers, p=[.08,.2,.37,.35])
    })
    employees = []
    for i in range(n_employees):
        sid = int(rng.integers(1,n_stores+1))
        pharmacist = bool(rng.random() < .38)
        employees.append([i+1,sid,f"Team Member {i+1:03d}",pharmacist,round(float(rng.uniform(6500,18000)),2)])
    dim_employees = pd.DataFrame(employees, columns=["employee_id","store_id","employee_name","is_pharmacist","salary"])

    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=730)
    dates = pd.date_range(start, periods=731, freq="D")
    n_sales = 14500
    sale_dates = rng.choice(dates, n_sales)
    sale_ids = np.arange(1,n_sales+1)
    product_ids = rng.integers(1,n_products+1,n_sales)
    sales = pd.DataFrame({
        "sale_id": sale_ids, "sale_date": pd.to_datetime(sale_dates),
        "store_id": rng.integers(1,n_stores+1,n_sales),
        "customer_id": rng.integers(1,n_customers+1,n_sales),
        "employee_id": rng.integers(1,n_employees+1,n_sales),
        "product_id": product_ids, "quantity": rng.integers(1,6,n_sales),
        "discount_pct": np.round(rng.choice([0,.03,.05,.08,.10,.15,.20],n_sales,p=[.3,.12,.18,.15,.12,.09,.04]),3),
        "payment_method": rng.choice(["Cash","Credit Card","Insurance","Digital Wallet"],n_sales,p=[.35,.3,.2,.15])
    })
    sales = sales.merge(dim_products[["product_id","unit_price"]],on="product_id",how="left")
    sales["unit_price"] = sales["unit_price"] * rng.uniform(.96,1.04,n_sales)
    sales["unit_price"] = sales["unit_price"].round(2)

    n_stock = 1150
    stock_dates = rng.choice(dates,n_stock)
    stock = pd.DataFrame({
        "stock_id":range(1,n_stock+1),
        "batch_number":[f"BATCH-{i:05d}" for i in range(1,n_stock+1)],
        "product_id":rng.integers(1,n_products+1,n_stock),
        "store_id":rng.integers(1,n_stores+1,n_stock),
        "quantity":rng.integers(0,160,n_stock),
        "reorder_level":rng.integers(20,65,n_stock),
        "expiry_date":pd.to_datetime(stock_dates)+pd.to_timedelta(rng.integers(-30,900,n_stock),unit="D"),
        "last_restocked":pd.to_datetime(stock_dates),
        "shelf_life_status":rng.choice(["Safe","Short Shelf Life","High Risk - Monitor","Critical Danger","Expired on Receipt"],n_stock,p=[.72,.12,.08,.05,.03]),
        "condition_notes":""
    })
    stock["is_below_reorder_level"] = stock["quantity"] < stock["reorder_level"]
    stock.loc[stock["is_below_reorder_level"],"condition_notes"] = "Below reorder level — replenishment required"

    n_rx = 3600
    prescriptions = pd.DataFrame({
        "prescription_id":range(1,n_rx+1),
        "issue_date":pd.to_datetime(rng.choice(dates,n_rx)),
        "customer_id":rng.integers(1,n_customers+1,n_rx),
        "product_id":rng.integers(1,n_products+1,n_rx),
        "store_id":rng.integers(1,n_stores+1,n_rx),
        "dosage":rng.choice(["Once daily","Twice daily","As directed","Every 8 hours"],n_rx),
        "doctor_name":rng.choice(["Dr. Ahmed","Dr. Sara","Dr. Omar","Dr. Mariam","Dr. Youssef"],n_rx)
    })
    return {
        "fact_sales":sales, "fact_stock_log":stock, "fact_prescriptions":prescriptions,
        "dim_products":dim_products, "dim_stores":dim_stores, "dim_customers":dim_customers,
        "dim_categories":dim_categories, "dim_employees":dim_employees,
        "dim_suppliers":dim_suppliers,
    }

# All nine project tables are loaded. dim_suppliers is part of the data model
# even though the current dashboard pages do not yet display supplier KPIs.
TABLES = [
    "fact_sales", "fact_stock_log", "fact_prescriptions", "dim_products",
    "dim_stores", "dim_customers", "dim_categories", "dim_employees",
    "dim_suppliers",
]
OPTIONAL_TABLES = []


def find_csv_file(filename: str) -> Optional[Path]:
    """Find a CSV reliably on Streamlit Cloud and local Windows/Linux runs.

    Search order:
      1. MERIDIAN_DATA_DIR environment variable, if configured
      2. app directory and app/data
      3. repository/project directory and project/data
      4. current working directory and current working directory/data
      5. recursive search under the app and project directories
    """
    app_dir = Path(__file__).resolve().parent
    project_dir = app_dir.parent
    working_dir = Path.cwd()

    search_dirs = []
    custom_dir = os.getenv("MERIDIAN_DATA_DIR", "").strip()
    if custom_dir:
        search_dirs.append(Path(custom_dir).expanduser())

    search_dirs.extend([
        app_dir,
        app_dir / "data",
        project_dir,
        project_dir / "data",
        working_dir,
        working_dir / "data",
    ])

    unique_dirs = []
    seen = set()
    for folder in search_dirs:
        try:
            resolved = folder.resolve()
        except OSError:
            continue
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(resolved)

    for folder in unique_dirs:
        candidate = folder / filename
        if candidate.is_file():
            return candidate

    # Covers common repository layouts such as /data/raw/filename.csv.
    for root in (app_dir, project_dir):
        if root.exists():
            try:
                for candidate in root.rglob(filename):
                    if candidate.is_file():
                        return candidate
            except (OSError, PermissionError):
                pass

    return None


@st.cache_data(ttl=300, show_spinner="Loading Meridian CSV files...")
def load_csv_data() -> Dict[str, pd.DataFrame]:
    """Load dashboard tables from CSV files using paths relative to this app."""
    frames: Dict[str, pd.DataFrame] = {}
    missing_files = []

    for table in TABLES + OPTIONAL_TABLES:
        filename = f"{table}.csv"
        file_path = find_csv_file(filename)

        if file_path is None:
            if table in TABLES:
                missing_files.append(filename)
            continue

        try:
            frames[table] = pd.read_csv(file_path, encoding="utf-8-sig")
        except Exception as exc:
            raise RuntimeError(
                f"Could not read {filename} from {file_path}: {exc}"
            ) from exc

    if missing_files:
        missing_list = "\n".join(f"• {name}" for name in missing_files)
        app_dir = Path(__file__).resolve().parent
        raise FileNotFoundError(
            "The dashboard could not find these required CSV files:\n\n"
            f"{missing_list}\n\n"
            "Place the files in the app folder or in an app/data folder. "
            "They must also be committed and pushed to GitHub for Streamlit Cloud.\n\n"
            f"App directory: {app_dir}\n"
            f"Current working directory: {Path.cwd()}\n\n"
            "If your files are stored elsewhere, set the MERIDIAN_DATA_DIR "
            "environment variable to that folder. File names are case-sensitive "
            "on Streamlit Cloud."
        )

    return frames


@st.cache_data(ttl=300, show_spinner="Loading Meridian data...")
def load_database(database_url: str):
    if create_engine is None:
        raise RuntimeError("SQLAlchemy is not installed.")
    engine = create_engine(database_url, pool_pre_ping=True)
    frames = {}
    with engine.connect() as conn:
        for table in TABLES:
            frames[table] = pd.read_sql(text(f'SELECT * FROM "{table}"'), conn)
    return frames

def normalize_data(frames):
    required = set(TABLES)
    missing = required - set(frames)
    if missing:
        raise ValueError(f"Missing tables: {', '.join(sorted(missing))}")
    d = {k:v.copy() for k,v in frames.items()}
    for col in ["sale_date"]:
        d["fact_sales"][col] = pd.to_datetime(d["fact_sales"][col], errors="coerce")
    d["fact_stock_log"]["expiry_date"] = pd.to_datetime(d["fact_stock_log"]["expiry_date"], errors="coerce")
    d["fact_stock_log"]["last_restocked"] = pd.to_datetime(d["fact_stock_log"]["last_restocked"], errors="coerce")
    d["fact_prescriptions"]["issue_date"] = pd.to_datetime(d["fact_prescriptions"]["issue_date"], errors="coerce")
    if "is_below_reorder_level" not in d["fact_stock_log"].columns:
        if {"quantity", "reorder_level"}.issubset(d["fact_stock_log"].columns):
            d["fact_stock_log"]["is_below_reorder_level"] = (
                pd.to_numeric(d["fact_stock_log"]["quantity"], errors="coerce").fillna(0)
                < pd.to_numeric(d["fact_stock_log"]["reorder_level"], errors="coerce").fillna(0)
            )
        else:
            d["fact_stock_log"]["is_below_reorder_level"] = False
    # Standardize null discounts and numeric measures.
    d["fact_sales"]["discount_pct"] = pd.to_numeric(d["fact_sales"]["discount_pct"], errors="coerce").fillna(0)
    for c in ["quantity","unit_price"]:
        d["fact_sales"][c] = pd.to_numeric(d["fact_sales"][c], errors="coerce").fillna(0)
    return d

def enrich(frames):
    d = normalize_data(frames)
    sales = d["fact_sales"].merge(d["dim_products"][["product_id","product_name","category_id","unit_price","cost_price"]].rename(columns={"unit_price":"product_list_price"}), on="product_id", how="left")
    sales = sales.merge(d["dim_stores"][["store_id","store_name","city","region"]],on="store_id",how="left")
    sales = sales.merge(d["dim_customers"][["customer_id","customer_segment"]],on="customer_id",how="left")
    sales = sales.merge(d["dim_categories"],on="category_id",how="left")
    sales["gross_revenue"] = sales["quantity"] * sales["unit_price"]
    sales["net_revenue"] = sales["gross_revenue"] * (1-sales["discount_pct"].fillna(0))
    sales["total_cost"] = sales["quantity"] * sales["cost_price"].fillna(0)
    sales["net_profit"] = sales["net_revenue"] - sales["total_cost"]
    sales["discount_value"] = sales["gross_revenue"] * sales["discount_pct"].fillna(0)
    sales["month"] = sales["sale_date"].dt.to_period("M").dt.to_timestamp()
    sales["day"] = sales["sale_date"].dt.floor("D")
    return d, sales

# ---------------------------------------------------------------------
# Load data and global controls
# ---------------------------------------------------------------------
brand_header()
database_url = os.getenv("DATABASE_URL", "").strip()
use_synthetic = os.getenv("USE_SYNTHETIC_DATA", "").strip().lower() in {"1", "true", "yes"}

if use_synthetic:
    raw = synthetic_data()
    source_label = "SYNTHETIC DEMO DATA"
elif database_url:
    try:
        raw = load_database(database_url)
        source_label = "POSTGRESQL · LIVE"
    except Exception as db_exc:
        # If PostgreSQL is temporarily unavailable, try the repository CSVs.
        try:
            raw = load_csv_data()
            source_label = "CSV DATA · DATABASE FALLBACK"
            st.sidebar.warning(f"Database connection failed; loaded CSV data instead. Details: {db_exc}")
        except Exception as csv_exc:
            st.error("Unable to load Meridian data from PostgreSQL or CSV files.")
            st.exception(db_exc)
            st.exception(csv_exc)
            st.stop()
else:
    try:
        raw = load_csv_data()
        source_label = "CSV DATA · REPOSITORY"
    except Exception as csv_exc:
        st.error("Meridian CSV data could not be loaded.")
        st.exception(csv_exc)
        st.info(
            "Expected layout: place the required CSV files in the same folder as "
            "app.py or inside a folder named data. Alternatively, configure "
            "MERIDIAN_DATA_DIR in Streamlit Secrets."
        )
        st.stop()

raw, sales_all = enrich(raw)
st.sidebar.markdown("## ✦ Meridian Controls")
st.sidebar.markdown(f'<span class="status-pill">{source_label}</span>', unsafe_allow_html=True)
min_date = sales_all["sale_date"].min().date()
max_date = sales_all["sale_date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date,max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range)==2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date
regions_available = ["All"] + sorted(sales_all["region"].dropna().unique().tolist())
region_filter = st.sidebar.selectbox("Region", regions_available)
store_options = ["All"] + sorted(sales_all.loc[sales_all["region"].eq(region_filter) if region_filter!="All" else slice(None),"store_name"].dropna().unique().tolist())
store_filter = st.sidebar.selectbox("Store", store_options)
category_options = ["All"] + sorted(sales_all["category_name"].dropna().unique().tolist())
category_filter = st.sidebar.selectbox("Product category", category_options)

sales = sales_all[sales_all["sale_date"].dt.date.between(start_date,end_date)].copy()
if region_filter!="All": sales = sales[sales["region"]==region_filter]
if store_filter!="All": sales = sales[sales["store_name"]==store_filter]
if category_filter!="All": sales = sales[sales["category_name"]==category_filter]
if sales.empty:
    st.warning("No sales match the selected filters. Widen the date range or clear a filter.")
    st.stop()

# Common metrics and customer-level data
gross = sales["gross_revenue"].sum()
net = sales["net_revenue"].sum()
cost = sales["total_cost"].sum()
profit = net-cost
margin = profit/net*100 if net else 0
orders = sales["sale_id"].nunique()
period_days = max((end_date-start_date).days+1,1)
prev_start = pd.Timestamp(start_date)-pd.Timedelta(days=period_days)
prev_end = pd.Timestamp(start_date)-pd.Timedelta(days=1)
prev = sales_all[sales_all["sale_date"].dt.date.between(prev_start.date(),prev_end.date())]
prev_net = prev["net_revenue"].sum()
delta_net = (net-prev_net)/prev_net*100 if prev_net else np.nan
rx = raw["fact_prescriptions"].copy()
rx = rx.merge(raw["dim_stores"][["store_id","store_name","region"]],on="store_id",how="left")
rx = rx.merge(raw["dim_products"][["product_id","category_id"]],on="product_id",how="left")
rx = rx.merge(raw["dim_categories"],on="category_id",how="left")
rx_filtered = rx[rx["issue_date"].dt.date.between(start_date,end_date)].copy()
if region_filter != "All":
    rx_filtered = rx_filtered[rx_filtered["region"] == region_filter]
if store_filter != "All":
    rx_filtered = rx_filtered[rx_filtered["store_name"] == store_filter]
if category_filter != "All":
    rx_filtered = rx_filtered[rx_filtered["category_name"] == category_filter]

# ---------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------
pages = ["Executive Overview","Sales Analysis","Customer Analysis",
         "Product & Inventory Analysis","Store & Geographic Analysis","Customer Behavior Analysis"]
page = st.sidebar.radio("WORKSPACE",pages,index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Data model: Star Schema")
st.sidebar.caption("Financial basis: net of discounts · product cost")
st.sidebar.caption("Demo mode uses reproducible synthetic data.")

# ---------------------------------------------------------------------
# Page 1 — Executive Overview
# ---------------------------------------------------------------------
if page == "Executive Overview":
    page_heading("Executive dashboard","Executive Overview","A decision-ready view of revenue, profitability, store performance and prescription operations.")
    cols=st.columns(4)
    with cols[0]: kpi("Total Net Revenue",money(net),f"{delta_net:+.1f}% vs previous period" if pd.notna(delta_net) else "No prior-period baseline")
    with cols[1]: kpi("Total Net Profit",money(profit),f"Margin {margin:.1f}%",True)
    with cols[2]: kpi("Profit Margin",pct(margin),"Net profit ÷ net revenue")
    with cols[3]: kpi("Total Orders",f"{orders:,}",f"{sales['customer_id'].nunique():,} unique customers",True)

    monthly=sales.groupby("month",as_index=False).agg(
        net_revenue=("net_revenue","sum"), total_cost=("total_cost","sum"),
        net_profit=("net_profit","sum"), gross_revenue=("gross_revenue","sum")
    )
    monthly["margin_pct"]=np.where(monthly["net_revenue"]!=0,monthly["net_profit"]/monthly["net_revenue"]*100,0)
    monthly["revenue_label"]=monthly["net_revenue"].map(money)
    monthly["profit_label"]=[f"{money(p)}\n{m:.1f}%" for p,m in zip(monthly["net_profit"],monthly["margin_pct"])]
    fig=go.Figure()
    fig.add_bar(x=monthly["month"],y=monthly["total_cost"],name="Total Cost",
                marker_color=INDIGO,hovertemplate="%{x|%b %Y}<br>Total Cost: $%{y:,.0f}<extra></extra>")
    fig.add_bar(x=monthly["month"],y=monthly["net_profit"],name="Net Profit",
                marker_color=AMBER,text=monthly["profit_label"],textposition="inside",
                insidetextfont=dict(color=INK,size=11),
                hovertemplate="%{x|%b %Y}<br>Net Profit: $%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=monthly["month"],y=monthly["net_revenue"],mode="text",
                    text=monthly["revenue_label"],textposition="top center",name="Net Revenue",
                    textfont=dict(color=INK,size=11),showlegend=False,hoverinfo="skip")
    fig.update_layout(barmode="relative",bargap=.28,margin=dict(l=12,r=12,t=55,b=12),
                      yaxis_title="Amount ($)",legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0))
    fig.update_yaxes(rangemode="tozero",tickprefix="$",tickformat=",.0f")
    fig.update_xaxes(title_text="Month",tickformat="%b %Y")
    st.markdown('<div class="section-head">Monthly Net Revenue Composition</div>',unsafe_allow_html=True)
    st.caption("Net revenue = total cost + net profit. Profit margin is displayed inside each profit segment.")
    if (monthly["net_profit"] < 0).any():
        st.info("At least one month has a net loss. Negative profit segments extend below zero, so those months do not appear as a conventional positive stacked total.")
    show_chart(fig,"exec_monthly",height=380)

    left,right=st.columns(2)
    prod=sales.groupby("product_name",as_index=False)["net_profit"].sum().nlargest(10,"net_profit").sort_values("net_profit")
    f1=px.bar(prod,x="net_profit",y="product_name",orientation="h",title="Top 10 Products · Net Profit",labels={"net_profit":"Net Profit","product_name":""},color_discrete_sequence=[INDIGO])
    with left:
        show_chart(f1,"top_products")
    store=sales.groupby(["store_name"],as_index=False).agg(net_revenue=("net_revenue","sum"),total_cost=("total_cost","sum"))
    store["net_profit"]=store["net_revenue"]-store["total_cost"]
    store["margin_pct"]=np.where(store["net_revenue"]!=0,store["net_profit"]/store["net_revenue"]*100,0)
    with right:
        f2=px.bar(store.nlargest(10,"margin_pct").sort_values("margin_pct"),x="margin_pct",y="store_name",orientation="h",title="Top Stores · Profit Margin",labels={"margin_pct":"Margin %","store_name":""},color_discrete_sequence=[AMBER])
        show_chart(f2,"top_stores")
    total_rx=len(rx_filtered)
    rx_per_order=total_rx/orders if orders else 0
    status="Healthy operating performance" if margin>=20 else "Monitor profitability and discount pressure" if margin>=10 else "Profitability requires management attention"
    st.markdown(f"""
    <div class="panel"><div class="section-head">Executive Health Summary</div>
    <div style="font-size:19px;font-weight:800;color:{INDIGO}">{status}</div>
    <p style="color:{MUTED};margin:7px 0 0">The selected portfolio generated <b>{money(net)}</b> in net revenue and <b>{money(profit)}</b> in net profit at a <b>{margin:.1f}%</b> margin.
    There were <b>{total_rx:,}</b> prescriptions issued in the selected period ({rx_per_order:.2f} prescriptions per order as a directional workload indicator).
    Review store margin dispersion and discount leakage before scaling promotional activity.</p></div>""",unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Page 2 — Sales Analysis
# ---------------------------------------------------------------------
elif page == "Sales Analysis":
    page_heading("Commercial performance","Sales Analysis","Understand sales momentum, discount leakage, payment mix and category-level economics.")
    gran=st.radio("Time granularity",["Monthly","Daily"],horizontal=True)
    sales["period"]=sales["month"] if gran=="Monthly" else sales["day"]
    trend=sales.groupby("period",as_index=False).agg(gross_revenue=("gross_revenue","sum"),discount_leakage=("discount_value","sum"),net_revenue=("net_revenue","sum"))
    fig=go.Figure()
    fig.add_bar(x=trend["period"],y=trend["gross_revenue"],name="Gross Revenue",marker_color=INDIGO)
    fig.add_scatter(x=trend["period"],y=trend["discount_leakage"],name="Discount Leakage",mode="lines",line=dict(color=AMBER,width=2))
    fig.add_scatter(x=trend["period"],y=trend["net_revenue"],name="Net Revenue",mode="lines+markers",line=dict(color="#3B82F6",width=2))
    st.markdown('<div class="section-head">Sales Trend & Discount Leakage</div>',unsafe_allow_html=True)
    show_chart(fig,"sales_trend")

    c1,c2=st.columns(2)
    region_store=sales.groupby(["region","store_name"],as_index=False)["net_revenue"].sum()
    with c1:
        st.markdown('<div class="section-head">Revenue by Region & Store</div>',unsafe_allow_html=True)
        show_chart(px.treemap(region_store,path=["region","store_name"],values="net_revenue",color="net_revenue",color_continuous_scale=["#DDE0FF",INDIGO]),"region_treemap")
    pay=sales.groupby("payment_method",as_index=False).agg(revenue=("net_revenue","sum"),orders=("sale_id","nunique"))
    pay["share_pct"]=pay["revenue"]/pay["revenue"].sum()*100
    pay["aov"]=pay["revenue"]/pay["orders"].replace(0,np.nan)
    with c2:
        st.markdown('<div class="section-head">Payment Method Mix</div>',unsafe_allow_html=True)
        show_chart(px.pie(pay,names="payment_method",values="revenue",hole=.62,color_discrete_sequence=PALETTE),"payment_donut")
    st.dataframe(pay.rename(columns={"payment_method":"Payment method","revenue":"Net revenue","orders":"Transactions","share_pct":"Revenue share %","aov":"Average order value"}).style.format({"Net revenue":"${:,.2f}","Revenue share %":"{:.1f}%","Average order value":"${:,.2f}"}),use_container_width=True,hide_index=True)
    cat=sales.groupby("category_name",as_index=False).agg(net_revenue=("net_revenue","sum"),avg_discount_pct=("discount_pct","mean"),transactions=("sale_id","nunique"))
    cat["avg_discount_pct"]*=100
    st.markdown('<div class="section-head">Category Revenue vs Average Discount</div>',unsafe_allow_html=True)
    show_chart(px.scatter(cat,x="avg_discount_pct",y="net_revenue",size="transactions",color="category_name",hover_name="category_name",labels={"avg_discount_pct":"Average discount %","net_revenue":"Net revenue"},size_max=42),"category_scatter")

# ---------------------------------------------------------------------
# Page 3 — Customer Analysis
# ---------------------------------------------------------------------
elif page == "Customer Analysis":
    page_heading("Customer intelligence","Customer Analysis","RFM segmentation, customer value tiers and new-versus-returning behavior.")
    base=sales_all[sales_all["customer_id"].notna()].copy()
    asof=base["sale_date"].max()
    cust=base.groupby("customer_id").agg(last_purchase=("sale_date","max"),frequency=("sale_id","nunique"),monetary=("net_revenue","sum"),first_purchase=("sale_date","min")).reset_index()
    cust["recency"]=(asof-cust["last_purchase"]).dt.days
    # NTILE(5)-style quintiles: recency is reversed because fewer days is better.
    # Rank-percentile scoring also works for very small customer samples.
    def quintile_score(series, reverse=False):
        score=np.ceil(series.rank(method="first",pct=True)*5).clip(1,5).astype(int)
        return 6-score if reverse else score
    cust["r_score"]=quintile_score(cust["recency"],reverse=True)
    cust["f_score"]=quintile_score(cust["frequency"])
    cust["m_score"]=quintile_score(cust["monetary"])
    cust["rfm_score"]=cust[["r_score","f_score","m_score"]].mean(axis=1)
    def segment(r):
        if r.r_score>=4 and r.f_score>=4 and r.m_score>=4: return "Champions"
        if r.r_score>=3 and r.f_score>=4: return "Loyal Customers"
        if r.r_score>=4 and r.f_score>=2: return "Potential Loyalists"
        if r.r_score>=4 and r.f_score==1: return "New Customers"
        if r.r_score<=2 and r.f_score>=3: return "At Risk"
        if r.r_score<=2 and r.f_score==2: return "Hibernating"
        return "Lost Customers"
    cust["rfm_segment"]=cust.apply(segment,axis=1)
    seg=cust.groupby("rfm_segment",as_index=False).agg(customers=("customer_id","count"),revenue=("monetary","sum"))
    seg["customer_share_pct"]=seg["customers"]/seg["customers"].sum()*100
    seg["revenue_share_pct"]=seg["revenue"]/seg["revenue"].sum()*100
    a,b=st.columns(2)
    with a:
        st.markdown('<div class="section-head">RFM Customer Distribution</div>',unsafe_allow_html=True)
        show_chart(px.bar(seg.sort_values("customers"),x="customers",y="rfm_segment",orientation="h",color="rfm_segment",color_discrete_sequence=PALETTE),"rfm_dist")
    with b:
        st.markdown('<div class="section-head">RFM Revenue Contribution</div>',unsafe_allow_html=True)
        show_chart(px.treemap(seg,path=["rfm_segment"],values="revenue",color="revenue",color_continuous_scale=["#FDE8B3",INDIGO]),"rfm_revenue")
    st.dataframe(seg.rename(columns={"rfm_segment":"RFM segment","customers":"Customers","revenue":"Net revenue","customer_share_pct":"Customer share %","revenue_share_pct":"Revenue share %"}).style.format({"Net revenue":"${:,.0f}","Customer share %":"{:.1f}%","Revenue share %":"{:.1f}%"}),use_container_width=True,hide_index=True)

    cust_dim=raw["dim_customers"][["customer_id","customer_segment"]]
    clv=cust.merge(cust_dim,on="customer_id",how="left")
    clv["customer_segment"]=clv["customer_segment"].fillna("Others")
    st.markdown('<div class="section-head">Customer Lifetime Value · Revenue Proxy</div>',unsafe_allow_html=True)
    st.caption("CLV here is observed cumulative net revenue per customer over the available transaction history, not a forecasted lifetime value.")
    show_chart(px.box(clv,x="customer_segment",y="monetary",color="customer_segment",labels={"customer_segment":"Customer tier","monetary":"Observed cumulative net revenue"},points=False,color_discrete_sequence=PALETTE),"clv_box")
    base["month"]=base["sale_date"].dt.to_period("M").dt.to_timestamp()
    first=base.groupby("customer_id")["sale_date"].min().rename("first_date")
    base=base.join(first,on="customer_id")
    base["customer_type"]=np.where(base["sale_date"].eq(base["first_date"]),"New","Returning")
    nt=base.groupby(["month","customer_type"],as_index=False)["net_revenue"].sum()
    st.markdown('<div class="section-head">New vs Returning Customer Revenue</div>',unsafe_allow_html=True)
    show_chart(px.bar(nt,x="month",y="net_revenue",color="customer_type",barmode="stack",color_discrete_map={"New":INDIGO,"Returning":AMBER}),"new_returning")
    aov=base.groupby("customer_type").agg(revenue=("net_revenue","sum"),orders=("sale_id","nunique"),customers=("customer_id","nunique")).reset_index()
    aov["aov"]=aov["revenue"]/aov["orders"].replace(0,np.nan)
    aov["revenue_per_customer"]=aov["revenue"]/aov["customers"].replace(0,np.nan)
    st.dataframe(aov[["customer_type","customers","orders","aov","revenue_per_customer"]].rename(columns={"customer_type":"Customer type","customers":"Customers","orders":"Orders","aov":"AOV","revenue_per_customer":"Net revenue / customer"}).style.format({"AOV":"${:,.2f}","Net revenue / customer":"${:,.2f}"}),use_container_width=True,hide_index=True)

# ---------------------------------------------------------------------
# Page 4 — Product & Inventory Analysis
# ---------------------------------------------------------------------
elif page == "Product & Inventory Analysis":
    page_heading("Supply & product intelligence","Product & Inventory Analysis","Monitor inventory exposure, replenishment risk, expiry status and product economics.")
    stock=raw["fact_stock_log"].merge(raw["dim_products"],on="product_id",how="left").merge(raw["dim_stores"][["store_id","store_name","region"]],on="store_id",how="left")
    stock["retail_value"]=stock["quantity"]*stock["unit_price"]
    stock["cost_value"]=stock["quantity"]*stock["cost_price"]
    stock["is_below_reorder_level"]=stock["is_below_reorder_level"].fillna(False).astype(bool)
    expiry=stock["shelf_life_status"].astype(str)
    critical=int(expiry.isin(["Critical Danger","Expired on Receipt"]).sum())
    reorder=int(stock["is_below_reorder_level"].sum())
    sold=sales_all.groupby("product_id")["quantity"].sum().rename("units_sold")
    inv=stock.groupby("product_id").agg(stock_units=("quantity","sum"),inventory_cost=("cost_value","sum")).join(sold).fillna(0).reset_index()
    inv["turnover_proxy"]=inv["units_sold"]/inv["stock_units"].replace(0,np.nan)
    prod_dim=raw["dim_products"][["product_id","product_name","unit_price","cost_price"]]
    profitability=sales_all.groupby("product_id").agg(net_revenue=("net_revenue","sum"),net_profit=("net_profit","sum")).reset_index().merge(prod_dim,on="product_id").merge(inv,on="product_id",how="left")
    profitability["margin_pct"]=np.where(profitability["net_revenue"]!=0,profitability["net_profit"]/profitability["net_revenue"]*100,0)
    turnover=profitability["turnover_proxy"].replace([np.inf,-np.inf],np.nan).median()
    c=st.columns(4)
    with c[0]: kpi("Inventory at Cost",money(stock["cost_value"].sum()),"Current stock snapshot")
    with c[1]: kpi("Inventory at Retail",money(stock["retail_value"].sum()),"Current stock snapshot",True)
    with c[2]: kpi("Critical / Expired Batches",f"{critical:,}","Critical Danger + Expired on Receipt")
    with c[3]: kpi("Below-Reorder Batches",f"{reorder:,}",f"Median turnover proxy {turnover:.2f}x" if pd.notna(turnover) else "Turnover unavailable",True)
    a,b=st.columns(2)
    with a:
        st.markdown('<div class="section-head">Shelf-Life & Expiry Risk</div>',unsafe_allow_html=True)
        status=stock["shelf_life_status"].value_counts().rename_axis("shelf_life_status").reset_index(name="batches")
        show_chart(px.pie(status,names="shelf_life_status",values="batches",hole=.55,color_discrete_sequence=PALETTE),"expiry_pie")
    with b:
        st.markdown('<div class="section-head">Inventory by Risk Status</div>',unsafe_allow_html=True)
        show_chart(px.bar(status,x="shelf_life_status",y="batches",color="shelf_life_status",color_discrete_sequence=PALETTE),"expiry_bar")
    st.markdown('<div class="section-head">Stock Conditions & Reorder Alerts</div>',unsafe_allow_html=True)
    only_alerts=st.checkbox("Show below-reorder batches only",value=True)
    alerts=stock[stock["is_below_reorder_level"]] if only_alerts else stock
    show_cols=[c for c in ["batch_number","product_name","store_name","quantity","reorder_level","is_below_reorder_level","expiry_date","shelf_life_status","condition_notes","supplier_id"] if c in alerts.columns]
    st.dataframe(alerts[show_cols].sort_values(["is_below_reorder_level","expiry_date"],ascending=[False,True]),use_container_width=True,hide_index=True)
    st.markdown('<div class="section-head">Product Profitability vs Inventory Efficiency</div>',unsafe_allow_html=True)
    st.caption("Turnover proxy = units sold over the available dataset ÷ current on-hand units. This is directional, not a time-normalized accounting turnover ratio.")
    show_chart(px.scatter(profitability,x="turnover_proxy",y="margin_pct",size="net_revenue",color="margin_pct",hover_name="product_name",labels={"turnover_proxy":"Units sold / current stock","margin_pct":"Profit margin %"},color_continuous_scale=["#F59E0B",INDIGO],size_max=40),"inventory_matrix")

# ---------------------------------------------------------------------
# Page 5 — Store & Geographic Analysis
# ---------------------------------------------------------------------
elif page == "Store & Geographic Analysis":
    page_heading("Network performance","Store & Geographic Analysis","Compare store economics, geographic contribution and pharmacy operating workload.")
    store=sales.groupby(["store_id","store_name","city","region"],as_index=False).agg(gross_revenue=("gross_revenue","sum"),net_revenue=("net_revenue","sum"),total_cost=("total_cost","sum"),net_profit=("net_profit","sum"),customers=("customer_id","nunique"))
    store["profit_margin_pct"]=np.where(store["net_revenue"]!=0,store["net_profit"]/store["net_revenue"]*100,0)
    rx_store=rx_filtered.groupby("store_id").size().rename("total_prescriptions")
    store=store.merge(rx_store,on="store_id",how="left").fillna({"total_prescriptions":0})
    emp=raw["dim_employees"].groupby("store_id").agg(pharmacist_count=("is_pharmacist","sum"),total_payroll=("salary","sum")).reset_index()
    store=store.merge(emp,on="store_id",how="left")
    store["prescriptions_per_pharmacist"]=store["total_prescriptions"]/store["pharmacist_count"].replace(0,np.nan)
    store["labor_cost_per_prescription"]=store["total_payroll"]/store["total_prescriptions"].replace(0,np.nan)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="section-head">Geographic Revenue & Profit</div>',unsafe_allow_html=True)
        city=store.groupby(["region","city"],as_index=False).agg(net_revenue=("net_revenue","sum"),net_profit=("net_profit","sum"))
        # City centroids are only supplied for the Egyptian demo locations. For a
        # production network, store latitude/longitude should live in dim_stores.
        city_coords={"Cairo":(30.0444,31.2357),"New Cairo":(30.0074,31.4913),
                     "Giza":(29.9870,31.2118),"6th of October":(29.9285,30.9188),
                     "Alexandria":(31.2001,29.9187),"Tanta":(30.7865,31.0004),
                     "Aswan":(24.0889,32.8998),"Luxor":(25.6872,32.6396),
                     "Ismailia":(30.5965,32.2715),"Suez":(29.9668,32.5498)}
        city["lat"]=city["city"].map(lambda x: city_coords.get(x,(np.nan,np.nan))[0])
        city["lon"]=city["city"].map(lambda x: city_coords.get(x,(np.nan,np.nan))[1])
        mapped=city.dropna(subset=["lat","lon"])
        if not mapped.empty:
            geo=px.scatter_mapbox(mapped,lat="lat",lon="lon",size="net_revenue",color="region",hover_name="city",
                                  hover_data={"net_revenue":":,.0f","net_profit":":,.0f","lat":False,"lon":False},
                                  size_max=35,zoom=4,mapbox_style="open-street-map")
            geo.update_layout(height=380,margin=dict(l=0,r=0,t=10,b=0),paper_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="Inter",color=INK,size=11),legend=dict(orientation="h",y=1.02))
            st.plotly_chart(geo,use_container_width=True,config={"displaylogo":False},key="store_geo_map")
        else:
            st.info("No recognized city coordinates are available. Add latitude/longitude columns to dim_stores to enable the map.")
    with c2:
        st.markdown('<div class="section-head">Region → City → Store</div>',unsafe_allow_html=True)
        tree=store.groupby(["region","city","store_name"],as_index=False)["net_revenue"].sum()
        show_chart(px.sunburst(tree,path=["region","city","store_name"],values="net_revenue",color="net_revenue",color_continuous_scale=["#DDE0FF",INDIGO]),"store_sunburst")
    st.markdown('<div class="section-head">Individual Store Scorecard</div>',unsafe_allow_html=True)
    score_cols=["store_name","city","region","gross_revenue","net_revenue","total_cost","net_profit","profit_margin_pct","total_prescriptions","prescriptions_per_pharmacist","labor_cost_per_prescription"]
    st.dataframe(store[score_cols].sort_values("net_profit",ascending=False).rename(columns={
        "store_name":"Store","city":"City","region":"Region","gross_revenue":"Gross revenue","net_revenue":"Net revenue","total_cost":"Total cost","net_profit":"Net profit","profit_margin_pct":"Profit margin %","total_prescriptions":"Prescriptions","prescriptions_per_pharmacist":"Prescriptions / pharmacist","labor_cost_per_prescription":"Labor cost / prescription"
    }).style.format({"Gross revenue":"${:,.0f}","Net revenue":"${:,.0f}","Total cost":"${:,.0f}","Net profit":"${:,.0f}","Profit margin %":"{:.1f}%","Prescriptions / pharmacist":"{:.1f}","Labor cost / prescription":"${:,.2f}"}),use_container_width=True,hide_index=True)
    st.markdown('<div class="section-head">Store Benchmarking</div>',unsafe_allow_html=True)
    selected=st.selectbox("Store to benchmark",store["store_name"].tolist())
    chosen=store[store["store_name"]==selected].iloc[0]
    metrics=["profit_margin_pct","net_revenue","customers","prescriptions_per_pharmacist"]
    labels=["Margin %","Net revenue","Unique customers","Rx / pharmacist"]
    network=store[metrics].mean(numeric_only=True)
    # Normalize store and network values to 0-100 relative to the observed max for readable radar comparison.
    vals=[]; avg=[]
    for m in metrics:
        mx=store[m].replace([np.inf,-np.inf],np.nan).max()
        vals.append(float(chosen[m]/mx*100) if pd.notna(chosen[m]) and mx else 0)
        avg.append(float(network[m]/mx*100) if pd.notna(network[m]) and mx else 0)
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals+[vals[0]],theta=labels+[labels[0]],fill="toself",name=selected,line_color=INDIGO))
    fig.add_trace(go.Scatterpolar(r=avg+[avg[0]],theta=labels+[labels[0]],fill="toself",name="Network average",line_color=AMBER))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100])),height=380)
    show_chart(fig,"store_radar")

# ---------------------------------------------------------------------
# Page 6 — Customer Behavior Analysis
# ---------------------------------------------------------------------
elif page == "Customer Behavior Analysis":
    page_heading("Retention & engagement","Customer Behavior Analysis","Track acquisition cohorts, repeat conversion, loyalty progression and time-to-return.")
    base=sales_all[sales_all["customer_id"].notna()].copy()
    tx=base.groupby(["customer_id","sale_id"],as_index=False).agg(sale_date=("sale_date","min"),revenue=("net_revenue","sum"),payment_method=("payment_method","first"),store_id=("store_id","first"))
    tx=tx.sort_values(["customer_id","sale_date","sale_id"])
    first=tx.groupby("customer_id",as_index=False).first().rename(columns={"sale_date":"first_purchase","payment_method":"first_payment","store_id":"first_store"})
    counts=tx.groupby("customer_id").agg(total_orders=("sale_id","nunique"),total_revenue=("revenue","sum")).reset_index()
    first=first.merge(counts,on="customer_id",how="left")
    first=first.merge(raw["dim_stores"][["store_id","region"]],left_on="first_store",right_on="store_id",how="left")
    first["cohort_month"]=first["first_purchase"].dt.to_period("M").dt.to_timestamp()
    cohort=first.groupby("cohort_month").agg(acquired=("customer_id","count"),repeat=("total_orders",lambda x:(x>=2).sum()),loyal=("total_orders",lambda x:(x>=5).sum())).reset_index()
    cohort["repeat_conversion_pct"]=cohort["repeat"]/cohort["acquired"]*100
    cohort["loyal_conversion_pct"]=cohort["loyal"]/cohort["acquired"]*100
    st.markdown('<div class="section-head">Monthly Acquisition Cohort Conversion</div>',unsafe_allow_html=True)
    heat=cohort.set_index(cohort["cohort_month"].dt.strftime("%Y-%m"))[["repeat_conversion_pct","loyal_conversion_pct"]]
    fig=px.imshow(heat,aspect="auto",text_auto=".1f",color_continuous_scale=["#FFF7E6","#F59E0B",INDIGO,],labels=dict(x="Conversion metric",y="Acquisition cohort",color="Conversion %"))
    show_chart(fig,"cohort_heatmap")
    a,b=st.columns(2)
    with a:
        st.markdown('<div class="section-head">Cohort by Geographic Region</div>',unsafe_allow_html=True)
        reg=first.groupby("region").agg(customers=("customer_id","count"),repeat_rate=("total_orders",lambda x:(x>=2).mean()*100)).reset_index()
        show_chart(px.bar(reg,x="region",y="repeat_rate",color="region",labels={"repeat_rate":"Repeat conversion %"},color_discrete_sequence=PALETTE),"cohort_region")
    with b:
        st.markdown('<div class="section-head">Cohort by First Payment Method</div>',unsafe_allow_html=True)
        pay=first.groupby("first_payment").agg(customers=("customer_id","count"),repeat_rate=("total_orders",lambda x:(x>=2).mean()*100)).reset_index()
        show_chart(px.bar(pay,x="first_payment",y="repeat_rate",color="first_payment",labels={"first_payment":"First payment","repeat_rate":"Repeat conversion %"},color_discrete_sequence=PALETTE),"cohort_payment")
    # Funnel thresholds match the SQL: >=1, >=2, >=5 distinct sale_id values.
    first_n=int((counts["total_orders"]>=1).sum())
    repeat_n=int((counts["total_orders"]>=2).sum())
    loyal_n=int((counts["total_orders"]>=5).sum())
    funnel=pd.DataFrame({"stage":["First Purchase (1+ Order)","Repeat Purchase (2+ Orders)","Loyal Customer (5+ Orders)"],"customers":[first_n,repeat_n,loyal_n]})
    funnel["conversion_from_previous_pct"]=[100,repeat_n/first_n*100 if first_n else 0,loyal_n/repeat_n*100 if repeat_n else 0]
    funnel["dropoff"]=[0,first_n-repeat_n,repeat_n-loyal_n]
    st.markdown('<div class="section-head">Conversion Funnel</div>',unsafe_allow_html=True)
    fig=go.Figure(go.Funnel(y=funnel["stage"],x=funnel["customers"],textinfo="value+percent initial",marker=dict(color=[INDIGO, "#6366F1", AMBER]),connector={"line":{"color":"#CBD5E1","dash":"dot"}}))
    show_chart(fig,"customer_funnel")
    st.dataframe(funnel.rename(columns={"stage":"Funnel stage","customers":"Customers","conversion_from_previous_pct":"Conversion from previous %","dropoff":"Customer drop-off"}).style.format({"Conversion from previous %":"{:.1f}%"}),use_container_width=True,hide_index=True)
    # Time to return is measured between each customer's first and second distinct transaction dates.
    ranked=tx.copy()
    ranked["order_rank"]=ranked.groupby("customer_id").cumcount()+1
    first_dates=ranked[ranked["order_rank"]==1][["customer_id","sale_date"]].rename(columns={"sale_date":"first_date"})
    second_dates=ranked[ranked["order_rank"]==2][["customer_id","sale_date"]].rename(columns={"sale_date":"second_date"})
    intervals=first_dates.merge(second_dates,on="customer_id")
    intervals["days_to_return"]=(intervals["second_date"]-intervals["first_date"]).dt.days
    intervals=intervals[intervals["days_to_return"]>=0]
    if not intervals.empty:
        avg_days=intervals["days_to_return"].mean()
        med_days=intervals["days_to_return"].median()
        intervals["return_bucket"]=pd.cut(intervals["days_to_return"],bins=[-1,7,30,60,90,np.inf],labels=["Within 7 Days","8–30 Days","31–60 Days","61–90 Days","90+ Days"])
        bucket=intervals["return_bucket"].value_counts(sort=False).rename_axis("return_bucket").reset_index(name="customers")
    else:
        avg_days=med_days=np.nan
        bucket=pd.DataFrame({"return_bucket":["Within 7 Days","8–30 Days","31–60 Days","61–90 Days","90+ Days"],"customers":[0]*5})
    m1,m2,m3=st.columns(3)
    with m1: kpi("Returning Customers",f"{len(intervals):,}","Customers with 2+ purchases")
    with m2: kpi("Average Days to Return",f"{avg_days:.1f}" if pd.notna(avg_days) else "—","First to second purchase",True)
    with m3: kpi("Median Days to Return",f"{med_days:.1f}" if pd.notna(med_days) else "—","First to second purchase")
    st.markdown('<div class="section-head">Time-to-Return Distribution</div>',unsafe_allow_html=True)
    show_chart(px.bar(bucket,x="return_bucket",y="customers",color="return_bucket",color_discrete_sequence=PALETTE,labels={"return_bucket":"Return interval","customers":"Customers"}),"return_distribution")

st.markdown("---")
<<<<<<< HEAD
st.caption("Meridian Health · Digitera BI Suite · Financial values use quantity × transaction unit price, discounts as fractions (0–1), and product cost price. Synthetic demo values are illustrative, not actual pharmacy operating data.")
=======
st.caption("Meridian Health · Digitera BI Suite · CSV-backed executive suite.")
>>>>>>> faed1c0e87c4664c54c128c95523452ce61194aa
