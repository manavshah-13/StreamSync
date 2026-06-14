import numpy as np
from typing import Any

def calculate_cosine_similarity(vecA: list[float], vecB: list[float]) -> float:
    """
    Calculates the cosine similarity between two 384-dimensional vector arrays.
    Returns a float between -1.0 and 1.0 (or 0.0 in case of zero vectors).
    """
    if not vecA or not vecB:
        return 0.0
        
    a = np.array(vecA, dtype=float)
    b = np.array(vecB, dtype=float)
    
    # Handle dimension mismatch if any
    if a.shape != b.shape:
        return 0.0
        
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return float(np.dot(a, b) / (norm_a * norm_b))

def rank_products_by_similarity(
    user_session_vector: list[float],
    product_catalog_vectors: dict[Any, list[float]],
    limit: int = 5
) -> list[Any]:
    """
    Compares the user session vector against all product vectors in the catalog.
    Sorts in descending order of similarity and returns the top product IDs.
    """
    if not user_session_vector or not product_catalog_vectors:
        return []
        
    u = np.array(user_session_vector, dtype=float)
    norm_u = np.linalg.norm(u)
    if norm_u == 0.0:
        return []
        
    scores = []
    for pid, pvec in product_catalog_vectors.items():
        if not pvec:
            continue
            
        p = np.array(pvec, dtype=float)
        if u.shape != p.shape:
            continue
            
        norm_p = np.linalg.norm(p)
        if norm_p == 0.0:
            similarity = 0.0
        else:
            similarity = float(np.dot(u, p) / (norm_u * norm_p))
            
        scores.append((pid, similarity))
        
    # Sort descending by similarity score
    scores.sort(key=lambda x: x[1], reverse=True)
    
    return [pid for pid, _ in scores[:limit]]
