# Step 2 - answer the business questions in SQL
#
# loads the three tidy tables into DuckDB, builds the schema and the shared
# delivered_orders view in sql/schema.sql, runs every question in
# sql/questions.sql, and saves each answer to outputs/sql/ for the dashboard.
#
# DuckDB because it's real SQL from a single file with no server to set up,
# so it runs the same in Colab as on a laptop
#
#   python 02_run_sql.py

import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).parent
PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
OUT = ROOT / "outputs" / "sql"

DATES = ["order_purchase_timestamp", "order_estimated_delivery_date", "order_delivered_customer_date"]


def questions():
    # each block starts with "-- name:" and "-- question:", so the .sql file
    # stays the single source of truth and the dashboard shows the exact query
    text = (SQL_DIR / "questions.sql").read_text()
    out = []
    for block in re.split(r"\n(?=-- name: )", text):
        name = re.search(r"-- name: (\w+)", block)
        if not name:
            continue
        question = re.search(r"-- question: (.+)", block).group(1).strip()
        body = block[block.index("\n", block.index("-- question:")):].strip()
        out.append((name.group(1), question, body))
    return out


if __name__ == "__main__":
    if not (PROCESSED / "orders.csv").exists():
        raise SystemExit("run 01_load_and_validate.py first")
    OUT.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    # dates have to arrive as real timestamps, or the delivery-time math in
    # SQL would be subtracting text
    con.register("orders_src", pd.read_csv(PROCESSED / "orders.csv", parse_dates=DATES))
    con.register("order_items_src", pd.read_csv(PROCESSED / "order_items.csv"))
    con.register("sellers_src", pd.read_csv(PROCESSED / "sellers.csv"))
    con.execute((SQL_DIR / "schema.sql").read_text())

    for name, question, sql in questions():
        result = con.execute(sql).df()
        result.to_csv(OUT / f"{name}.csv", index=False)
        with pd.option_context("display.width", 200, "display.max_columns", 20):
            print(f"\n{question}\n{result.head(10).to_string(index=False)}")

    print(f"\nsaved {len(questions())} answers to outputs/sql/")
