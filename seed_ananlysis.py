import pandas as pd
import mysql.connector
from sklearn.cluster import KMeans

# Function to safely get DB connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="its.pdv.0410",
        database="indumai"
    )

# Query
query = """
SELECT product_name, quantity, district
FROM orders
WHERE state='Maharashtra'
"""

# Use connection in a context manager style
try:
    db = get_db_connection()
    df = pd.read_sql(query, db)
finally:
    db.close()  # always close connection

# Group data region wise
region_data = df.groupby(['district','product_name'])['quantity'].sum().reset_index()

# Encode product names
region_data['product_code'] = region_data['product_name'].astype('category').cat.codes

# ML clustering
X = region_data[['product_code','quantity']]

kmeans = KMeans(n_clusters=3, random_state=42)  # always good to set random_state
region_data['cluster'] = kmeans.fit_predict(X)

print(region_data)
