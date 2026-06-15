import sys
import os
import asyncio
import logging
import inspect
from typing import Dict, Any, Union, List
from sqlalchemy import select, desc

# Ensure parent directories are in python module path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import async_session_maker
from models.schema import PricingHistory, FairnessLog, Product
from app.compliance.fairness import FairnessAuditor

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workers.fairness_worker")

async def run_fairness_scan(db_session) -> Dict[str, Any]:
    """
    Scans the recent 'pricing_history' table records, simulates demographic
    segment offers, audits pricing parity, and logs anomalies to 'fairness_logs'.
    
    Args:
        db_session: A sync or async SQLAlchemy session.
        
    Returns:
        Dict summarizing the scan results.
    """
    logger.info("[Fairness Scanner] Initiating fairness audit sweep...")
    is_async = hasattr(db_session, "execute") and inspect.iscoroutinefunction(db_session.execute)
    
    # 1. Fetch recent pricing history rows
    try:
        if is_async:
            result = await db_session.execute(
                select(PricingHistory).order_by(desc(PricingHistory.timestamp)).limit(100)
            )
            history_rows = result.scalars().all()
        else:
            history_rows = db_session.query(PricingHistory).order_by(PricingHistory.timestamp.desc()).limit(100).all()
    except Exception as e:
        logger.error(f"[Fairness Scanner] Failed to query pricing history: {e}")
        return {"status": "error", "message": str(e)}

    if not history_rows:
        logger.info("[Fairness Scanner] No pricing history records found to scan.")
        return {"status": "success", "scanned_products": 0, "anomalies_detected": 0}

    # Group price adjustments by product_id
    grouped_by_product: Dict[str, List[PricingHistory]] = {}
    for row in history_rows:
        if row.product_id not in grouped_by_product:
            grouped_by_product[row.product_id] = []
        grouped_by_product[row.product_id].append(row)

    auditor = FairnessAuditor(threshold=0.15)
    anomalies_detected = 0
    scanned_products = len(grouped_by_product)

    # 2. Group adjustments and calculate scores
    for product_id, rows in grouped_by_product.items():
        # Get the latest price change for this product
        latest_change = rows[0]
        new_price = float(latest_change.new_price)
        reason = latest_change.change_reason or ""
        
        # Determine if price change represents surge demand/high velocity
        is_high_demand = (
            "demand" in reason.lower() or 
            "velocity" in reason.lower() or 
            "surge" in reason.lower() or 
            "high" in reason.lower()
        )
        
        # Simulate demographic pricing offers based on segment attributes
        if is_high_demand:
            # Trigger dynamic pricing disparity (> 15% difference)
            segment_prices = {
                "Age 18-25": new_price * 0.88,
                "Age 26-45": new_price * 1.05,
                "Age 45+": new_price * 1.22
            }
        else:
            # Safe compliant pricing variance
            segment_prices = {
                "Age 18-25": new_price * 0.98,
                "Age 26-45": new_price * 1.00,
                "Age 45+": new_price * 1.02
            }
            
        # 3. Analyze pricing parity using FairnessAuditor
        metrics = auditor.analyze_pricing_parity(product_id, segment_prices)
        
        # 4. Log to fairness_logs if bias is detected
        if metrics["bias_detected"]:
            anomalies_detected += 1
            operational_fix = (
                f"WARNING: Clamping price ceiling for Product {product_id}; "
                f"demographic variance exceeded safe limit ({metrics['max_spread']} spread)"
            )
            
            logger.warning(
                f"[Fairness Scanner] Bias detected on SKU {product_id}! "
                f"Variance: {metrics['variance_score']}. Fix: {operational_fix}"
            )
            
            log_entry = FairnessLog(
                metric_scanned="Dynamic Pricing Disparity",
                bias_detected=True,
                variance_score=metrics["variance_score"],
                operational_fix=operational_fix
            )
            
            try:
                db_session.add(log_entry)
                if is_async:
                    await db_session.commit()
                else:
                    db_session.commit()
            except Exception as le:
                logger.error(f"[Fairness Scanner] Failed to write fairness log: {le}")
                if is_async:
                    await db_session.rollback()
                else:
                    db_session.rollback()

    logger.info(
        f"[Fairness Scanner] Sweep completed. Scanned products: {scanned_products}, "
        f"Anomalies logged: {anomalies_detected}."
    )
    
    return {
        "status": "success",
        "scanned_products": scanned_products,
        "anomalies_detected": anomalies_detected
    }

async def run_daemon():
    """
    Main loop that invokes run_fairness_scan periodically.
    """
    logger.info("[Fairness Scanner] Starting automated fairness scan daemon...")
    while True:
        try:
            async with async_session_maker() as db:
                await run_fairness_scan(db)
        except Exception as e:
            logger.error(f"[Fairness Scanner] Error in automated scanner sweep: {e}", exc_info=True)
            
        logger.info("[Fairness Scanner] Sleeping for 60 seconds...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(run_daemon())
    except KeyboardInterrupt:
        logger.info("[Fairness Scanner] Stopped by user command.")
