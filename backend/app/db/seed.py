import sys
import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

# Ensure backend directory is in python module path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from db.database import SessionLocal, engine
from models.schema import Product, Base
from app.ml.embedder import ProductEmbedder
from app.ml.indexer import build_product_text_blob

SEED_PRODUCTS = [
    {
        "id": "seed-prod-1",
        "name": "Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "base_price": 19999.0,
        "brand": "AcousticPro",
        "description": "Experience premium sound quality with these wireless noise-canceling headphones. Featuring active noise cancellation (ANC), 40-hour battery life, fast charging, and plush memory foam earcups for all-day comfort. Seamlessly connect via Bluetooth 5.2 to enjoy high-fidelity audio.",
        "color": "black",
        "material": "plastic",
        "style": "wireless",
        "tags": "headphones,audio,wireless,noise-canceling,anc,bluetooth",
        "rating": 4.8,
        "review_count": 142,
        "demand_velocity": 85,
        "image": "/images/noise_cancelling_buds.png",
        "specs": {
            "Weight": "0.25 kg",
            "Warranty": "2 years",
            "Battery Life": "40 hours",
            "Bluetooth": "5.2"
        }
    },
    {
        "id": "seed-prod-2",
        "name": "Ergonomic Mechanical Keyboard",
        "category": "Electronics",
        "base_price": 12500.0,
        "brand": "KeyForge",
        "description": "Boost your typing productivity and comfort with this ergonomic mechanical keyboard. It features hot-swappable tactile brown switches, a split-key layout, customizable RGB backlighting, and a cushioned wrist rest. Designed to reduce wrist strain during long coding or gaming sessions.",
        "color": "grey",
        "material": "aluminium",
        "style": "ergonomic",
        "tags": "keyboard,mechanical,ergonomic,rgb,gaming,coding",
        "rating": 4.7,
        "review_count": 98,
        "demand_velocity": 65,
        "image": "/images/mechanical_watch.png",
        "specs": {
            "Weight": "0.95 kg",
            "Warranty": "1 year",
            "Switches": "Tactile Brown",
            "Layout": "Split Ergonomic"
        }
    },
    {
        "id": "seed-prod-3",
        "name": "Ultra-Wide Curved Gaming Monitor",
        "category": "Electronics",
        "base_price": 45000.0,
        "brand": "PixelPerfect",
        "description": "Immerse yourself in stunning visuals with this 34-inch ultra-wide curved gaming monitor. Boasting a WQHD resolution, 144Hz refresh rate, 1ms response time, and AMD FreeSync Premium support. The 1500R curve provides an expansive field of view and reduces eye strain.",
        "color": "black",
        "material": "plastic",
        "style": "professional",
        "tags": "monitor,curved,gaming,display,ultrawide,144hz",
        "rating": 4.9,
        "review_count": 76,
        "demand_velocity": 90,
        "image": "/images/ultra_wide_webcam.png",
        "specs": {
            "Weight": "6.8 kg",
            "Warranty": "3 years",
            "Resolution": "3440 x 1440",
            "Refresh Rate": "144Hz"
        }
    },
    {
        "id": "seed-prod-4",
        "name": "Portable Smart Projector",
        "category": "Electronics",
        "base_price": 29999.0,
        "brand": "Lumina",
        "description": "Bring the theater home or on the go with this compact, portable smart projector. Features 1080p Full HD resolution, built-in Android TV with access to all streaming apps, 360-degree auto-keystone correction, and dual Harman Kardon speakers. Perfect for movie nights and presentations.",
        "color": "white",
        "material": "plastic",
        "style": "portable",
        "tags": "projector,smart,portable,theater,hd,streaming",
        "rating": 4.6,
        "review_count": 64,
        "demand_velocity": 55,
        "image": "/images/led_desk_lamp.png",
        "specs": {
            "Weight": "1.2 kg",
            "Warranty": "2 years",
            "Brightness": "800 ANSI Lumens",
            "Resolution": "1080p"
        }
    },
    {
        "id": "seed-prod-5",
        "name": "Multi-Device Wireless Mouse",
        "category": "Electronics",
        "base_price": 4200.0,
        "brand": "Logitech",
        "description": "Navigate multiple computers seamlessly with this advanced multi-device wireless mouse. Features an ergonomic thumb rest, hyper-fast scroll wheel, customizable buttons, and a high-precision sensor that works on any surface, including glass. Connects to up to 3 devices simultaneously.",
        "color": "charcoal",
        "material": "plastic",
        "style": "premium",
        "tags": "mouse,wireless,multidevice,ergonomic,office,logitech",
        "rating": 4.5,
        "review_count": 210,
        "demand_velocity": 70,
        "image": "/images/ultra_wide_webcam.png",
        "specs": {
            "Weight": "0.14 kg",
            "Warranty": "1 year",
            "DPI": "4000",
            "Battery": "Rechargeable Li-Po"
        }
    },
    {
        "id": "seed-prod-6",
        "name": "Premium Running Shoes",
        "category": "Apparel",
        "base_price": 8999.0,
        "brand": "SwiftStride",
        "description": "Engineered for speed and endurance, these premium running shoes offer unmatched comfort and energy return. Featuring a highly breathable mesh upper, reactive foam midsole cushioning, and a durable rubber outsole for superior grip on all surfaces. Lightweight design reduces foot fatigue.",
        "color": "blue",
        "material": "fabric",
        "style": "casual",
        "tags": "shoes,running,sneakers,apparel,fitness,sportswear",
        "rating": 4.7,
        "review_count": 315,
        "demand_velocity": 80,
        "image": "/images/leather_backpack.png",
        "specs": {
            "Weight": "0.58 kg",
            "Warranty": "6 months",
            "Material": "Recycled Polyester Mesh",
            "Type": "Neutral Cushioning"
        }
    },
    {
        "id": "seed-prod-7",
        "name": "Waterproof Windbreaker Jacket",
        "category": "Apparel",
        "base_price": 5499.0,
        "brand": "ArcticShield",
        "description": "Stay dry and warm during outdoor adventures with this waterproof, windproof windbreaker jacket. Features a lightweight, breathable shell, fully taped seams, adjustable hood and cuffs, and multiple secure zippered pockets. Packs down small for convenient travel storage.",
        "color": "olive",
        "material": "nylon",
        "style": "outdoor",
        "tags": "jacket,waterproof,windbreaker,apparel,outdoor,hiking",
        "rating": 4.6,
        "review_count": 184,
        "demand_velocity": 60,
        "image": "/images/leather_backpack.png",
        "specs": {
            "Weight": "0.38 kg",
            "Warranty": "1 year",
            "Material": "Ripstop Nylon",
            "Waterproofing": "10000mm"
        }
    },
    {
        "id": "seed-prod-8",
        "name": "Merino Wool Hiking Socks",
        "category": "Apparel",
        "base_price": 1499.0,
        "brand": "TrailBlaze",
        "description": "Keep your feet warm, dry, and blister-free with these premium merino wool hiking socks. Knit with high-density cushioning underfoot for impact protection, breathable ventilation channels, and reinforced heel/toe zones for extreme durability. Naturally moisture-wicking and odor-resistant.",
        "color": "charcoal",
        "material": "wool",
        "style": "outdoor",
        "tags": "socks,wool,merino,apparel,hiking,outdoor",
        "rating": 4.9,
        "review_count": 250,
        "demand_velocity": 50,
        "image": "/images/silk_pillowcase_set.png",
        "specs": {
            "Weight": "0.08 kg",
            "Warranty": "Lifetime Guarantee",
            "Material": "65% Merino Wool, 33% Nylon, 2% Spandex"
        }
    },
    {
        "id": "seed-prod-9",
        "name": "Slim-Fit Stretch Denim Jeans",
        "category": "Apparel",
        "base_price": 3999.0,
        "brand": "UrbanDenim",
        "description": "Upgrade your casual wardrobe with these classic slim-fit stretch denim jeans. Crafted from mid-weight cotton-stretch denim that moves with you for ultimate comfort. Features a modern five-pocket design, zip fly, and a clean, versatile wash suitable for day or night wear.",
        "color": "blue",
        "material": "cotton",
        "style": "casual",
        "tags": "jeans,denim,apparel,pants,casual,clothing",
        "rating": 4.4,
        "review_count": 195,
        "demand_velocity": 75,
        "image": "/images/leather_backpack.png",
        "specs": {
            "Weight": "0.6 kg",
            "Warranty": "1 year",
            "Material": "98% Cotton, 2% Elastane",
            "Fit": "Slim"
        }
    },
    {
        "id": "seed-prod-10",
        "name": "Polarized Sports Sunglasses",
        "category": "Apparel",
        "base_price": 2800.0,
        "brand": "LunaShade",
        "description": "Protect your eyes and enhance visibility during outdoor workouts with these polarized sports sunglasses. Features 100% UV400 protection, impact-resistant polarized lenses to reduce glare, and a lightweight, wrap-around frame that stays secure during high-impact movement.",
        "color": "black",
        "material": "acetate",
        "style": "modern",
        "tags": "sunglasses,polarized,eyewear,apparel,sports,running",
        "rating": 4.5,
        "review_count": 128,
        "demand_velocity": 80,
        "image": "/images/silk_pillowcase_set.png",
        "specs": {
            "Weight": "0.03 kg",
            "Warranty": "1 year",
            "Lens Type": "Polarized UV400",
            "Frame Material": "TR90 Flexible Nylon"
        }
    },
    {
        "id": "seed-prod-11",
        "name": "Heavy-Duty Resistance Bands Kit",
        "category": "Fitness",
        "base_price": 2499.0,
        "brand": "IronCore",
        "description": "Bring the gym home with this comprehensive heavy-duty resistance bands kit. Includes 5 stackable latex bands ranging from 10 to 50 lbs of resistance, cushioned foam handles, comfortable ankle straps, a door anchor, and a compact carrying pouch. Perfect for strength training, physical therapy, and home workouts.",
        "color": "multi",
        "material": "rubber",
        "style": "fitness",
        "tags": "resistance-bands,workout,gym,fitness,home-gym,strength",
        "rating": 4.8,
        "review_count": 412,
        "demand_velocity": 95,
        "image": "/images/resistance_bands_kit.png",
        "specs": {
            "Weight": "0.85 kg",
            "Warranty": "2 years",
            "Resistance Range": "10 - 150 lbs total",
            "Material": "100% Natural Latex"
        }
    },
    {
        "id": "seed-prod-12",
        "name": "High-Density Foam Roller",
        "category": "Fitness",
        "base_price": 1899.0,
        "brand": "GlidePro",
        "description": "Relieve muscle soreness and improve recovery time with this high-density foam roller. Made from premium molded polypropylene foam that maintains shape under heavy use. Ideal for physical therapy, myofascial release, deep tissue massage, and core stability exercises.",
        "color": "black",
        "material": "foam",
        "style": "fitness",
        "tags": "foam-roller,recovery,massage,fitness,muscle,stretching",
        "rating": 4.6,
        "review_count": 305,
        "demand_velocity": 55,
        "image": "/images/foam_roller_set.png",
        "specs": {
            "Weight": "0.4 kg",
            "Warranty": "1 year",
            "Length": "18 inches",
            "Firmness": "Extra Firm"
        }
    },
    {
        "id": "seed-prod-13",
        "name": "Adjustable Competition Kettlebell",
        "category": "Fitness",
        "base_price": 9999.0,
        "brand": "PowerBell",
        "description": "Optimize your strength training setup with this versatile adjustable competition kettlebell. Consolidates multiple weights into a single solid-steel design, adjusting from 12 kg to 32 kg in 2 kg increments. Heavy-duty locking mechanism ensures plates stay silent and secure.",
        "color": "black",
        "material": "metal",
        "style": "fitness",
        "tags": "kettlebell,adjustable,weights,fitness,strength,gym",
        "rating": 4.7,
        "review_count": 92,
        "demand_velocity": 70,
        "image": "/images/resistance_bands_kit.png",
        "specs": {
            "Weight": "32 kg max",
            "Warranty": "5 years",
            "Weight Range": "12 kg - 32 kg",
            "Material": "Solid Steel"
        }
    },
    {
        "id": "seed-prod-14",
        "name": "Non-Slip Rubber Yoga Mat",
        "category": "Fitness",
        "base_price": 4999.0,
        "brand": "ZenFlow",
        "description": "Enjoy superior grip and comfort during yoga, pilates, and floor exercises with this premium non-slip rubber yoga mat. Crafted from eco-friendly, biodegradable natural tree rubber with an alignment grid to help refine your poses. 5mm cushioning protect joints.",
        "color": "green",
        "material": "rubber",
        "style": "fitness",
        "tags": "yoga-mat,non-slip,rubber,fitness,exercise,eco-friendly",
        "rating": 4.8,
        "review_count": 188,
        "demand_velocity": 85,
        "image": "/images/yoga_mat_premium.png",
        "specs": {
            "Weight": "2.8 kg",
            "Warranty": "2 years",
            "Thickness": "5 mm",
            "Material": "Natural Tree Rubber"
        }
    },
    {
        "id": "seed-prod-15",
        "name": "Smart Body Fat Scale",
        "category": "Fitness",
        "base_price": 3200.0,
        "brand": "NovaSmart",
        "description": "Track your fitness progress accurately with this smart body fat scale. Using Bioelectrical Impedance Analysis (BIA), it measures 13 key body composition metrics including weight, body fat %, muscle mass, hydration, and bone mass. Syncs automatically to your phone via Bluetooth.",
        "color": "white",
        "material": "glass",
        "style": "smart",
        "tags": "scale,smart,body-fat,fitness,health,weight",
        "rating": 4.5,
        "review_count": 220,
        "demand_velocity": 75,
        "image": "/images/smart_water_bottle.png",
        "specs": {
            "Weight": "1.5 kg",
            "Warranty": "1 year",
            "Max Capacity": "180 kg",
            "Connectivity": "Bluetooth 5.0"
        }
    }
]

def seed_db():
    print("Initializing database connection...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Ensure 'embedding' column exists
    if not engine.url.drivername.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding JSON;"))
                conn.commit()
            print("Ensured 'embedding' column exists in 'products' table.")
        except Exception as e:
            print(f"Warning: Could not alter table to add embedding column: {e}")
    else:
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN embedding JSON;"))
                conn.commit()
            print("Added 'embedding' column to SQLite products table.")
        except Exception as e:
            # Column might already exist, which is fine
            print(f"Note: SQLite alter table result: {e}")

    db: Session = SessionLocal()
    
    try:
        # Load ProductEmbedder
        print("Loading ProductEmbedder to generate 384-dimensional semantic vectors...")
        embedder = ProductEmbedder()
        
        for idx, prod_info in enumerate(SEED_PRODUCTS):
            # Check if product already exists to avoid duplicates
            existing = db.query(Product).filter(Product.id == prod_info["id"]).first()
            if existing:
                print(f"Product '{prod_info['name']}' ({prod_info['id']}) already exists. Updating...")
                db_prod = existing
            else:
                print(f"Inserting new product: '{prod_info['name']}' ({prod_info['id']})")
                db_prod = Product(id=prod_info["id"])
                db.add(db_prod)
                
            # Assign basic attributes
            db_prod.name = prod_info["name"]
            db_prod.category = prod_info["category"]
            db_prod.base_price = float(prod_info["base_price"])
            db_prod.current_price = float(prod_info["base_price"])
            db_prod.brand = prod_info["brand"]
            db_prod.description = prod_info["description"]
            db_prod.color = prod_info["color"]
            db_prod.material = prod_info["material"]
            db_prod.style = prod_info["style"]
            db_prod.tags = prod_info["tags"]
            db_prod.rating = float(prod_info["rating"])
            db_prod.review_count = int(prod_info["review_count"])
            db_prod.demand_velocity = int(prod_info["demand_velocity"])
            db_prod.image = prod_info["image"]
            db_prod.specs = prod_info["specs"]
            
            # Generate embedding using name, category, and description
            text_blob = build_product_text_blob(
                name=db_prod.name,
                category=db_prod.category,
                description=db_prod.description
            )
            
            print(f"  Generating embedding for: '{db_prod.name}'...")
            embedding = embedder.get_embedding(text_blob)
            
            # Save the 384-dimensional semantic vector
            db_prod.embedding = embedding
            print(f"  Generated embedding size: {len(embedding)} dimensions.")
            
        db.commit()
        print("Success: Database seeded with 15 products and their semantic vectors!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
