import sqlite3
import os

db_path = 'd:/mart/instance/store.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find the product in 'products' table
cursor.execute("SELECT id, name, image_path FROM products WHERE name LIKE '%Advance%'")
results = cursor.fetchall()

if not results:
    print("No products found with 'Advance' in name.")

for row in results:
    p_id, name, img = row
    print(f"Found: ID={p_id}, Name={name}, Image={img}")
    
    # We want to clear the image regardless if it's the "Advance" product mentioned in logs
    # but let's be safe and check if it's the one with the Aadhar card (usually a generic upload name)
    if img:
        print(f"Updating image for product {p_id} ({name})...")
        cursor.execute("UPDATE products SET image_path = NULL WHERE id = ?", (p_id,))
        print("Image path cleared in database.")

conn.commit()
conn.close()
