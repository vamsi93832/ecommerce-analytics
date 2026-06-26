# =====================================================
# PROJECT 1: E-COMMERCE DATA GENERATION
# Simple, readable code with line-by-line comments
# =====================================================

# === STEP 1: Import libraries ===
import pandas as pd        # pd = tool for working with tables (Excel-like)
import numpy as np         # np = tool for working with numbers
from datetime import datetime, timedelta  # For handling dates
import random              # For random values

# Make random numbers same each time (for testing)
np.random.seed(42)
random.seed(42)

# === Print welcome message ===
print("\n" + "="*60)
print("CREATING E-COMMERCE SAMPLE DATA")
print("="*60 + "\n")


# ===== SECTION 1: CREATE CUSTOMERS =====
print("1️⃣  Creating 1,000 customers...")

num_customers = 1000  # How many customers

# Create customer data
customers = {
    # Column 1: Customer ID (1001, 1002, 1003... 2000)
    'customer_id': range(1001, 1001 + num_customers),
    
    # Column 2: Customer names (Customer_1, Customer_2... etc)
    'customer_name': [f'Customer_{i}' for i in range(1, num_customers + 1)],
    
    # Column 3: Emails
    'email': [f'customer{i}@email.com' for i in range(1, num_customers + 1)],
    
    # Column 4: Random country for each customer
    'country': np.random.choice(['USA', 'Canada', 'UK', 'Germany', 'France', 'India'], num_customers),
    
    # Column 5: Random state
    'state': np.random.choice(['NY', 'CA', 'TX', 'FL', 'PA', 'IL', 'OH', 'GA'], num_customers),
    
    # Column 6: Signup date (random date in 2023)
    'signup_date': [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(num_customers)],
    
    # Column 7: Total money spent ($500 average, range 0-5000)
    'customer_lifetime_value': np.random.normal(500, 200, num_customers).clip(0, 5000),
    
    # Column 8: Number of orders (average 5)
    'total_orders': np.random.poisson(5, num_customers) + 1
}

# Convert to table (DataFrame)
df_customers = pd.DataFrame(customers)

# Convert dates to proper format
df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date'])

# Round money to 2 decimal places
df_customers['customer_lifetime_value'] = df_customers['customer_lifetime_value'].round(2)

# Save as CSV file
df_customers.to_csv('customers.csv', index=False)
print(f"   ✓ Created {len(df_customers)} customers\n")


# ===== SECTION 2: CREATE PRODUCTS =====
print("2️⃣  Creating product list...")

# List of products: (Name, Price, Category)
products = [
    ('Laptop', 1200, 'Electronics'),
    ('Monitor', 350, 'Electronics'),
    ('Keyboard', 100, 'Electronics'),
    ('Mouse', 45, 'Electronics'),
    ('Headphones', 120, 'Electronics'),
    ('USB Cable', 15, 'Accessories'),
    ('Phone', 800, 'Electronics'),
    ('Tablet', 500, 'Electronics'),
    ('Smartwatch', 300, 'Electronics'),
    ('Camera', 600, 'Electronics'),
    ('Charger', 35, 'Accessories'),
    ('Screen Protector', 12, 'Accessories'),
    ('Phone Case', 25, 'Accessories'),
    ('SSD Drive', 150, 'Storage'),
    ('RAM Memory', 100, 'Components'),
]

# Convert to table
df_products = pd.DataFrame(products, columns=['product_name', 'price', 'category'])

# Add product IDs (2001, 2002, 2003... etc)
df_products['product_id'] = range(2001, 2001 + len(df_products))

# Add random stock amount for each product (10-500 items)
df_products['stock_quantity'] = np.random.randint(10, 500, len(df_products))

# Reorder columns nicely
df_products = df_products[['product_id', 'product_name', 'price', 'category', 'stock_quantity']]

# Save as CSV
df_products.to_csv('products.csv', index=False)
print(f"   ✓ Created {len(df_products)} products\n")


# ===== SECTION 3: CREATE ORDERS =====
print("3️⃣  Creating 5,000 orders...")

num_orders = 5000  # How many orders

# Create random dates (Jan-Jun 2024)
order_dates = [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 180)) for _ in range(num_orders)]

# Create order data
orders = {
    # Column 1: Order ID (3001, 3002, 3003... etc)
    'order_id': range(3001, 3001 + num_orders),
    
    # Column 2: Random customer (pick from customer list)
    'customer_id': np.random.choice(df_customers['customer_id'], num_orders),
    
    # Column 3: Order date
    'order_date': order_dates,
    
    # Column 4: Order status
    # 75% = Completed, 15% = Pending, 5% = Cancelled, 5% = Shipped
    'order_status': np.random.choice(
        ['Completed', 'Pending', 'Cancelled', 'Shipped'], 
        num_orders, 
        p=[0.75, 0.15, 0.05, 0.05]
    ),
    
    # Column 5: Order amount ($50 to $2000)
    'total_order_value': np.random.uniform(50, 2000, num_orders).round(2),
    
    # Column 6: Payment method
    'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Apple Pay'], num_orders),
}

# Convert to table
df_orders = pd.DataFrame(orders)

# Make sure dates are correct format
df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])

# Save as CSV
df_orders.to_csv('orders.csv', index=False)
print(f"   ✓ Created {len(df_orders)} orders\n")


# ===== SECTION 4: CREATE ORDER ITEMS =====
print("4️⃣  Creating order items (products in each order)...")

# Empty list to store items
items_list = []

# For each order, add 1-5 random products
for row_index, order_row in df_orders.iterrows():
    # Random number of items per order (1-5)
    num_items = random.randint(1, 5)
    
    # Add each item
    for _ in range(num_items):
        # Pick random product
        product = df_products.sample(1).iloc[0]
        
        # Random quantity (1-3)
        qty = random.randint(1, 3)
        
        # Create item entry
        item = {
            'order_item_id': len(items_list) + 4001,        # Item ID
            'order_id': order_row['order_id'],              # Which order
            'product_id': product['product_id'],            # Which product
            'product_name': product['product_name'],        # Product name
            'quantity': qty,                                # How many
            'unit_price': product['price'],                 # Price per item
            'line_total': (product['price'] * qty)          # Total for this item
        }
        
        # Add to list
        items_list.append(item)

# Convert to table
df_items = pd.DataFrame(items_list)

# Save as CSV
df_items.to_csv('order_items.csv', index=False)
print(f"   ✓ Created {len(df_items)} order items\n")


# ===== SECTION 5: CREATE REVIEWS =====
print("5️⃣  Creating customer reviews...")

# Empty list for reviews
reviews_list = []

# Check each order
for row_index, order in df_orders.iterrows():
    # Only add review if order is completed (and 60% probability)
    if random.random() > 0.4 and order['order_status'] == 'Completed':
        
        # Review date = 5-30 days after order
        review_date = order['order_date'] + timedelta(days=random.randint(5, 30))
        
        # Create review
        review = {
            'review_id': len(reviews_list) + 5001,          # Review ID
            'order_id': order['order_id'],                  # Which order
            'customer_id': order['customer_id'],            # Who reviewed
            'product_id': np.random.choice(df_products['product_id']),  # Which product
            'rating': random.randint(1, 5),                 # Rating (1-5 stars)
            'review_text': random.choice([                  # What they wrote
                'Great product!', 'Good quality', 'Fast delivery', 'Excellent value',
                'Not satisfied', 'Average', 'Highly recommend', 'Poor quality'
            ]),
            'review_date': review_date,                     # When posted
        }
        
        # Add to list
        reviews_list.append(review)

# Convert to table
df_reviews = pd.DataFrame(reviews_list)

# Make sure dates are correct format
df_reviews['review_date'] = pd.to_datetime(df_reviews['review_date'])

# Save as CSV
df_reviews.to_csv('reviews.csv', index=False)
print(f"   ✓ Created {len(df_reviews)} reviews\n")


# ===== SUMMARY =====
print("="*60)
print("✅ SUCCESS! ALL DATA CREATED")
print("="*60)
print(f"\n📊 Summary:")
print(f"   • Customers:    {len(df_customers):,}")
print(f"   • Products:     {len(df_products):,}")
print(f"   • Orders:       {len(df_orders):,}")
print(f"   • Order Items:  {len(df_items):,}")
print(f"   • Reviews:      {len(df_reviews):,}")
print(f"   • TOTAL:        {len(df_customers) + len(df_products) + len(df_orders) + len(df_items) + len(df_reviews):,} records")

print(f"\n📁 Files created:")
print(f"   • customers.csv")
print(f"   • products.csv")
print(f"   • orders.csv")
print(f"   • order_items.csv")
print(f"   • reviews.csv")
print(f"\n✨ Ready for analysis!")
print("="*60 + "\n")
