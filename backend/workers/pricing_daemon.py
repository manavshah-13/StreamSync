import asyncio
import logging
import sys
import os
from typing import Optional
from sqlalchemy import select
import redis.asyncio as aioredis

# Ensure parent directory is in python module path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import async_session_maker
from models.schema import Product, PricingHistory, FairnessLog
from analytics.velocity import DemandVelocityAnalyzer
from pricing.engine import calculate_dynamic_sku_price
from pricing.explainer import generate_price_change_reason

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workers.pricing_daemon")

async def run_pricing_sweep(redis_client: Optional[aioredis.Redis] = None) -> None:
    """
    Executes a single pricing sweep over all products in the database.
    Calculates dynamic prices based on current demand velocity, stock count, and trending status.
    If prices differ, updates the database and logs structural reasoning in PricingHistory.
    """
    logger.info("[Pricing Daemon] Initiating pricing sweep...")
    analyzer = DemandVelocityAnalyzer(redis_client=redis_client)

    try:
        async with async_session_maker() as db:
            # Fetch all products from the database
            result = await db.execute(select(Product))
            products = result.scalars().all()

            logger.info(f"[Pricing Daemon] Loaded {len(products)} products for evaluation.")
            changes_made = False

            for product in products:
                try:
                    # 1. Fetch live 30-second interaction count (demand velocity)
                    velocity = await analyzer.get_sku_velocity(product.id, window_seconds=30)

                    # 2. Extract product inventory details from specs JSON
                    specs = product.specs or {}
                    
                    # Fallback default values if not present in DB
                    stock_count = int(specs.get("stock_count", 50))
                    is_trending = bool(specs.get("is_trending", False)) or (velocity > 30)

                    base_price = product.base_price or 0.0
                    old_price = product.current_price if product.current_price is not None else base_price

                    # 3. Calculate new dynamic price using business logic rules
                    new_price = calculate_dynamic_sku_price(
                        base_price=base_price,
                        demand_velocity=velocity,
                        stock_count=stock_count,
                        is_trending=is_trending,
                        current_price=old_price
                    )

                    # 4. Check for active bias flags in fairness_logs for this product or segment
                    bias_query = select(FairnessLog).where(
                        FairnessLog.bias_detected == True
                    ).order_by(FairnessLog.timestamp.desc()).limit(10)
                    bias_result = await db.execute(bias_query)
                    bias_logs = bias_result.scalars().all()
                    
                    product_has_bias = False
                    for log in bias_logs:
                        if hasattr(log, "metric_scanned"):
                            if (log.metric_scanned == f"pricing_parity:{product.id}") or \
                               (log.metric_scanned == "Dynamic Pricing Disparity" and f"Product {product.id}" in (log.operational_fix or "")):
                                product_has_bias = True
                                break

                    clamped_by_fairness = False
                    if product_has_bias and new_price != base_price:
                        new_price = base_price
                        clamped_by_fairness = True

                    if new_price != product.current_price:
                        # Update product
                        product.current_price = new_price

                        if clamped_by_fairness:
                            reason = "Price adjustment clamped by AI Fairness Scanner to prevent segment discrimination"
                        else:
                            # Generate structured reason using explainer service
                            reason = generate_price_change_reason(old_price, new_price, velocity, stock_count)

                        history_entry = PricingHistory(
                            product_id=product.id,
                            old_price=old_price,
                            new_price=new_price,
                            change_reason=reason
                        )
                        db.add(history_entry)
                        changes_made = True

                        logger.info(
                            f"[Pricing Daemon] SKU {product.id}: Price updated "
                            f"{old_price:.2f} -> {new_price:.2f} ({reason})"
                        )

                except Exception as pe:
                    logger.error(
                        f"[Pricing Daemon] Error calculating dynamic price for SKU {product.id}: {pe}", 
                        exc_info=True
                    )

            if changes_made:
                try:
                    await db.commit()
                    logger.info("[Pricing Daemon] Transaction committed successfully with price updates.")
                except Exception as commit_err:
                    await db.rollback()
                    logger.error(f"[Pricing Daemon] Transaction commit failed, rolled back: {commit_err}", exc_info=True)
            else:
                logger.info("[Pricing Daemon] Sweep execution completed. No price updates were required.")

    except Exception as e:
        logger.error(f"[Pricing Daemon] Database or sweep orchestration failure: {e}", exc_info=True)

async def run_daemon(redis_client: Optional[aioredis.Redis] = None) -> None:
    """
    Main background daemon worker loop executing every 30 seconds.
    """
    logger.info("[Pricing Daemon] Dynamic pricing daemon starting...")
    while True:
        try:
            await run_pricing_sweep(redis_client=redis_client)
        except Exception as e:
            logger.error(f"[Pricing Daemon] Critical error in daemon sweep loop: {e}", exc_info=True)
        
        logger.info("[Pricing Daemon] Sleeping for 30 seconds before next sweep...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(run_daemon())
    except KeyboardInterrupt:
        logger.info("[Pricing Daemon] Stopped by user command.")
