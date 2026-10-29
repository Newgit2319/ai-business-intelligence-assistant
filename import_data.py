"""Clean the supplied CSV and load valid rows into SQLite."""
from pathlib import Path
import sys
import pandas as pd

from database import get_connection, initialize_database

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "sales.csv"
REQUIRED = [
    "Transaction_Id", "Order_date", "Product", "Category", "Region",
    "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status"
]


def import_sales(csv_path: Path = CSV_PATH):
    if not csv_path.exists():
        raise FileNotFoundError(f"Sales CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing_columns = sorted(set(REQUIRED) - set(df.columns))
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

    original_count = len(df)
    df = df[REQUIRED].copy()
    df["Order_date"] = pd.to_datetime(df["Order_date"], errors="coerce", dayfirst=True)
    for col in ["Quantity", "Unit_price", "Discount_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["Transaction_Id", "Product", "Category", "Region", "Sales_channel", "Status"]:
        df[col] = df[col].astype("string").str.strip()

    df = df.drop_duplicates(subset=["Transaction_Id"], keep="first")
    required_not_missing = df[REQUIRED].notna().all(axis=1)
    valid = (
        required_not_missing
        & (df["Transaction_Id"] != "")
        & (df["Product"] != "")
        & (df["Quantity"] > 0)
        & (df["Unit_price"] >= 0)
        & (df["Discount_amount"] >= 0)
        & (df["Discount_amount"] <= df["Quantity"] * df["Unit_price"])
    )
    cleaned = df.loc[valid].copy()
    cleaned["Order_date"] = cleaned["Order_date"].dt.strftime("%Y-%m-%d")
    cleaned["Quantity"] = cleaned["Quantity"].astype(int)
    cleaned["Unit_price"] = cleaned["Unit_price"].astype(float)
    cleaned["Discount_amount"] = cleaned["Discount_amount"].astype(float)

    initialize_database()
    with get_connection() as conn:
        conn.execute("DELETE FROM sales")
        cleaned.columns = [
            "transaction_id", "order_date", "product", "category", "region",
            "sales_channel", "quantity", "unit_price", "discount_amount", "status"
        ]
        cleaned.to_sql("sales", conn, if_exists="append", index=False)
        conn.commit()

    report = {
        "source_rows": original_count,
        "loaded_rows": len(cleaned),
        "rejected_rows": original_count - len(cleaned),
        "database": str(Path(__file__).resolve().parent / "sales.db"),
    }
    print("Sales import complete:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    return report


if __name__ == "__main__":
    supplied = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else CSV_PATH
    import_sales(supplied)
