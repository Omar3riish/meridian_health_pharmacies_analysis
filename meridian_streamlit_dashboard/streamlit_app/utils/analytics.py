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
    # Group 2's amount column stores the per-unit selling price.
    "unit_price": ["unit_price", "selling_price", "price", "amount"],
    "discount_pct": ["discount_pct", "discount_percent", "discount"],
    "payment_method": ["payment_method", "payment_type", "payment"],
    "cost_price": ["cost_price", "unit_cost", "purchase_price"],
    "product_name": ["product_name", "name", "medicine_name"],
    "product_category": ["product_category", "category", "category_name"],
    "region": ["region", "state", "province", "area"],
    "city": ["city", "town"],
    "customer_type": ["customer_type", "customer_segment_type", "client_type", "customer_segment"],
}


def _standardize_columns(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.columns = [
        str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for col in out.columns
    ]
    for canonical, aliases in ALIASES.items():
        if canonical not in out.columns:
            found = next((alias for alias in aliases if alias in out.columns), None)
            if found:
                out = out.rename(columns={found: canonical})
    return out


def _standardize_dimension(df, id_col):
    out = _standardize_columns(df)
    if id_col in out.columns:
        out[id_col] = out[id_col].astype("string").str.strip()
    return out


def _numeric(series):
    return pd.to_numeric(
        series.astype("string")
        .str.replace(r"[$,]", "", regex=True)
        .str.strip(),
        errors="coerce",
    )


def prepare_sales(sales_raw, customers=None, products=None, stores=None):
    sales = _standardize_columns(sales_raw)
    if sales.empty:
        return sales

    dimensions = [
        (customers, "customer_id"),
        (products, "product_id"),
        (stores, "store_id"),
    ]

    for dimension, join_col in dimensions:
        dim = _standardize_dimension(dimension, join_col)
        if join_col not in sales.columns or join_col not in dim.columns:
            continue

        sales[join_col] = sales[join_col].astype("string").str.strip()
        dim = dim.drop_duplicates(subset=[join_col], keep="first")
        new_cols = [
            col for col in dim.columns
            if col == join_col or col not in sales.columns
        ]
        if len(new_cols) > 1:
            sales = sales.merge(
                dim[new_cols],
                on=join_col,
                how="left",
                validate="many_to_one",
            )

    if "quantity" not in sales.columns:
        sales["quantity"] = 1
    sales["quantity"] = _numeric(sales["quantity"]).fillna(0)

    if "unit_price" in sales.columns:
        sales["unit_price"] = _numeric(sales["unit_price"])
    else:
        sales["unit_price"] = np.nan

    if "discount_pct" in sales.columns:
        discount = _numeric(sales["discount_pct"]).fillna(0)
        # Source CSVs store percentages such as 8.1; processed files
        # store decimals such as 0.081. Support both representations.
        sales["discount_rate"] = np.where(discount > 1, discount / 100, discount)
        sales["discount_rate"] = sales["discount_rate"].clip(lower=0, upper=1)
    else:
        sales["discount_rate"] = 0.0

    if "revenue" in sales.columns:
        sales["revenue"] = _numeric(sales["revenue"])
    else:
        sales["revenue"] = (
            sales["quantity"]
            * sales["unit_price"]
            * (1 - sales["discount_rate"])
        )

    if "cost_price" in sales.columns:
        sales["cost_price"] = _numeric(sales["cost_price"])
        sales["cost_amount"] = sales["quantity"] * sales["cost_price"]
        sales["profit"] = sales["revenue"] - sales["cost_amount"]
    elif "cost_amount" in sales.columns:
        sales["cost_amount"] = _numeric(sales["cost_amount"])
        sales["profit"] = sales["revenue"] - sales["cost_amount"]
    else:
        # Do not label revenue as profit when cost information is missing.
        sales["profit"] = np.nan

    if "sale_date" in sales.columns:
        sales["sale_date"] = pd.to_datetime(
            sales["sale_date"], errors="coerce"
        )
    else:
        sales["sale_date"] = pd.NaT

    if "payment_method" in sales.columns:
        sales["payment_method"] = (
            sales["payment_method"].astype("string").str.strip().str.title()
        )

    for col in ["region", "city", "product_category", "customer_type"]:
        if col in sales.columns:
            sales[col] = sales[col].astype("string").str.strip()

    return sales


def _quartile_score(values, labels):
    """Stable quartile scoring even when a segment has very few customers."""
    n = len(values)
    if n == 0:
        return pd.Series(dtype="int64", index=values.index)
    if n == 1:
        return pd.Series([labels[-1]], index=values.index, dtype="int64")
    ranks = values.rank(method="first", ascending=True)
    bins = min(4, n)
    scores = pd.qcut(ranks, q=bins, labels=labels[-bins:])
    return scores.astype(int)


def build_rfm(sales):
    required = {"customer_id", "sale_date", "revenue"}
    if not required.issubset(sales.columns):
        return pd.DataFrame()

    data = sales.dropna(subset=["customer_id", "sale_date"]).copy()
    if data.empty:
        return pd.DataFrame()

    snapshot = data["sale_date"].max() + pd.Timedelta(days=1)
    frequency_agg = (
        ("sale_id", "nunique")
        if "sale_id" in data.columns
        else ("revenue", "size")
    )
    rfm = data.groupby("customer_id").agg(
        recency=("sale_date", lambda values: (snapshot - values.max()).days),
        frequency=frequency_agg,
        monetary=("revenue", "sum"),
    ).reset_index()

    rfm["R_score"] = _quartile_score(
        -rfm["recency"], [1, 2, 3, 4]
    )
    rfm["F_score"] = _quartile_score(
        rfm["frequency"], [1, 2, 3, 4]
    )
    rfm["M_score"] = _quartile_score(
        rfm["monetary"], [1, 2, 3, 4]
    )

    score = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
    rfm["segment"] = np.select(
        [score >= 10, score >= 8, score >= 6],
        [
            "Champions / High Value",
            "Loyal / Potential Loyalists",
            "Needs Attention",
        ],
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

    order_agg = (
        ("sale_id", "nunique")
        if "sale_id" in data.columns
        else ("revenue", "size")
    )
    summary = data.groupby(dimension, dropna=False).agg(
        total_revenue=("revenue", "sum"),
        customers=("customer_id", "nunique"),
        orders=order_agg,
    ).reset_index()

    customer_order_agg = (
        ("sale_id", "nunique")
        if "sale_id" in data.columns
        else ("revenue", "size")
    )
    customer_counts = data.groupby(
        [dimension, "customer_id"], dropna=False
    ).agg(customer_orders=customer_order_agg).reset_index()

    repeat = customer_counts.groupby(dimension, dropna=False).agg(
        repeat_customers=("customer_orders", lambda values: int((values > 1).sum()))
    ).reset_index()

    summary = summary.merge(repeat, on=dimension, how="left")
    summary["repeat_customer_rate_pct"] = (
        summary["repeat_customers"]
        / summary["customers"].replace(0, np.nan)
        * 100
    ).round(2)
    summary["revenue_per_customer"] = (
        summary["total_revenue"]
        / summary["customers"].replace(0, np.nan)
    ).round(2)

    return summary.sort_values("total_revenue", ascending=False)
