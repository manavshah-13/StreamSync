import sys, os
import json
from sqlalchemy.orm import Session

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal, engine
from models.schema import Product, Base
from db.mock_db import PRODUCTS_DATA

def seed_products():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Product).count() > 0:
            print("Products already seeded. Skipping...")
            return

        print(f"Seeding {len(PRODUCTS_DATA)} products into PostgreSQL...")
        
        for i, p_info in enumerate(PRODUCTS_DATA):
            prod_id = f"prod-{i + 1}"
            
            # Use original price or calculate one
            base_price = p_info.get("price", 1000)
            
            new_product = Product(
                id=prod_id,
                name=p_info["name"],
                category=p_info["category"],
                base_price=float(base_price),
                current_price=float(base_price),
                rating=float(p_info.get("rating", 4.5)),
                review_count=int(50 + (i * 7) % 500),
                demand_velocity=int(20 + (i * 3) % 80),
                brand=p_info.get("brand", "Generic"),
                description=p_info.get("description", ""),
                specs=json.loads(json.dumps({
                    "Weight": f"{round(0.5 + (i % 5)*0.4, 1)} kg",
                    "Warranty": "2 years",
                    "Color": p_info.get("color", "N/A"),
                    "Material": p_info.get("material", "N/A")
                })),
                image=p_info.get("image", ""),
                color=p_info.get("color", ""),
                material=p_info.get("material", ""),
                style=p_info.get("style", ""),
                tags=p_info.get("tags", "")
            )
            db.add(new_product)
        
        db.commit()
        print("Success: PostgreSQL seeding complete!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_products()
