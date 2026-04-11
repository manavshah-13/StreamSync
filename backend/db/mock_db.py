import json
import random
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.redis_client import get_redis_sync

CATEGORIES = ['Electronics', 'Apparel', 'Home', 'Sports', 'Beauty', 'Toys']
NAMES = [
  'Pro Wireless Headphones', 'Smart 4K Monitor', 'Ergonomic Keyboard',
  'Running Shoes Elite', 'Yoga Mat Premium', 'Coffee Maker Deluxe',
  'Gaming Chair X500', 'LED Desk Lamp', 'Bluetooth Speaker',
  'Mechanical Watch', 'Leather Backpack', 'Noise Cancelling Buds',
  'Ultra-Wide Webcam', 'Standing Desk', 'Portable Charger 20K',
  'Silk Pillowcase Set', 'Kitchen Scale Pro', 'Foam Roller Set',
  'Smart Water Bottle', 'Resistance Bands Kit',
]

def generate_mock_products():
    client = get_redis_sync()
    
    for i in range(20):
        prod_id = f"prod-{i + 1}"
        base_price = round(19.99 + i * 12.5 + random.random() * 30, 2)
        
        product_data = {
            "id": prod_id,
            "name": NAMES[i % len(NAMES)],
            "category": CATEGORIES[i % len(CATEGORIES)],
            "base_price": base_price,
            "current_price": base_price,
            "rating": round(3.5 + random.random() * 1.5, 1),
            "reviewCount": int(50 + random.random() * 900),
            "demandVelocity": random.randint(20, 100),
            "brand": ['Sony', 'Samsung', 'Apple', 'Nike', 'Logitech', 'IKEA'][i % 6],
            "description": f"High-quality {NAMES[i % len(NAMES)].lower()} engineered for peak performance and daily comfort. StreamSync dynamically adjusts its price based on real-time demand signals.",
            "specs": json.dumps({
                "Weight": f"{round(0.3 + random.random() * 2, 1)} kg",
                "Warranty": "2 years",
                "Origin": "Imported"
            }),
            "image": ""
        }
        
        client.hset(f"product:{prod_id}", mapping=product_data)
        client.sadd("products:all", prod_id)
        
    print("Mock database populated successfully into Redis Hashes.")

if __name__ == "__main__":
    generate_mock_products()
