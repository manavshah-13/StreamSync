import random

def get_similar_skus(sku_id: str, limit: int = 4) -> list:
    """
    In production:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    embeddings = model.encode(texts)
    """
    try:
        num = int(sku_id.split('-')[1])
    except:
        num = 1
        
    recommendations = []
    # Force diverse fallback IDs so UI doesn't look barren
    for _ in range(limit):
        target = random.randint(1, 20)
        while target == num:
            target = random.randint(1, 20)
        recommendations.append(f"prod-{target}")
        
    return recommendations
