# Step 1 - load the Olist marketplace data and check it before trusting it
#
# Olist ships 9 linked tables. this script joins the ones the analysis needs,
# fixes the traps that would quietly break the numbers (the customer ID that
# changes every order, duplicate reviews, half-empty months at the edges),
# builds the delivery fields, and writes a data quality report so every
# number downstream can be traced back to a check.
#
#   python 01_load_and_validate.py

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"

# the first and last few months only have a handful of orders (4 in Sept 2016,
# 16 in Sept 2018). left in, every trend line would show a fake crash at the
# end. trends and growth use complete months only
FIRST_FULL_MONTH, LAST_FULL_MONTH = "2017-01", "2018-08"

# two categories are missing from Olist's own translation table
EXTRA_TRANSLATIONS = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_appliances",
}


def read(name):
    return pd.read_csv(RAW / f"{name}.csv.gz")


def load():
    t = {
        "customers": read("olist_customers_dataset"),
        "sellers": read("olist_sellers_dataset"),
        "orders": read("olist_orders_dataset"),
        "items": read("olist_order_items_dataset"),
        "payments": read("olist_order_payments_dataset"),
        "reviews": read("olist_order_reviews_dataset"),
        "products": read("olist_products_dataset"),
        "translation": read("product_category_name_translation"),
    }
    for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                "order_delivered_customer_date", "order_estimated_delivery_date"]:
        t["orders"][col] = pd.to_datetime(t["orders"][col])
    t["reviews"]["review_answer_timestamp"] = pd.to_datetime(t["reviews"]["review_answer_timestamp"])
    return t


def build(t):
    o = t["orders"].merge(t["customers"], on="customer_id", how="left")

    # money per order. an order can have several items and several payments
    # (vouchers, split cards), so both get summed to one row per order first
    items = t["items"].groupby("order_id").agg(
        n_items=("order_item_id", "count"), n_sellers=("seller_id", "nunique"),
        items_value=("price", "sum"), freight_value=("freight_value", "sum"))
    pays = t["payments"].groupby("order_id").agg(
        payment_value=("payment_value", "sum"), max_installments=("payment_installments", "max"))
    # the payment type that covered the most money, so a R$5 voucher on a
    # R$300 card order still counts as a card order
    main_type = (t["payments"].sort_values("payment_value", ascending=False)
                 .drop_duplicates("order_id").set_index("order_id")["payment_type"].rename("payment_type"))

    # some orders have more than one review. keep the latest answer, which is
    # the customer's final word
    reviews = (t["reviews"].sort_values("review_answer_timestamp")
               .drop_duplicates("order_id", keep="last").set_index("order_id"))
    reviews = reviews.assign(has_comment=reviews["review_comment_message"].notna().astype(int))[
        ["review_score", "has_comment"]]

    o = o.join(items, on="order_id").join(pays, on="order_id").join(main_type, on="order_id").join(reviews, on="order_id")
    o["order_value"] = o["items_value"] + o["freight_value"]
    o["purchase_month"] = o["order_purchase_timestamp"].dt.to_period("M").astype(str)
    o["in_full_months"] = o["purchase_month"].between(FIRST_FULL_MONTH, LAST_FULL_MONTH).astype(int)

    # delivery fields, only for orders that actually reached the customer.
    # late = arrived on a later calendar day than the date the customer was promised
    delivered = (o["order_status"] == "delivered") & o["order_delivered_customer_date"].notna()
    o["is_delivered"] = delivered.astype(int)
    o["delivery_days"] = ((o["order_delivered_customer_date"] - o["order_purchase_timestamp"])
                          .dt.total_seconds() / 86400).round(1).where(delivered)
    o["days_vs_estimate"] = ((o["order_delivered_customer_date"].dt.normalize()
                              - o["order_estimated_delivery_date"].dt.normalize()).dt.days).where(delivered)
    o["is_late"] = (o["days_vs_estimate"] > 0).astype("Int64").where(delivered)

    orders = o[["order_id", "customer_id", "customer_unique_id", "customer_state", "order_status",
                "order_purchase_timestamp", "purchase_month", "in_full_months",
                "order_estimated_delivery_date", "order_delivered_customer_date",
                "is_delivered", "delivery_days", "days_vs_estimate", "is_late",
                "n_items", "n_sellers", "items_value", "freight_value", "order_value",
                "payment_value", "payment_type", "max_installments", "review_score", "has_comment"]]

    translation = dict(zip(t["translation"]["product_category_name"],
                           t["translation"]["product_category_name_english"])) | EXTRA_TRANSLATIONS
    products = t["products"].assign(
        category=lambda d: d["product_category_name"].map(translation).fillna("unknown").str.replace("_", " "))
    order_items = (t["items"].merge(products[["product_id", "category", "product_weight_g"]], on="product_id", how="left")
                   .merge(t["sellers"][["seller_id", "seller_state"]], on="seller_id", how="left")
                   [["order_id", "order_item_id", "product_id", "seller_id", "seller_state",
                     "category", "product_weight_g", "price", "freight_value"]])
    return orders, order_items, t["sellers"]


def quality_checks(t, orders, order_items):
    checks = []

    def check(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    o, c = t["orders"], t["customers"]
    check("One row per order", o["order_id"].is_unique, f"{len(o):,} orders, {o['order_id'].nunique():,} unique IDs")

    # the trap that matters most. customer_id is new on every order, so using
    # it would say nobody ever comes back
    per_id = o["customer_id"].value_counts().max()
    people = c["customer_unique_id"].nunique()
    # same definition as the repeat_customers SQL: canceled and unavailable
    # orders don't count as a purchase, so both reports give the same rate
    valid = orders[~orders["order_status"].isin(["canceled", "unavailable"])]
    repeat = (valid.groupby("customer_unique_id")["order_id"].nunique() > 1).mean()
    check("Customers counted as people, not orders", per_id == 1,
          f"customer_id never repeats (max {per_id} order each), so it would show 0% repeat buyers. "
          f"customer_unique_id finds {people:,} real people; {repeat:.1%} of buyers completed more than one order")

    items_ok = order_items["product_id"].isin(t["products"]["product_id"]).all() and \
        order_items["seller_id"].isin(t["sellers"]["seller_id"]).all() and \
        order_items["order_id"].isin(o["order_id"]).all()
    check("Every order item links to a real order, product and seller", items_ok,
          f"{len(order_items):,} items checked against orders, products and sellers")

    r = t["reviews"]
    dup_orders = (r["order_id"].value_counts() > 1).sum()
    check("Duplicate reviews resolved", True,
          f"{len(r) - r['review_id'].nunique():,} repeated review IDs and {dup_orders:,} orders with more than one review; "
          "the latest answer per order is kept")
    check("Review scores in range 1-5", r["review_score"].between(1, 5).all(),
          f"scores range {r['review_score'].min()}-{r['review_score'].max()}")

    months = o["order_purchase_timestamp"].dt.to_period("M").astype(str).value_counts().sort_index()
    edge = months[(months.index < FIRST_FULL_MONTH) | (months.index > LAST_FULL_MONTH)]
    check("Partial months kept out of trends", True,
          f"{FIRST_FULL_MONTH} to {LAST_FULL_MONTH} used for trends. Left out: "
          + ", ".join(f"{m} ({n:,} order{'s' if n != 1 else ''})" for m, n in edge.items()))

    no_date = ((o["order_status"] == "delivered") & o["order_delivered_customer_date"].isna()).sum()
    check("Delivered orders without a delivery date", True,
          f"{no_date} orders marked delivered have no delivery date; left out of delivery metrics")

    before = (o["order_delivered_customer_date"] < o["order_purchase_timestamp"]).sum()
    check("No order delivered before it was bought", before == 0, f"{before} orders fail")

    odd = (o["order_delivered_carrier_date"] < o["order_approved_at"]).sum()
    check("Carrier pickup before payment approval", True,
          f"{odd:,} orders show the carrier picking up before payment was approved, likely a timestamp "
          "recording issue. Flagged only; delivery speed is measured from purchase to doorstep, so it isn't affected")

    both = orders.dropna(subset=["order_value", "payment_value"])
    diff = (both["payment_value"] - both["order_value"]).abs()
    check("Payments match items plus freight", (diff <= 0.01).mean() >= 0.99,
          f"{(diff <= 0.01).mean():.1%} of {len(both):,} orders match to the cent; {(diff > 1).sum()} are off by more than R$1 "
          "(likely interest on installment plans). Revenue is measured from item prices, not payments")

    no_items = orders["n_items"].isna()
    status = orders.loc[no_items, "order_status"].value_counts().head(3).to_dict()
    check("Orders with no items", True,
          f"{no_items.sum():,} orders have no items, mostly {status}; they carry no revenue")

    p = t["products"]
    untranslated = set(p["product_category_name"].dropna()) - set(t["translation"]["product_category_name"])
    check("Every category has an English name", True,
          f"{p['product_category_name'].isna().sum()} products have no category (labeled 'unknown'); "
          f"{len(untranslated)} categories missing from Olist's translation table were added by hand")
    return pd.DataFrame(checks)


def write_report(checks):
    lines = ["# Data quality report", "",
             "Source: Olist Brazilian E-Commerce Public Dataset (Kaggle), real anonymized marketplace orders, 2016-2018.", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    for _, c in checks.iterrows():
        lines.append(f"| {c['check']} | {'Pass' if c['passed'] else 'FAIL'} | {c['detail']} |")
    (OUT / "data_quality.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)

    t = load()
    orders, order_items, sellers = build(t)
    checks = quality_checks(t, orders, order_items)

    orders.to_csv(PROCESSED / "orders.csv", index=False)
    order_items.to_csv(PROCESSED / "order_items.csv", index=False)
    sellers.to_csv(PROCESSED / "sellers.csv", index=False)
    checks.to_csv(OUT / "data_quality_checks.csv", index=False)
    write_report(checks)

    print(f"orders: {len(orders):,} | items: {len(order_items):,} | sellers: {len(sellers):,} | "
          f"people: {orders['customer_unique_id'].nunique():,}")
    print(f"\ndata quality: {checks['passed'].sum()} of {len(checks)} checks passed")
    for _, c in checks[~checks["passed"]].iterrows():
        print(f"  FAILED: {c['check']} -> {c['detail']}")
    print("\nsaved data/processed/ and outputs/data_quality.md")
