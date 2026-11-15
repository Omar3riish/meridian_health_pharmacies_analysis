import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.data_loader import load_project_data
from utils.analytics import prepare_sales, build_rfm, build_cohort_summary

st.set_page_config(
    page_title="Meridian Health | Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern dark-friendly visual styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(145deg, #0b1220 0%, #111827 55%, #172033 100%); }
    section[data-testid="stSidebar"] { background: #0b1322; border-right: 1px solid #263449; }
    .block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30,41,59,.95), rgba(20,31,49,.95));
        border: 1px solid #334155; padding: 16px 18px; border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] { color: #aab8cc; }
    div[data-testid="stMetricValue"] { color: #f8fafc; }
    h1, h2, h3 { color: #f8fafc; }
    .small-muted { color: #9caec4; font-size: .9rem; }
    div[data-testid="stAlert"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("💊 Meridian Health Analytics")
st.caption("Pharmacy operations • Sales performance • Customer behavior • Inventory insights")

with st.sidebar:
    st.markdown("## Meridian Health")
    st.caption("Interactive analytics workspace")
    source_mode = st.selectbox(
        "Data connection",
        ["PostgreSQL first, CSV fallback", "CSV only", "PostgreSQL only"],
        index=0,
        help="The recommended mode tries PostgreSQL for each dataset and uses the matching CSV when the database/table is unavailable."
    )
    page = st.radio(
        "Explore dashboard",
        [
            "Executive Overview",
            "Sales Analysis",
            "Customer Analysis",
            "Product & Inventory",
            "Store & Geographic Analysis",
            "Cohort Analysis",
            "Data Quality"
        ],
    )
    st.divider()
    st.caption("Data source: PostgreSQL / local CSV files")
    st.caption("Built with Streamlit, Pandas and Plotly")

@st.cache_data(ttl=300, show_spinner="Loading Meridian Health data...")
def get_data(mode):
    return load_project_data(mode)

try:
    datasets, source_notes = get_data(source_mode)
except Exception as exc:
    st.error("The dashboard could not load its datasets.")
    st.exception(exc)
    st.stop()

sales_raw = datasets.get("sales", pd.DataFrame())
customers = datasets.get("customers", pd.DataFrame())
products = datasets.get("products", pd.DataFrame())
stores = datasets.get("stores", pd.DataFrame())
inventory = datasets.get("inventory", pd.DataFrame())
employees = datasets.get("employees", pd.DataFrame())
prescriptions = datasets.get("prescriptions", pd.DataFrame())
categories = datasets.get("categories", pd.DataFrame())
suppliers = datasets.get("suppliers", pd.DataFrame())

sales = prepare_sales(sales_raw, customers, products, stores)

with st.sidebar.expander("Loaded data sources", expanded=False):
    for key, note in source_notes.items():
        st.write(f"**{key.title()}:** {note}")
    st.write(f"**Sales rows:** {len(sales):,}")
    st.write(f"**Customers:** {len(customers):,}")
    st.write(f"**Products:** {len(products):,}")

if sales.empty:
    st.warning(
        "No sales rows were loaded. Add your sales CSV files under `data/raw/` "
        "or configure PostgreSQL in `.streamlit/secrets.toml`. See README.md."
    )
    st.stop()

# Shared filters
sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")
valid_dates = sales["sale_date"].dropna()
with st.sidebar:
    st.markdown("### Filters")
    if not valid_dates.empty:
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
        date_range = st.date_input("Sale date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

    region_col = next((c for c in ["region", "city"] if c in sales.columns), None)
    if region_col:
        regions = sorted(sales[region_col].dropna().astype(str).unique().tolist())
        selected_regions = st.multiselect("Region / city", regions, default=regions)
    else:
        selected_regions = []

filtered = sales.copy()
if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2 and "sale_date" in filtered:
    filtered = filtered[
        filtered["sale_date"].isna()
        | filtered["sale_date"].dt.date.between(date_range[0], date_range[1])
    ]
if region_col and selected_regions:
    filtered = filtered[filtered[region_col].astype(str).isin(selected_regions)]

def money(value):
    return f"${value:,.2f}" if pd.notna(value) else "—"

def metric_row(frame):
    revenue = frame["revenue"].sum() if "revenue" in frame else 0
    profit = frame["profit"].sum() if "profit" in frame else np.nan
    orders = frame["sale_id"].nunique() if "sale_id" in frame else len(frame)
    customers_n = frame["customer_id"].nunique() if "customer_id" in frame else 0
    margin = (profit / revenue * 100) if pd.notna(profit) and revenue else np.nan
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", money(revenue))
    c2.metric("Profit", money(profit))
    c3.metric("Orders", f"{orders:,}")
    c4.metric("Customers", f"{customers_n:,}")
    if pd.notna(margin):
        st.caption(f"Calculated profit margin: {margin:.1f}%")

def chart_or_note(condition, message):
    if not condition:
        st.info(message)

if page == "Executive Overview":
    st.subheader("Executive Overview")
    metric_row(filtered)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Revenue over time")
        trend = filtered.dropna(subset=["sale_date"]).groupby(
            filtered.dropna(subset=["sale_date"])["sale_date"].dt.to_period("M").astype(str)
        )["revenue"].sum().reset_index()
        if not trend.empty:
            trend.columns = ["month", "revenue"]
            fig = px.line(trend, x="month", y="revenue", markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("A valid sale_date is needed for a monthly trend.")
    with right:
        st.markdown("#### Revenue by payment method")
        if "payment_method" in filtered.columns:
            by_payment = filtered.groupby("payment_method", dropna=False)["revenue"].sum().reset_index()
            fig = px.pie(by_payment, names="payment_method", values="revenue", hole=.55, template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payment_method column was found.")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Top products by revenue")
        if "product_name" in filtered.columns:
            top = filtered.groupby("product_name")["revenue"].sum().nlargest(10).reset_index()
            fig = px.bar(top.sort_values("revenue"), x="revenue", y="product_name", orientation="h", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Join a product dimension containing product_name to see this chart.")
    with right:
        st.markdown("#### Revenue by region")
        if region_col:
            reg = filtered.groupby(region_col)["revenue"].sum().nlargest(10).reset_index()
            fig = px.bar(reg, x=region_col, y="revenue", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Join a store or customer dimension containing region/city.")

elif page == "Sales Analysis":
    st.subheader("Sales Analysis")
    metric_row(filtered)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Sales by product category")
        if "product_category" in filtered.columns:
            x = filtered.groupby("product_category")["revenue"].sum().nlargest(15).reset_index()
            fig = px.bar(x, x="product_category", y="revenue", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No product_category field found. Check your products table/CSV.")
    with c2:
        st.markdown("#### Payment method")
        if "payment_method" in filtered.columns:
            x = filtered.groupby("payment_method")["revenue"].agg(["sum", "count"]).reset_index()
            fig = px.bar(x, x="payment_method", y="sum", color="count", template="plotly_dark",
                         labels={"sum": "Revenue", "count": "Sales rows"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payment_method field found.")
    st.markdown("#### Sales records")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

elif page == "Customer Analysis":
    st.subheader("Customer Analysis")
    if "customer_id" not in filtered.columns:
        st.warning("Customer analysis requires customer_id in the sales data.")
    else:
        rfm = build_rfm(filtered)
        if not rfm.empty:
            a, b, c = st.columns(3)
            a.metric("Customers analyzed", f"{len(rfm):,}")
            b.metric("Average customer revenue", money(rfm["monetary"].mean()))
            c.metric("Repeat customers", f"{(rfm['frequency'] > 1).sum():,}")
            if "segment" in rfm.columns:
                seg = rfm.groupby("segment").size().reset_index(name="customers")
                fig = px.bar(seg, x="segment", y="customers", color="segment", template="plotly_dark")
                fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(rfm.sort_values("monetary", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("RFM requires customer_id and sale_date. Confirm both fields are available.")

elif page == "Product & Inventory":
    st.subheader("Product & Inventory")
    if not products.empty:
        st.markdown("#### Product catalog")
        st.dataframe(products, use_container_width=True, hide_index=True)
    else:
        st.info("No product catalog was loaded.")
    if not inventory.empty:
        st.markdown("#### Stock condition records")
        st.dataframe(inventory, use_container_width=True, hide_index=True)
        st.caption("Inventory KPIs will be added after the stock-condition schema and status definitions are confirmed.")
    else:
        st.info("No stock-condition log was loaded. Add stock_condition_log.csv or configure its PostgreSQL table.")
    if "product_name" in filtered.columns:
        st.markdown("#### Product profitability")
        if "profit" in filtered.columns:
            p = filtered.groupby("product_name")[["revenue", "profit"]].sum().nlargest(15, "revenue").reset_index()
            fig = px.bar(p, x="product_name", y=["revenue", "profit"], barmode="group", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Profit requires a product cost_price or a transaction-level cost field.")

elif page == "Store & Geographic Analysis":
    st.subheader("Store & Geographic Analysis")
    if "store_id" in filtered.columns:
        store_metrics = filtered.groupby("store_id").agg(
            revenue=("revenue", "sum"),
            orders=("sale_id", "nunique") if "sale_id" in filtered.columns else ("revenue", "size"),
            customers=("customer_id", "nunique") if "customer_id" in filtered.columns else ("revenue", "size"),
        ).reset_index().sort_values("revenue", ascending=False)
        st.dataframe(store_metrics, use_container_width=True, hide_index=True)
        fig = px.bar(store_metrics.head(20), x="store_id", y="revenue", template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Store analysis requires store_id in sales.")
    if not stores.empty:
        with st.expander("Store dimension data"):
            st.dataframe(stores, use_container_width=True, hide_index=True)

elif page == "Cohort Analysis":
    st.subheader("Cohort Analysis")
    st.caption("These are attribute-based cohorts, not month-of-first-purchase cohorts: geographic, product, store, customer type and payment method.")
    cohort_type = st.selectbox(
        "Choose cohort dimension",
        ["Geographic (region/city)", "Product category", "Store", "Customer type", "Payment method"]
    )
    dimension_map = {
        "Geographic (region/city)": ["region", "city"],
        "Product category": ["product_category"],
        "Store": ["store_id"],
        "Customer type": ["customer_type"],
        "Payment method": ["payment_method"],
    }
    candidates = dimension_map[cohort_type]
    dim = next((c for c in candidates if c in filtered.columns), None)
    if dim:
        summary = build_cohort_summary(filtered, dim)
        st.dataframe(summary, use_container_width=True, hide_index=True)
        if not summary.empty:
            fig = px.bar(summary.head(20), x=dim, y="total_revenue", color="repeat_customer_rate_pct",
                         template="plotly_dark", labels={"repeat_customer_rate_pct": "Repeat customer rate %"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"The selected cohort field is not available in the loaded data. Expected one of: {', '.join(candidates)}.")
        st.write("Check whether the corresponding customer, product or store dimension has been loaded and joined.")

elif page == "Data Quality":
    st.subheader("Data Quality Snapshot")
    st.caption("A quick profile of the filtered sales dataset. This does not replace the detailed SQL data-quality checks.")
    quality = pd.DataFrame({
        "column": filtered.columns,
        "data_type": [str(filtered[c].dtype) for c in filtered.columns],
        "missing_values": [int(filtered[c].isna().sum()) for c in filtered.columns],
        "missing_pct": [(filtered[c].isna().mean() * 100).round(2) for c in filtered.columns],
        "distinct_values": [int(filtered[c].nunique(dropna=True)) for c in filtered.columns],
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)
    duplicates = int(filtered.duplicated().sum())
    st.metric("Fully duplicated rows in filtered sales", f"{duplicates:,}")
    st.markdown("#### Data source diagnostics")
    for key, note in source_notes.items():
        st.write(f"- **{key}:** {note}")

st.divider()
st.caption("Meridian Health Analytics | Figures depend on the fields available in the connected database or CSV files. Validate business definitions before publishing.")
