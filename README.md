# E-Commerce Marketplace Analytics

[![Open the live dashboard](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ecommerce-analytics-6sbbpjme6k2qx4nuczlynb.streamlit.app/)

**[View the live dashboard →](https://ecommerce-analytics-6sbbpjme6k2qx4nuczlynb.streamlit.app/)**

**What drives customer satisfaction on an online marketplace, which sellers and routes are hurting it, and where should operations focus first?**

Olist is a Brazilian marketplace that connects small sellers to big online stores. This project takes about 100,000 of its real orders, from 96,000 customers and 3,095 sellers between 2016 and 2018, and turns nine linked tables into the analysis a marketplace analytics team would hand to leadership: validated KPIs, a delivery-to-review link, a seller scorecard, category economics, and customer behavior. It runs on Python, SQL and a Streamlit dashboard.

This is real, anonymized data, published by Olist on Kaggle.

---

## Key findings

1. **Orders more than doubled, but delivery didn't keep up.** Comparing January–August of each year, orders grew 135% and revenue 137%, while on-time delivery fell from 96.5% to 92.3% and the average review slipped from 4.14 to 4.09.
2. **A late delivery is what turns a customer against you.** On-time orders average 4.3 stars. Late orders average 2.3, and 54% of them get a 1-star review, against 7% for on-time orders. Past 8 days late, 70% are 1-star.
3. **Reviews follow delivery month by month.** Late deliveries spiked after Black Friday 2017 (12% late) and again in February–March 2018 (14–19%), and the average review fell to its lowest point, 3.75, in exactly those months.
4. **Delivery promises are heavily padded, and still missed.** The median order takes 10 days and is promised in 23, so it arrives 12 days early. Even with that cushion, 6.8% arrive late.
5. **The northeast is underserved.** Most sellers ship from São Paulo, and routes from there to Maranhão (19% late), Piauí (17%), Ceará and Bahia (13–14%) fail most. Rio de Janeiro is the biggest problem by volume: 8,048 orders from São Paulo, 14% late.
6. **Almost nobody comes back.** 97% of customers buy once. Repeat buyers bring just 5.6% of revenue, and those who return take a median of 41 days. For most customers, the first delivery is the whole relationship.
7. **Revenue is concentrated in a few sellers.** The top 1% of sellers (30 of them) bring 26% of revenue, and the top 10% bring 68%. Of the 201 sellers with 100+ orders, 15 are flagged for late deliveries, poor reviews, or both.
8. **Installments are how customers afford bigger baskets.** Card orders split into 7+ installments average R$303, almost four times the R$83 for cards paid in full.

## Recommendations

**For logistics and operations:** Fix the São Paulo to northeast and São Paulo to Rio routes first. That's where late deliveries concentrate, and a late delivery is the single biggest driver of 1-star reviews. Plan carrier capacity ahead of Black Friday and the post-holiday months, which is when late rates tripled.

**For the seller team:** Start with the 2 sellers flagged as both late and poorly rated, then the 13 on watch. With 68% of revenue coming from 10% of sellers, protecting those top sellers' service levels matters more than recruiting new ones.

**For customer experience:** Since 97% of buyers never return, a late first order costs the whole customer. A proactive delay message and a small credit when an order is about to miss its promised date is cheap compared with losing the customer.

**For category managers:** Office furniture has the lowest review score (3.6) and the highest shipping cost relative to price (25%). Bulky categories need either better carrier contracts or more realistic delivery promises.

---

## KPI definitions

| KPI | Definition |
|---|---|
| Revenue (GMV) | Sum of item prices, without freight. Measured from order items, not payments, since payments include installment interest and vouchers |
| Average order value | GMV ÷ orders with items |
| On time / late | Late = delivered on a later calendar day than the date promised to the customer. Delivered orders only |
| Repeat buyer | A person (`customer_unique_id`) with more than one completed order. Canceled and unavailable orders don't count |
| Seller review | Average review on that seller's single-seller orders only |

## Data quality

All 12 checks pass (`outputs/data_quality.md`). Two traps would have broken the analysis if missed.

**`customer_id` changes on every order.** Each order gets a new customer ID, so counting customers with it says nobody ever returns. The real person identifier is `customer_unique_id`, which finds 96,096 people and a 3.0% repeat rate.

**The first and last months are nearly empty.** September 2016 has 4 orders and September 2018 has 16. Left in, every trend would show a fake collapse at the end. Trends use complete months only, January 2017 to August 2018, and the year-over-year comparison uses the same eight months in each year.

Other checks resolve 547 orders with more than one review (the latest answer is kept), confirm that every order item links to a real order, product and seller, and confirm that payments match items plus freight on 99.6% of orders. They also flag 1,359 orders where the carrier picked up before payment was approved. That looks like a timestamp recording issue, and it's flagged but doesn't affect delivery times, which are measured from purchase to doorstep.

---

## The dashboard

`streamlit run app.py` opens seven tabs:

| Tab | Who it's for | What it shows |
|---|---|---|
| Overview | Leadership | Year-over-year KPIs, monthly orders, and late deliveries against reviews |
| Delivery & reviews | Operations | Reviews by how late the order was, delivery promise accuracy, worst states and routes |
| Sellers | Marketplace team | Seller scorecard with flags, revenue concentration |
| Categories | Category managers | Revenue share, shipping cost as a share of price, late rate and reviews |
| Customers & payments | CRM, marketing | Repeat buying, time to return, payment methods and installments |
| Data quality | Anyone checking the work | All 12 checks with results |
| SQL answers | Anyone | All eleven business questions with the query behind each |

## How it was built

| Step | File | What it does |
|---|---|---|
| 1 | `01_load_and_validate.py` | Loads the Olist tables, fixes customer identity and duplicate reviews, builds delivery fields, runs the quality checks |
| 2 | `02_run_sql.py` | Builds the tables in `sql/schema.sql` and answers the questions in `sql/questions.sql` with DuckDB |
| 3 | `app.py` | The Streamlit dashboard |

**Fair seller ratings.** A review belongs to a whole order. In an order with two sellers, there's no fair way to say which one earned the stars, so seller reviews use single-seller orders only.

**Like-for-like growth.** The data stops in August 2018, so year-over-year comparisons use January–August in both years. Comparing a full 2017 with eight months of 2018 would make the business look like it shrank.

**Revenue from items, not payments.** Payments include installment interest and vouchers, so revenue is measured from item prices, and payments are only used to study how people pay.

## Run it yourself

In Google Colab:

```python
!git clone https://github.com/vamsi93832/ecommerce-analytics.git
%cd ecommerce-analytics
!pip install -q -r requirements-pipeline.txt

!python 01_load_and_validate.py
!python 02_run_sql.py
```

Locally, run the same two scripts, then `streamlit run app.py`. The Olist tables ship with the repo, compressed, in `data/raw/`.

## Project structure

```
ecommerce-analytics/
├── 01_load_and_validate.py
├── 02_run_sql.py
├── app.py                        Streamlit dashboard
├── sql/
│   ├── schema.sql                tables and the shared delivered-orders view
│   └── questions.sql             eleven business questions
├── data/raw/                     the Olist tables, gzip compressed
├── outputs/                      data quality report and SQL answers (the dashboard reads these)
├── requirements.txt              dashboard only
└── requirements-pipeline.txt     adds DuckDB for the full pipeline
```

## Data source

Olist, [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), Kaggle, licensed CC BY-NC-SA 4.0. Real orders, anonymized by Olist. The geolocation table isn't used and isn't included.

---

Built by Vamsi Krishna Chirumalla · [Portfolio](https://vamsikrishnachirumalla.com) · [GitHub](https://github.com/vamsi93832)
