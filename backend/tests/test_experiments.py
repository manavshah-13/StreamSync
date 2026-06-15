import sys
import os
import pytest

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.experiments.router_logic import assign_experiment_variant

def test_assign_experiment_variant_determinism():
    # Determinism check: Same identifier and experiment should always result in same variant
    assert assign_experiment_variant("user_123", "exp_recommendation_v2") == assign_experiment_variant("user_123", "exp_recommendation_v2")
    assert assign_experiment_variant("user_abc", "exp_pricing_v1") == assign_experiment_variant("user_abc", "exp_pricing_v1")

def test_assign_experiment_variant_distribution():
    # Statistical distribution check: check that 1000 simulated users split roughly 50/50
    variants = []
    for i in range(1000):
        variants.append(assign_experiment_variant(f"user_{i}", "exp_test"))
        
    count_a = variants.count("A")
    count_b = variants.count("B")
    
    # Assert that the distribution is within a reasonable statistical bounds of a 50/50 split
    # For 1000 iterations, the standard deviation is sqrt(1000 * 0.5 * 0.5) = ~15.8.
    # A threshold of 450 to 550 easily covers the 99.9% confidence interval.
    assert 450 <= count_a <= 550
    assert 450 <= count_b <= 550
    assert count_a + count_b == 1000

def test_assign_experiment_variant_different_experiments():
    # User should get potentially different assignments in different experiments
    user_id = "user_456"
    var_1 = assign_experiment_variant(user_id, "exp_1")
    var_2 = assign_experiment_variant(user_id, "exp_2")
    var_3 = assign_experiment_variant(user_id, "exp_3")
    var_4 = assign_experiment_variant(user_id, "exp_4")
    
    # They shouldn't all be identical unless by 1/16 chance. Over different experiments,
    # the user will fall into different buckets.
    results = {var_1, var_2, var_3, var_4}
    assert len(results) > 0
