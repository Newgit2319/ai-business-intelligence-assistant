"""Deterministic sales analytics. All calculations come from SQLite."""
from datetime import datetime
from database import get_connection

REVENUE_SQL = "(quantity * unit_price - discount_amount)"
BASE_FILTER = "UPPER(status) = 'COMPLETED' AND quantity > 0 AND unit_price >= 0"


def rows(query, params=()):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def total_revenue():
    result = rows(f"SELECT ROUND(COALESCE(SUM({REVENUE_SQL}), 0), 2) AS revenue, COUNT(*) AS transactions FROM sales WHERE {BASE_FILTER}")[0]
    return {"answer": f"Total revenue is ₹{result['revenue']:,.2f} across {result['transactions']} completed transactions.", "data": [result], "metric": "revenue"}


def highest_revenue_product():
    data = rows(f"SELECT product, ROUND(SUM({REVENUE_SQL}), 2) AS revenue, SUM(quantity) AS units_sold FROM sales WHERE {BASE_FILTER} GROUP BY product ORDER BY revenue DESC, product ASC LIMIT 1")
    if not data:
        return {"answer": "There is no valid completed sales data to analyze.", "data": [], "metric": "revenue"}
    d = data[0]
    return {"answer": f"{d['product']} generated the highest revenue at ₹{d['revenue']:,.2f} ({d['units_sold']} units sold).", "data": data, "metric": "revenue"}


def highest_sales_region():
    data = rows(f"SELECT region, ROUND(SUM({REVENUE_SQL}), 2) AS revenue, SUM(quantity) AS units_sold FROM sales WHERE {BASE_FILTER} GROUP BY region ORDER BY revenue DESC, region ASC LIMIT 1")
    if not data:
        return {"answer": "There is no valid completed sales data to analyze.", "data": [], "metric": "revenue"}
    d = data[0]
    return {"answer": f"{d['region']} generated the highest sales revenue at ₹{d['revenue']:,.2f}.", "data": data, "metric": "revenue"}


def monthly_revenue():
    data = rows(f"SELECT substr(order_date, 1, 7) AS month, ROUND(SUM({REVENUE_SQL}), 2) AS revenue, SUM(quantity) AS units_sold FROM sales WHERE {BASE_FILTER} GROUP BY substr(order_date, 1, 7) ORDER BY month")
    return {"answer": "Here is the monthly revenue trend for completed transactions.", "data": data, "metric": "revenue"}


def compare_months(month_a: str, month_b: str):
    # Expected month format: YYYY-MM. Validate before passing to SQL.
    try:
        datetime.strptime(month_a, "%Y-%m")
        datetime.strptime(month_b, "%Y-%m")
    except (TypeError, ValueError):
        return {"answer": "Please provide both months in YYYY-MM format, for example January 2026 and February 2026.", "data": [], "metric": "revenue"}
    data = rows(
        f"SELECT substr(order_date, 1, 7) AS month, ROUND(SUM({REVENUE_SQL}), 2) AS revenue FROM sales WHERE {BASE_FILTER} AND substr(order_date, 1, 7) IN (?, ?) GROUP BY substr(order_date, 1, 7) ORDER BY month",
        (month_a, month_b),
    )
    values = {item["month"]: float(item["revenue"] or 0) for item in data}
    a, b = values.get(month_a, 0.0), values.get(month_b, 0.0)
    change = round(b - a, 2)
    pct = round((change / a) * 100, 2) if a != 0 else None
    comparison = [
        {"month": month_a, "revenue": round(a, 2), "change": None, "percentage_change": None},
        {"month": month_b, "revenue": round(b, 2), "change": change, "percentage_change": pct},
    ]
    direction = "increased" if change > 0 else "decreased" if change < 0 else "did not change"
    pct_text = f" ({pct:+.2f}%)" if pct is not None else " (percentage change unavailable because the first month's revenue is zero)"
    return {"answer": f"Revenue {direction} by ₹{abs(change):,.2f} from {month_a} to {month_b}{pct_text}.", "data": comparison, "metric": "revenue"}


def category_revenue():
    data = rows(f"SELECT category, ROUND(SUM({REVENUE_SQL}), 2) AS revenue FROM sales WHERE {BASE_FILTER} GROUP BY category ORDER BY revenue DESC")
    return {"answer": "Revenue by product category.", "data": data, "metric": "revenue"}


def channel_revenue():
    data = rows(f"SELECT sales_channel, ROUND(SUM({REVENUE_SQL}), 2) AS revenue FROM sales WHERE {BASE_FILTER} GROUP BY sales_channel ORDER BY revenue DESC")
    return {"answer": "Revenue by sales channel.", "data": data, "metric": "revenue"}
