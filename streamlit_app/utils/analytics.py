import numpy as np
import pandas as pd

ALIASES = {
    "sale_id": ["sale_id", "transaction_id", "order_id", "invoice_id"],
    "customer_id": ["customer_id", "client_id", "patient_id"],
    "store_id": ["store_id", "branch_id", "pharmacy_id"],
    "employee_id": ["employee_id", "staff_id"],
    "product_id": ["product_id", "item_id", "medicine_id"],
    "sale_date": ["sale_date", "transaction_date", "order_date", "date"],
    "quantity": ["quantity", "qty", "units_sold"],
    "unit_price": ["unit_price", "selling_price", "price"],
    "discount_pct": ["discount_pct", "discount_percent", "discount"],
    "payment_method": ["payment_method", "payment_type", "payment"],
    "cost_price": ["cost_price", "unit_cost", "purchase_price"],
    "product_name": ["product_name", "name", "medicine_name"],
    "product_category": ["product_category", "category", "category_name"],
    "region": ["region", "state", "province", "area"],
    "city": ["city", "town"],
    "customer_type": ["customer_type", "customer_segment_type", "client_type"],
}

def _standardize_columns(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    for canonical, aliases in ALIASES.items():
        if canonical not in out.columns:
            found = next((a for a in aliases if a in out.columns), None)
            if found:
                out = out.rename(columns={found: canonical})
    return out

def _standardize_dimension(df, id_col):
    out = _standardize_columns(df)
    if id_col in out.columns:
        out[id_col] = out[id_col].astype(str).str.strip()
    return out

def prepare_sales(sales_raw, customers=None, products=None, stores=None):
    sales = _standardize_columns(sales_raw)
    if sales.empty:
        return sales

    for key, dim, join_col in [
        ("customers", customers, "customer_id"),
        ("products", products, "product_id"),
        ("stores", stores, "store_id"),
    ]:
        d = _standardize_dimension(dim, join_col)
        if join_col in sales.columns and join_col in d.columns:
            sales[join_col] = sales[join_col].astype(str).str.strip()
            # Avoid overwriting sales fields; use dimension values where sales lacks them.
            d = d.drop_duplicates(subset=[join_col], keep="first")
            new_cols = [c for c in d.columns if c == join_col or c not in sales.columns]
            sales = sales.merge(d[new_cols], on=join_col, how="left")

    if "quantity" not in sales.columns:
        sales["quantity"] = 1
    sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce").fillna(0)

    if "unit_price" in sales.columns:
        sales["unit_price"] = (
            sales["unit_price"].astype(str).str.replace(r"[$,]", "", regex=True).str.strip()
        )
        sales["unit_price"] = pd.to_numeric(sales["unit_price"], errors="coerce")
    else:
        sales["unit_price"] = np.nan

    if "discount_pct" in sales.columns:
        discount = pd.to_numeric(sales["discount_pct"], errors="coerce").fillna(0)
        # Accept either decimal form (0.10) or percentage form (10).
        sales["discount_rate"] = np.where(discount > 1, discount / 100, discount)
    else:
        sales["discount_rate"] = 0.0

    if "revenue" in sales.columns:
        sales["revenue"] = pd.to_numeric(
            sales["revenue"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"
        )
    else:
        sales["revenue"] = sales["quantity"] * sales["unit_price"] * (1 - sales["discount_rate"])

    if "cost_price" in sales.columns:
        sales["cost_price"] = pd.to_numeric(sales["cost_price"], errors="coerce")
        sales["cost_amount"] = sales["quantity"] * sales["cost_price"]
        sales["profit"] = sales["revenue"] - sales["cost_amount"]
    elif "cost_amount" in sales.columns:
        sales["cost_amount"] = pd.to_numeric(sales["cost_amount"], errors="coerce")
        sales["profit"] = sales["revenue"] - sales["cost_amount"]
    else:
        sales["profit"] = np.nan

    if "sale_date" in sales.columns:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce", dayfirst=True)
    else:
        sales["sale_date"] = pd.NaT

    return sales

def build_rfm(sales):
    required = {"customer_id", "sale_date", "revenue"}
    if not required.issubset(sales.columns):
        return pd.DataFrame()
    data = sales.dropna(subset=["customer_id", "sale_date"]).copy()
    if data.empty:
        return pd.DataFrame()
    snapshot = data["sale_date"].max() + pd.Timedelta(days=1)
    rfm = data.groupby("customer_id").agg(
        recency=("sale_date", lambda x: (snapshot - x.max()).days),
        frequency=("sale_id", "nunique") if "sale_id" in data.columns else ("revenue", "size"),
        monetary=("revenue", "sum"),
    ).reset_index()
    # Rank-based scoring avoids qcut failures when many values are tied.
    rfm["R_score"] = pd.qcut(rfm["recency"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    score = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
    rfm["segment"] = np.select(
        [score >= 10, score >= 8, score >= 6],
        ["Champions / High Value", "Loyal / Potential Loyalists", "Needs Attention"],
        default="At Risk / Low Engagement",
    )
    return rfm.sort_values("monetary", ascending=False)

def build_cohort_summary(sales, dimension):
    required = {dimension, "customer_id", "revenue"}
    if not required.issubset(sales.columns):
        return pd.DataFrame()
    data = sales.dropna(subset=[dimension, "customer_id"]).copy()
    if data.empty:
        return pd.DataFrame()
    orders = data.groupby(dimension).agg(
        total_revenue=("revenue", "sum"),
        customers=("customer_id", "nunique"),
        orders=("sale_id", "nunique") if "sale_id" in data.columns else ("revenue", "size"),
    ).reset_index()
    repeat = data.groupby([dimension, "customer_id"]).agg(
        customer_orders=("sale_id", "nunique") if "sale_id" in data.columns else ("revenue", "size")
    ).reset_index()
    repeat = repeat.groupby(dimension)["customer_orders"].apply(lambda x: int((x > 1).sum())).reset_index(name="repeat_customers")
    result = orders.merge(repeat, on=dimension, how="left")
    result["repeat_customer_rate_pct"] = (
        result["repeat_customers"] / result["customers"].replace(0, np.nan) * 100
    ).round(2)
    result["revenue_per_customer"] = (
        result["total_revenue"] / result["customers"].replace(0, np.nan)
    ).round(2)
    return result.sort_values("total_revenue", ascending=False)
