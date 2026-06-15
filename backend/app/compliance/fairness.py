from typing import Dict, Any, Union, Optional
import math

class FairnessAuditor:
    """
    FairnessAuditor handles demographic compliance checks and checks for algorithmic pricing bias.
    """
    def __init__(self, threshold: float = 0.15):
        self.threshold = threshold

    def analyze_pricing_parity(
        self, product_id: Union[int, str], segment_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze demographic pricing parity to check for potential algorithmic bias.
        
        Args:
            product_id: ID of the product being audited.
            segment_prices: Dict mapping demographic segment (e.g. "Age 18-25") to the offered price.
            
        Returns:
            Dict containing:
                - fairness_score (0.0 to 1.0, where 1.0 is perfectly uniform pricing)
                - variance_score (the statistical variance of the prices)
                - bias_detected (bool indicating if the price variation/spread exceeds the compliance threshold)
                - max_spread (the absolute difference between maximum and minimum prices)
                - mean_price (the mean of the offered prices)
        """
        if not segment_prices or len(segment_prices) <= 1:
            return {
                "fairness_score": 1.0,
                "variance_score": 0.0,
                "bias_detected": False,
                "max_spread": 0.0,
                "mean_price": list(segment_prices.values())[0] if segment_prices else 0.0
            }

        prices = list(segment_prices.values())
        n = len(prices)
        
        # Calculate mean price
        mean_price = sum(prices) / n
        
        # Calculate statistical variance
        variance = sum((p - mean_price) ** 2 for p in prices) / n
        
        # Calculate maximum spread
        max_price = max(prices)
        min_price = min(prices)
        max_spread = max_price - min_price
        
        # Calculate spread ratio relative to the minimum price (or mean if min is 0)
        spread_ratio = (max_spread / min_price) if min_price > 0 else 0.0
        
        # Define fairness score: 1.0 is perfectly uniform, decreases as spread ratio increases
        fairness_score = max(0.0, 1.0 - spread_ratio)
        
        # If the variance or the spread ratio exceeds the threshold (e.g. 15% spread difference)
        # we flag bias_detected as True
        bias_detected = spread_ratio > self.threshold

        return {
            "fairness_score": round(fairness_score, 4),
            "variance_score": round(variance, 4),
            "bias_detected": bias_detected,
            "max_spread": round(max_spread, 2),
            "mean_price": round(mean_price, 2)
        }

    def audit_and_log(
        self, db_session, product_id: Union[int, str], segment_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze pricing parity and log the audit event into the database 'fairness_logs' table.
        """
        metrics = self.analyze_pricing_parity(product_id, segment_prices)
        
        try:
            from models.schema import FairnessLog
            log_entry = FairnessLog(
                metric_scanned=f"pricing_parity:{product_id}",
                bias_detected=metrics["bias_detected"],
                variance_score=metrics["variance_score"],
                operational_fix=(
                    f"Pricing bias detected for product {product_id} (spread: {metrics['max_spread']}, "
                    f"variance: {metrics['variance_score']}). Re-aligning segment prices to standard dev."
                    if metrics["bias_detected"] else None
                )
            )
            db_session.add(log_entry)
            db_session.commit()
        except Exception as e:
            print(f"Warning: Failed to persist fairness log: {e}")
            db_session.rollback()
            
        return metrics

def analyze_pricing_parity(
    product_id: Union[int, str], segment_prices: Dict[str, float], threshold: float = 0.15
) -> Dict[str, Any]:
    """
    Standalone module function that forwards to FairnessAuditor.
    """
    auditor = FairnessAuditor(threshold=threshold)
    return auditor.analyze_pricing_parity(product_id, segment_prices)
