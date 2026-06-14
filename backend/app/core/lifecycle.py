import asyncio
import logging
from db.database import SessionLocal
from app.ml.indexer import generate_catalog_embeddings

logger = logging.getLogger(__name__)

# Global in-memory cache for fast similarity lookup
PRODUCT_EMBEDDING_CACHE: dict[str, list[float]] = {}

async def build_and_cache_catalog_embeddings():
    """
    Background worker task that generates product embeddings and loads them
    into the in-memory runtime cache. Wraps the routine in a try-except block
    and enforces a timeout to fail gracefully if the model download or indexing hangs.
    """
    logger.info("Initializing background catalog embedding sync...")
    db_session = None
    try:
        db_session = SessionLocal()
        
        # Enforce a 45-second timeout on the overall generation/download process
        embeddings = await asyncio.wait_for(
            generate_catalog_embeddings(db_session),
            timeout=45.0
        )
        
        # Load active product vectors directly into the runtime cache
        global PRODUCT_EMBEDDING_CACHE
        PRODUCT_EMBEDDING_CACHE.clear()
        for item in embeddings:
            for prod_id, vector in item.items():
                PRODUCT_EMBEDDING_CACHE[prod_id] = vector
                
        logger.info(f"Successfully loaded {len(PRODUCT_EMBEDDING_CACHE)} product embeddings into in-memory cache.")
    except asyncio.TimeoutError:
        logger.warning(
            "Background catalog embedding synchronization timed out (possibly due to slow model download). "
            "Proceeding in fallback mode."
        )
    except Exception as e:
        logger.warning(
            f"Failed to load or cache product vector embeddings: {e}. "
            "Proceeding in fallback mode."
        )
    finally:
        if db_session:
            db_session.close()

def register_startup_sync(app):
    """
    Spawns the startup catalog synchronization background worker.
    """
    asyncio.create_task(build_and_cache_catalog_embeddings())
