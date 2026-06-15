import asyncio
import re
import logging
from app.ml.embedder import ProductEmbedder
from models.schema import Product

logger = logging.getLogger(__name__)

def build_product_text_blob(name: str, category: str, description: str) -> str:
    """
    Combines name, category, and description into a single, cleaned, lowercase text string.
    Handles empty or null text fields gracefully.
    """
    # Replace None/null values with empty strings
    name_str = name or ""
    category_str = category or ""
    description_str = description or ""
    
    # Combine parts with space separator
    combined = f"{name_str} {category_str} {description_str}"
    
    # Clean: convert to lowercase and replace multiple whitespace/newlines with a single space
    cleaned = re.sub(r"\s+", " ", combined.lower())
    
    return cleaned.strip()

async def generate_catalog_embeddings(db_session) -> list[dict[str, list[float]]]:
    """
    Fetches all active products from the database, builds their text blobs,
    generates vector embeddings using ProductEmbedder, and returns a list
    of dictionaries mapping product IDs to their corresponding vector arrays.
    """
    try:
        products = db_session.query(Product).all()
    except Exception as e:
        logger.error(f"Failed to query products from database: {e}")
        return []
        
    # Instantiate ProductEmbedder on a separate thread to prevent event loop blocking
    embedder = await asyncio.to_thread(ProductEmbedder)
    results = []
    
    for product in products:
        if not product or not product.id:
            continue
            
        # Check if pre-computed embedding exists in DB
        if product.embedding is not None and len(product.embedding) == 384:
            results.append({product.id: product.embedding})
            continue

        # Extract fields and pass to build_product_text_blob
        text_blob = build_product_text_blob(
            name=product.name,
            category=product.category,
            description=product.description
        )
        
        try:
            # Perform inference on a separate thread to keep API gateway responsive
            embedding = await asyncio.to_thread(embedder.get_embedding, text_blob)
            results.append({product.id: embedding})
        except Exception as e:
            logger.error(f"Failed to generate embedding for product {product.id}: {e}")
            
    return results

