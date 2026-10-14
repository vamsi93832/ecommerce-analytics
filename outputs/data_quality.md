# Data quality report

Source: Olist Brazilian E-Commerce Public Dataset (Kaggle), real anonymized marketplace orders, 2016-2018.

| Check | Result | Detail |
|---|---|---|
| One row per order | Pass | 99,441 orders, 99,441 unique IDs |
| Customers counted as people, not orders | Pass | customer_id never repeats (max 1 order each), so it would show 0% repeat buyers. customer_unique_id finds 96,096 real people; 3.0% of buyers completed more than one order |
| Every order item links to a real order, product and seller | Pass | 112,650 items checked against orders, products and sellers |
| Duplicate reviews resolved | Pass | 814 repeated review IDs and 547 orders with more than one review; the latest answer per order is kept |
| Review scores in range 1-5 | Pass | scores range 1-5 |
| Partial months kept out of trends | Pass | 2017-01 to 2018-08 used for trends. Left out: 2016-09 (4 orders), 2016-10 (324 orders), 2016-12 (1 order), 2018-09 (16 orders), 2018-10 (4 orders) |
| Delivered orders without a delivery date | Pass | 8 orders marked delivered have no delivery date; left out of delivery metrics |
| No order delivered before it was bought | Pass | 0 orders fail |
| Carrier pickup before payment approval | Pass | 1,359 orders show the carrier picking up before payment was approved, likely a timestamp recording issue. Flagged only; delivery speed is measured from purchase to doorstep, so it isn't affected |
| Payments match items plus freight | Pass | 99.6% of 98,665 orders match to the cent; 249 are off by more than R$1 (likely interest on installment plans). Revenue is measured from item prices, not payments |
| Orders with no items | Pass | 775 orders have no items, mostly {'unavailable': 603, 'canceled': 164, 'created': 5}; they carry no revenue |
| Every category has an English name | Pass | 610 products have no category (labeled 'unknown'); 2 categories missing from Olist's translation table were added by hand |
