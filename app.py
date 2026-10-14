# the dashboard
#
# seven tabs, one per audience:
#   overview            -> leadership: growth and service quality, same months year over year
#   delivery & reviews  -> operations: how late deliveries turn into bad reviews, and where
#   sellers             -> marketplace team: who to coach, and how concentrated revenue is
#   categories          -> category managers: revenue, freight cost, review problems
#   customers           -> CRM / marketing: repeat buying and payment behavior
#   data quality        -> anyone checking the work
#   sql answers         -> every question with the query behind it
#
# reads only from outputs/, which is committed, so the live site never has
# to reprocess the raw Olist tables when it wakes up
#
#   streamlit run app.py

import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
RED, BLUE, AMBER, GREY = "#c0392b", "#1f6f8b", "#edae49", "#9aa5b1"

st.set_page_config(page_title="Marketplace Analytics", layout="wide")

if not (OUT / "sql" / "kpi_summary.csv").exists():
    st.error("No results yet. Run 01_load_and_validate.py and 02_run_sql.py first.")
    st.stop()


@st.cache_data
def load():
    sql = {p.stem: pd.read_csv(p) for p in (OUT / "sql").glob("*.csv")}
    return sql, pd.read_csv(OUT / "data_quality_checks.csv")


def sql_blocks():
    text = (ROOT / "sql" / "questions.sql").read_text()
    out = {}
    for block in re.split(r"\n(?=-- name: )", text):
        name = re.search(r"-- name: (\w+)", block)
        if name:
            question = re.search(r"-- question: (.+)", block).group(1).strip()
            out[name.group(1)] = (question, block[block.index("\n", block.index("-- question:")):].strip())
    return out


def hbar(df, y, x, title, color=RED, sort="-x", height=260, fmt=".1f"):
    return (alt.Chart(df).mark_bar(color=color)
            .encode(y=alt.Y(f"{y}:N", sort=sort, title=None),
                    x=alt.X(f"{x}:Q", title=title),
                    tooltip=[y, alt.Tooltip(f"{x}:Q", format=fmt)])
            .properties(height=height))


sql, checks = load()
kpi = sql["kpi_summary"].set_index("period")
cur, prev = kpi.iloc[1], kpi.iloc[0]

st.title("Olist Marketplace Analytics")
st.caption("About 100,000 real orders from Olist, a Brazilian online marketplace, 2016–2018. "
           "Revenue in Brazilian reais (R$).")

tabs = st.tabs(["Overview", "Delivery & reviews", "Sellers", "Categories", "Customers & payments",
                "Data quality", "SQL answers"])
overview, delivery, sellers_tab, categories, customers, quality_tab, sql_tab = tabs


with overview:
    st.caption(f"Comparing {kpi.index[1]} with {kpi.index[0]}. The data ends in August 2018, so both years use the same eight months.")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Orders", f"{cur['orders']:,.0f}", f"{cur['orders'] / prev['orders'] - 1:+.0%}")
    k2.metric("Revenue (GMV)", f"R${cur['gmv'] / 1e6:.1f}M", f"{cur['gmv'] / prev['gmv'] - 1:+.0%}")
    k3.metric("Avg order value", f"R${cur['avg_order_value']:.0f}",
              f"{cur['avg_order_value'] / prev['avg_order_value'] - 1:+.1%}")
    k4.metric("Delivered on time", f"{cur['on_time_pct']:.1f}%",
              f"{cur['on_time_pct'] - prev['on_time_pct']:+.1f} pts")
    k5.metric("Avg review", f"{cur['avg_review']:.2f}", f"{cur['avg_review'] - prev['avg_review']:+.2f}")

    trend = sql["monthly_trend"].assign(month=lambda d: pd.to_datetime(d["month"]))
    base = alt.Chart(trend).encode(x=alt.X("yearmonth(month):T", title=None))
    st.markdown("**Monthly orders**")
    st.altair_chart(base.mark_bar(color=BLUE).encode(
        y=alt.Y("orders:Q", title="Orders"), tooltip=["yearmonth(month):T", "orders", "gmv"]).properties(height=200),
        width="stretch")
    st.markdown("**When deliveries ran late, reviews dropped the same month**")
    late = base.mark_line(color=RED, point=True).encode(
        y=alt.Y("late_pct:Q", title="Late deliveries (%)", axis=alt.Axis(titleColor=RED)),
        tooltip=["yearmonth(month):T", "late_pct", "avg_review"])
    review = base.mark_line(color=BLUE, point=True, strokeDash=[4, 3]).encode(
        y=alt.Y("avg_review:Q", title="Avg review (dashed)", scale=alt.Scale(domain=[3.6, 4.4]),
                axis=alt.Axis(titleColor=BLUE)))
    st.altair_chart(alt.layer(late, review).resolve_scale(y="independent").properties(height=260), width="stretch")
    st.caption("Late deliveries spiked after Black Friday 2017 and again in February–March 2018; average reviews fell in exactly those months.")


with delivery:
    p = sql["delivery_promise"].iloc[0]
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Median days to deliver", f"{p['median_days_to_deliver']:.0f}")
    d2.metric("Median days promised", f"{p['median_days_promised']:.0f}")
    d3.metric("Typical arrival", f"{p['median_days_early']:.0f} days early")
    d4.metric("Arrived late", f"{p['late_pct']:.1f}%")

    lvr = sql["lateness_vs_reviews"].assign(arrival=lambda d: d["arrival"].str[3:])
    left, right = st.columns(2)
    with left:
        st.markdown("**Average review by when the order arrived**")
        st.altair_chart(
            alt.Chart(lvr).mark_bar()
            .encode(x=alt.X("arrival:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30)),
                    y=alt.Y("avg_review:Q", title="Avg review", scale=alt.Scale(domain=[1, 5])),
                    color=alt.condition(alt.datum.avg_review < 4, alt.value(RED), alt.value(BLUE)),
                    tooltip=["arrival", "orders", "avg_review", "one_star_pct"])
            .properties(height=280), width="stretch")
    with right:
        st.markdown("**Share of 1-star reviews**")
        st.altair_chart(
            alt.Chart(lvr).mark_bar(color=RED)
            .encode(x=alt.X("arrival:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30)),
                    y=alt.Y("one_star_pct:Q", title="1-star reviews (%)"),
                    tooltip=["arrival", "orders", "one_star_pct"])
            .properties(height=280), width="stretch")
    worst = lvr.iloc[-1]
    st.write(f"Orders that arrived 8+ days late averaged **{worst['avg_review']:.1f} stars**, and "
             f"**{worst['one_star_pct']:.0f}%** got a 1-star review. Orders that arrived early averaged above 4.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Customer states with the most late deliveries** (500+ orders)")
        st.dataframe(sql["late_by_customer_state"], hide_index=True, width="stretch")
    with right:
        st.markdown("**Shipping routes that fail most often** (300+ orders)")
        st.dataframe(sql["worst_shipping_lanes"], hide_index=True, width="stretch")


with sellers_tab:
    sc = sql["seller_scorecard"]
    conc = sql["seller_concentration"]
    s1, s2, s3 = st.columns(3)
    s1.metric("Sellers with 100+ orders", f"{len(sc)}")
    s2.metric("Flagged for review or watch", f"{(sc['flag'] != 'OK').sum()}")
    s3.metric("Revenue from top 10% of sellers",
              f"{conc.iloc[:2]['gmv_share_pct'].sum():.0f}%")
    st.caption("Seller reviews use single-seller orders only. A review covers the whole order, so in a "
               "multi-seller order there's no fair way to say which seller earned it.")

    flags = st.multiselect("Show", sorted(sc["flag"].unique()),
                           default=[f for f in sorted(sc["flag"].unique()) if f != "OK"])
    st.dataframe(sc[sc["flag"].isin(flags)] if flags else sc, hide_index=True, width="stretch",
                 column_config={"seller_id": st.column_config.TextColumn("Seller", width="medium"),
                                "gmv": st.column_config.NumberColumn("Revenue (R$)", format="%d")})

    st.markdown("**How concentrated revenue is**")
    st.altair_chart(hbar(conc.assign(tier=lambda d: d["tier"].str[3:]), "tier", "gmv_share_pct",
                         "Share of revenue (%)", color=BLUE, sort=None, height=170), width="stretch")


with categories:
    cat = sql["category_performance"]
    left, right = st.columns(2)
    with left:
        st.markdown("**Revenue share by category** (top 20)")
        st.altair_chart(hbar(cat, "category", "gmv_share_pct", "Share of revenue (%)", color=BLUE, height=480),
                        width="stretch")
    with right:
        st.markdown("**Shipping cost as a share of price**")
        st.altair_chart(hbar(cat, "category", "freight_pct_of_price", "Freight as % of item price",
                             color=AMBER, height=480), width="stretch")
    st.markdown("**All metrics by category**")
    st.dataframe(cat, hide_index=True, width="stretch",
                 column_config={"gmv": st.column_config.NumberColumn("Revenue (R$)", format="%d")})


with customers:
    rep = sql["repeat_customers"]
    once = rep.set_index("segment").loc["One order"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Buyers who ordered only once", f"{once['customer_share_pct']:.0f}%")
    c2.metric("Revenue from repeat buyers", f"{100 - once['gmv_share_pct']:.1f}%")
    c3.metric("Median days to a second order",
              f"{rep.set_index('segment').loc['Two orders', 'median_days_to_return']:.0f}")
    st.write("Almost every customer buys once and never returns. That makes the first delivery the "
             "whole relationship, so a late first order is unlikely to get a second chance.")
    # one-time buyers never returned, so their "days to return" is blank on purpose
    st.dataframe(rep, hide_index=True, width="stretch",
                 column_config={"median_days_to_return": st.column_config.NumberColumn(
                     "Median days to return", format="%d")})

    st.markdown("**Payment methods and installment plans**")
    pay = sql["payment_mix"].assign(label=lambda d: d["payment_type"].str.replace("_", " ") + ", " + d["installments"].str[3:])
    st.altair_chart(hbar(pay, "label", "avg_order_value", "Average order value (R$)", color=BLUE,
                         sort=None, height=240, fmt=".2f"), width="stretch")
    st.caption("Card orders split into 7+ installments are almost four times the size of card orders paid in full. "
               "Installments are how customers afford bigger baskets.")


with quality_tab:
    st.subheader("Checks run before any number was trusted")
    st.dataframe(checks.assign(passed=checks["passed"].map({True: "Pass", False: "FAIL"})),
                 hide_index=True, width="stretch",
                 column_config={"check": "Check", "passed": "Result",
                                "detail": st.column_config.TextColumn("Detail", width="large")})
    st.markdown("""
**The two that mattered most**

- **`customer_id` is new on every order.** Counting customers with it says nobody ever comes back.
  `customer_unique_id` identifies the actual person and shows that 3% do.
- **The first and last months are nearly empty.** Four orders in September 2016, sixteen in September 2018.
  Trends use January 2017 to August 2018 only, so the charts don't show a fake collapse.
""")


with sql_tab:
    blocks = sql_blocks()
    names = [n for n in blocks if n in sql]
    q = st.selectbox("Question", names, format_func=lambda n: blocks[n][0])
    st.dataframe(sql[q], hide_index=True, width="stretch")
    with st.expander("Show the SQL"):
        st.code(blocks[q][1], language="sql")
