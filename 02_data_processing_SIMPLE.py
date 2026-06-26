# =====================================================
# PROJECT 1: E-COMMERCE DATA PROCESSING (ETL PIPELINE)
# Simple, readable code with detailed comments
# =====================================================

# === Import libraries ===
import pandas as pd  # For working with data tables
import numpy as np   # For working with numbers
from datetime import datetime  # For handling dates
import warnings  # For hiding warnings
warnings.filterwarnings('ignore')  # Hide warning messages

print("\n" + "="*80)
print("E-COMMERCE DATA PROCESSING PIPELINE")
print("="*80)

# ============================================================================
# STEP 1: LOAD ALL CSV FILES
# ============================================================================
print("\n📂 STEP 1: Loading data files...")
print("-"*80)

try:
    # Load customer data
    customers = pd.read_csv('customers.csv')
    print(f"✓ Loaded customers.csv - {len(customers)} records")
    
    # Load product data
    products = pd.read_csv('products.csv')
    print(f"✓ Loaded products.csv - {len(products)} records")
    
    # Load order data
    orders = pd.read_csv('orders.csv')
    print(f"✓ Loaded orders.csv - {len(orders)} records")
    
    # Load order items data
    order_items = pd.read_csv('order_items.csv')
    print(f"✓ Loaded order_items.csv - {len(order_items)} records")
    
    # Load reviews data
    reviews = pd.read_csv('reviews.csv')
    print(f"✓ Loaded reviews.csv - {len(reviews)} records")
    
except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    print("Make sure all CSV files are in the same folder!")
    exit()

# Convert date columns to proper date format
customers['signup_date'] = pd.to_datetime(customers['signup_date'])
orders['order_date'] = pd.to_datetime(orders['order_date'])
reviews['review_date'] = pd.to_datetime(reviews['review_date'])

print(f"✓ All files loaded successfully!\n")

# ============================================================================
# STEP 2: CLEAN AND VALIDATE DATA
# ============================================================================
print("🧹 STEP 2: Cleaning data...")
print("-"*80)

# Remove duplicate orders (keep only unique orders)
orders_before = len(orders)
orders = orders.drop_duplicates(subset=['order_id'])
duplicates_removed = orders_before - len(orders)
print(f"✓ Removed {duplicates_removed} duplicate orders")

# Keep only completed or shipped orders (remove cancelled/pending)
orders_completed = orders[orders['order_status'].isin(['Completed', 'Shipped'])].copy()
print(f"✓ Filtered to {len(orders_completed)} completed/shipped orders")

# Check for missing values
missing_customers = customers.isnull().sum().sum()
missing_orders = orders_completed.isnull().sum().sum()
print(f"✓ Missing values - Customers: {missing_customers}, Orders: {missing_orders}")

# ============================================================================
# STEP 3: MERGE DATA (JOIN TABLES)
# ============================================================================
print("\n🔗 STEP 3: Merging data tables...")
print("-"*80)

# Join orders with order items
merged = orders_completed.merge(order_items, on='order_id', how='left')
print(f"✓ Merged orders with items - {len(merged)} rows")

# Join with customers
merged = merged.merge(customers, on='customer_id', how='left')
print(f"✓ Added customer information - {len(merged)} rows")

# Join with products
merged = merged.merge(products[['product_id', 'category']], on='product_id', how='left')
print(f"✓ Added product categories - {len(merged)} rows")

# ============================================================================
# STEP 4: CREATE TIME DIMENSIONS
# ============================================================================
print("\n⏰ STEP 4: Creating time dimensions...")
print("-"*80)

# Extract year from order date
merged['order_year'] = merged['order_date'].dt.year

# Extract month from order date
merged['order_month'] = merged['order_date'].dt.month

# Extract quarter from order date
merged['order_quarter'] = merged['order_date'].dt.quarter

# Extract week from order date
merged['order_week'] = merged['order_date'].dt.isocalendar().week

# Extract day of week (Monday, Tuesday, etc.)
merged['day_of_week'] = merged['order_date'].dt.day_name()

print(f"✓ Added time dimensions (year, month, quarter, week, day)")

# ============================================================================
# STEP 5: CALCULATE BUSINESS METRICS
# ============================================================================
print("\n📊 STEP 5: Calculating metrics...")
print("-"*80)

# Calculate profit margin (assume 30% cost)
merged['profit_margin'] = ((merged['line_total'] - (merged['unit_price'] * 0.3)) / merged['line_total'] * 100).round(2)

# Calculate days since customer signed up
merged['days_since_signup'] = (merged['order_date'] - merged['signup_date']).dt.days

print(f"✓ Calculated profit margins")
print(f"✓ Calculated customer age (days since signup)")

# ============================================================================
# STEP 6: CREATE AGGREGATED DATASETS
# ============================================================================
print("\n📈 STEP 6: Creating analytical datasets...")
print("-"*80)

# --- DATASET 1: Daily Sales Summary ---
daily_sales = merged.groupby('order_date').agg({
    'order_id': 'nunique',          # Count unique orders
    'line_total': 'sum',            # Total revenue
    'quantity': 'sum',              # Total items sold
    'customer_id': 'nunique'        # Unique customers
}).reset_index()

# Rename columns for clarity
daily_sales.columns = ['date', 'total_orders', 'revenue', 'units_sold', 'unique_customers']

# Round revenue
daily_sales['revenue'] = daily_sales['revenue'].round(2)

# Calculate average order value
daily_sales['avg_order_value'] = (daily_sales['revenue'] / daily_sales['total_orders']).round(2)

# Save to file
daily_sales.to_csv('daily_sales_summary.csv', index=False)
print(f"✓ Created daily_sales_summary.csv ({len(daily_sales)} records)")

# --- DATASET 2: Product Performance ---
product_performance = merged.groupby(['product_id', 'product_name']).agg({
    'order_id': 'nunique',          # How many times ordered
    'quantity': 'sum',              # Total units sold
    'line_total': 'sum',            # Total revenue
    'rating': 'mean'                # Average rating
}).reset_index()

# Rename columns
product_performance.columns = ['product_id', 'product_name', 'orders_count', 'units_sold', 'revenue', 'avg_rating']

# Round values
product_performance['revenue'] = product_performance['revenue'].round(2)
product_performance['avg_rating'] = product_performance['avg_rating'].round(2)

# Sort by revenue (best sellers first)
product_performance = product_performance.sort_values('revenue', ascending=False)

# Save to file
product_performance.to_csv('product_performance.csv', index=False)
print(f"✓ Created product_performance.csv ({len(product_performance)} records)")

# --- DATASET 3: Category Performance ---
category_performance = merged.groupby('category').agg({
    'order_id': 'nunique',          # Orders per category
    'quantity': 'sum',              # Units sold
    'line_total': 'sum',            # Revenue
    'customer_id': 'nunique'        # Unique customers
}).reset_index()

# Rename columns
category_performance.columns = ['category', 'orders_count', 'units_sold', 'revenue', 'unique_customers']

# Round revenue
category_performance['revenue'] = category_performance['revenue'].round(2)

# Calculate average order value by category
category_performance['avg_order_value'] = (category_performance['revenue'] / category_performance['orders_count']).round(2)

# Save to file
category_performance.to_csv('category_performance.csv', index=False)
print(f"✓ Created category_performance.csv ({len(category_performance)} records)")

# --- DATASET 4: Monthly Sales Trends ---
# Group by month and calculate metrics
monthly_sales = merged.groupby(merged['order_date'].dt.to_period('M')).agg({
    'order_id': 'nunique',          # Orders per month
    'line_total': 'sum',            # Revenue
    'quantity': 'sum',              # Units sold
    'customer_id': 'nunique'        # Unique customers
}).reset_index()

# Rename columns
monthly_sales.columns = ['month', 'total_orders', 'revenue', 'units_sold', 'unique_customers']

# Convert month to string
monthly_sales['month'] = monthly_sales['month'].astype(str)

# Round revenue
monthly_sales['revenue'] = monthly_sales['revenue'].round(2)

# Save to file
monthly_sales.to_csv('monthly_sales_trend.csv', index=False)
print(f"✓ Created monthly_sales_trend.csv ({len(monthly_sales)} records)")

# --- DATASET 5: Customer Metrics ---
customer_metrics = merged.groupby('customer_id').agg({
    'customer_name': 'first',       # Get customer name
    'country': 'first',             # Get country
    'order_id': 'nunique',          # Count of orders
    'line_total': 'sum',            # Total spent
    'quantity': 'sum',              # Total items
    'signup_date': 'first',         # When signed up
    'days_since_signup': 'max'      # Age of customer
}).reset_index()

# Rename columns
customer_metrics.columns = ['customer_id', 'customer_name', 'country', 'purchase_count', 'total_spent', 'total_items', 'signup_date', 'customer_age_days']

# Round money
customer_metrics['total_spent'] = customer_metrics['total_spent'].round(2)

# Calculate average order value per customer
customer_metrics['avg_order_value'] = (customer_metrics['total_spent'] / customer_metrics['purchase_count']).round(2)

# Segment customers by spending (Bronze/Silver/Gold)
customer_metrics['customer_segment'] = pd.cut(
    customer_metrics['total_spent'],
    bins=[0, 500, 1500, float('inf')],
    labels=['Bronze', 'Silver', 'Gold']
)

# Save to file
customer_metrics.to_csv('customer_metrics.csv', index=False)
print(f"✓ Created customer_metrics.csv ({len(customer_metrics)} records)")

# --- DATASET 6: Geographic Analysis ---
geographic = merged.groupby(['country', 'state']).agg({
    'order_id': 'nunique',          # Orders per region
    'line_total': 'sum',            # Revenue
    'customer_id': 'nunique'        # Customers
}).reset_index()

# Rename columns
geographic.columns = ['country', 'state', 'orders_count', 'revenue', 'unique_customers']

# Round revenue
geographic['revenue'] = geographic['revenue'].round(2)

# Save to file
geographic.to_csv('geographic_analysis.csv', index=False)
print(f"✓ Created geographic_analysis.csv ({len(geographic)} records)")

# --- DATASET 7: Review Analysis ---
review_summary = reviews.merge(products[['product_id', 'product_name']], on='product_id', how='left')
review_summary = review_summary.groupby(['product_id', 'product_name']).agg({
    'rating': ['mean', 'count'],    # Average rating and count
    'review_id': 'nunique'          # Number of reviews
}).reset_index()

# Flatten column names
review_summary.columns = ['product_id', 'product_name', 'avg_rating', 'total_reviews', 'unique_reviews']

# Round rating
review_summary['avg_rating'] = review_summary['avg_rating'].round(2)

# Save to file
review_summary.to_csv('review_analysis.csv', index=False)
print(f"✓ Created review_analysis.csv ({len(review_summary)} records)")

# ============================================================================
# STEP 7: SUMMARY AND KEY METRICS
# ============================================================================
print("\n" + "="*80)
print("✅ PROCESSING COMPLETE - KEY METRICS")
print("="*80)

# Calculate key metrics
total_revenue = merged['line_total'].sum()
total_orders = merged['order_id'].nunique()
total_customers = merged['customer_id'].nunique()
avg_order_value = total_revenue / total_orders
top_product = product_performance.iloc[0]['product_name']
top_category = category_performance.iloc[0]['category']

print(f"\n💰 Revenue Metrics:")
print(f"   • Total Revenue: ${total_revenue:,.2f}")
print(f"   • Total Orders: {total_orders:,}")
print(f"   • Average Order Value: ${avg_order_value:,.2f}")

print(f"\n👥 Customer Metrics:")
print(f"   • Total Customers: {total_customers:,}")
print(f"   • Total Items Sold: {merged['quantity'].sum():,}")

print(f"\n📊 Top Performers:")
print(f"   • Top Product: {top_product}")
print(f"   • Top Category: {top_category}")

print(f"\n👤 Customer Segments:")
segment_dist = customer_metrics['customer_segment'].value_counts()
for segment, count in segment_dist.items():
    percentage = (count / len(customer_metrics)) * 100
    print(f"   • {segment}: {count:,} customers ({percentage:.1f}%)")

# ============================================================================
# STEP 8: FILES CREATED
# ============================================================================
print(f"\n📁 Files Created (Ready for Power BI/Tableau):")
print(f"   1. daily_sales_summary.csv - Daily metrics")
print(f"   2. product_performance.csv - Product analysis")
print(f"   3. category_performance.csv - Category analysis")
print(f"   4. monthly_sales_trend.csv - Monthly trends")
print(f"   5. customer_metrics.csv - Customer segmentation")
print(f"   6. geographic_analysis.csv - Geographic insights")
print(f"   7. review_analysis.csv - Review statistics")

print(f"\n✨ Ready for visualization in Power BI or Tableau!")
print("="*80 + "\n")
