def calculate_kpis(df):
    orders = df["order_id"].nunique() if "order_id" in df.columns else len(df)
    revenue = df["total_pembayaran"].sum() if "total_pembayaran" in df.columns else 0
    avg_order_value = revenue / orders if orders else 0

    cancel_rate = (
        df["status_group"].eq("Batal").mean() * 100
        if len(df)
        else 0
    )

    returned_qty = (
        df["total_returned_qty"].sum()
        if "total_returned_qty" in df.columns
        else 0
    )
    total_qty = df["total_qty"].sum() if "total_qty" in df.columns else 0
    return_rate = returned_qty / total_qty * 100 if total_qty else 0

    return {
        "orders": orders,
        "revenue": revenue,
        "avg_order_value": avg_order_value,
        "cancel_rate": cancel_rate,
        "return_rate": return_rate,
    }
