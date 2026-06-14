import sys
import os

# Ensure backend directory is in python module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import math
from app.ml.similarity import calculate_cosine_similarity, rank_products_by_similarity

def test_calculate_cosine_similarity_basic():
    # Identical vectors -> 1.0
    sim_identical = calculate_cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert math.isclose(sim_identical, 1.0, rel_tol=1e-5)

    # Orthogonal vectors -> 0.0
    sim_orthogonal = calculate_cosine_similarity([1.0, 0.0], [0.0, 1.0])
    assert math.isclose(sim_orthogonal, 0.0, abs_tol=1e-5)

    # Opposite vectors -> -1.0
    sim_opposite = calculate_cosine_similarity([1.0, 1.0], [-1.0, -1.0])
    assert math.isclose(sim_opposite, -1.0, rel_tol=1e-5)

def test_calculate_cosine_similarity_edge_cases():
    # Zero vector
    assert calculate_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert calculate_cosine_similarity([1.0, 2.0], [0.0, 0.0]) == 0.0

    # Empty vectors
    assert calculate_cosine_similarity([], [1.0]) == 0.0
    assert calculate_cosine_similarity([1.0], []) == 0.0

    # Dimension mismatch
    assert calculate_cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0

def test_rank_products_by_similarity():
    user_vec = [1.0, 1.0, 0.0]
    catalog = {
        10: [0.0, 0.0, 1.0], # Orthogonal -> sim = 0.0
        20: [1.0, 1.0, 0.0], # Identical -> sim = 1.0
        30: [1.0, 0.0, 0.0], # Partially matching -> sim = 0.707
        40: [0.5, 0.5, 0.0], # Identical direction -> sim = 1.0
    }

    # Rank with limit = 3
    ranked = rank_products_by_similarity(user_vec, catalog, limit=3)
    
    # 20 and 40 are top (sim=1.0), then 30 (sim=0.707), then 10 (sim=0.0)
    # So top 3 should include 20, 40, 30
    assert len(ranked) == 3
    assert ranked[0] in [20, 40]
    assert ranked[1] in [20, 40]
    assert ranked[2] == 30

    # Test empty catalog
    assert rank_products_by_similarity(user_vec, {}, limit=5) == []

    # Test zero user vector
    assert rank_products_by_similarity([0.0, 0.0], catalog, limit=5) == []
