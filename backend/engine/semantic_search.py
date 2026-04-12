"""
SemanticSearchEngine — TF-IDF + Attribute Boosting
====================================================
Understands natural language queries like "green shoes", "lightweight laptop",
"wireless noise-cancelling earbuds" without any external APIs or model downloads.

Pipeline:
  1. build_index(products)  — called once at startup
     - Tokenises name + description + tags, builds TF-IDF matrix in-process
     - Repeats attribute tokens (color×5, tags×4, material×3) for emphasis
  2. query(text, limit)  — real-time, sub-millisecond
     - Parses query → extracts {colors, materials, styles, category, keywords}
     - Scores every product by TF-IDF cosine similarity
     - Applies multiplicative boosts for exact attribute matches
     - Returns sorted results with matchScore
"""
import re
import math
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Vocabulary tables ──────────────────────────────────────────────────────────

COLORS = {
    "red", "blue", "green", "black", "white", "silver", "gold", "grey", "gray",
    "brown", "orange", "purple", "pink", "yellow", "cyan", "teal", "navy",
    "charcoal", "beige", "cream", "dark", "light", "matte", "rose", "jade",
}

MATERIALS = {
    "leather", "fabric", "metal", "plastic", "silicon", "silicone", "aluminum",
    "aluminium", "steel", "glass", "wood", "rubber", "mesh", "nylon", "cotton",
    "silk", "foam", "carbon", "ceramic",
}

STYLES = {
    "minimalist", "gaming", "professional", "casual", "premium", "luxury",
    "compact", "portable", "wireless", "smart", "ergonomic", "ultralight",
    "fitness", "outdoor", "vintage", "modern", "sleek",
}

# Maps search terms → product category
CATEGORY_ALIASES: dict[str, str] = {
    # Apparel
    "shoes": "Apparel", "sneakers": "Apparel", "clothing": "Apparel",
    "apparel": "Apparel", "fashion": "Apparel", "bag": "Apparel",
    "backpack": "Apparel", "wear": "Apparel", "pillowcase": "Apparel",
    "bedding": "Apparel",
    # Electronics
    "laptop": "Electronics", "computer": "Electronics", "tab": "Electronics",
    "phone": "Electronics", "device": "Electronics", "gadget": "Electronics",
    "headphones": "Electronics", "earbuds": "Electronics", "speaker": "Electronics",
    "webcam": "Electronics", "camera": "Electronics", "charger": "Electronics",
    "watch": "Electronics", "lamp": "Electronics", "light": "Electronics",
    # Home
    "desk": "Home", "furniture": "Home", "kitchen": "Home",
    "scale": "Home", "bottle": "Home",
    # Sports
    "mat": "Sports", "fitness": "Sports", "workout": "Sports", "gym": "Sports",
    "roller": "Sports", "bands": "Sports", "resistance": "Sports",
    # Beauty
    "beauty": "Beauty", "skincare": "Beauty",
    # Toys
    "toys": "Toys", "game": "Toys",
}

# Synonym expansion: query token → list of equivalent tokens
SYNONYMS: dict[str, list] = {
    "earbuds": ["buds", "earbud", "earphone"],
    "buds":    ["earbuds", "earphone"],
    "laptop":  ["notebook", "computer"],
    "shoes":   ["footwear", "sneakers"],
    "speaker": ["audio", "sound"],
    "wireless": ["bluetooth", "bt"],
    "noise":   ["anc", "cancelling"],
}


class SemanticSearchEngine:
    def __init__(self):
        self._idf:          dict[str, float] = {}
        self._product_tfs:  dict[str, dict]  = {}  # pid → {term: tf}
        self._products:     dict[str, dict]  = {}  # pid → raw product dict
        self._ready = False

    # ── Public: build index ────────────────────────────────────────────────────

    def build_index(self, products: list[dict]):
        """
        Build TF-IDF index from a list of product dicts.
        Call once at server startup after mock_db is seeded.
        """
        n_docs = len(products)
        if n_docs == 0:
            logger.warning("[SemanticSearch] No products to index.")
            return

        term_doc_freq: dict[str, int] = defaultdict(int)
        product_term_counts: dict[str, dict] = {}

        for prod in products:
            pid = prod.get("id", "")
            self._products[pid] = prod

            # Build weighted document
            base_tokens   = self._tokenize(f"{prod.get('name','')} {prod.get('description','')} {prod.get('category','')} {prod.get('brand','')}")
            color_tokens  = self._tokenize(prod.get("color", "")) * 5
            tag_tokens    = self._tokenize(prod.get("tags", "").replace(",", " ")) * 4
            mat_tokens    = self._tokenize(prod.get("material", "")) * 3
            style_tokens  = self._tokenize(prod.get("style", "")) * 2
            all_tokens    = base_tokens + color_tokens + tag_tokens + mat_tokens + style_tokens

            term_counts: dict[str, int] = defaultdict(int)
            for t in all_tokens:
                if len(t) >= 2:
                    term_counts[t] += 1

            product_term_counts[pid] = dict(term_counts)
            for term in term_counts:
                term_doc_freq[term] += 1

        # IDF: log((N+1)/(df+1)) + 1  (smoothed)
        self._idf = {
            term: math.log((n_docs + 1) / (df + 1)) + 1
            for term, df in term_doc_freq.items()
        }

        # TF: normalised by max term frequency in document
        self._product_tfs = {}
        for pid, counts in product_term_counts.items():
            max_c = max(counts.values()) if counts else 1
            self._product_tfs[pid] = {t: c / max_c for t, c in counts.items()}

        self._ready = True
        logger.info(f"[SemanticSearch] Index built: {n_docs} products, {len(self._idf)} unique terms.")

    def build_index_from_redis_sync(self, redis_sync):
        """
        Convenience: build index directly from the synchronous FakeRedis client.
        Pulls all product hashes from Redis.
        """
        try:
            all_ids = redis_sync.smembers("products:all")
            products = []
            for pid in all_ids:
                prod = redis_sync.hgetall(f"product:{pid}")
                if prod:
                    products.append(dict(prod))
            self.build_index(products)
        except Exception as e:
            logger.error(f"[SemanticSearch] build_index_from_redis_sync failed: {e}")

    # ── Public: query ──────────────────────────────────────────────────────────

    def query(self, query_text: str, limit: int = 10) -> dict:
        """
        Main search entry point.
        Returns {products, query_parsed, total, status}.
        """
        if not self._ready:
            return {"products": [], "query_parsed": {}, "total": 0, "status": "cold"}

        parsed        = self._parse_query(query_text)
        query_tokens  = self._expand_synonyms(self._tokenize(query_text))
        scores: dict[str, float] = {}

        for pid, tf_dict in self._product_tfs.items():
            prod = self._products.get(pid, {})

            # ── TF-IDF score ──────────────────────────────────────────────────
            tfidf = sum(
                tf_dict.get(t, 0) * self._idf.get(t, 0)
                for t in query_tokens
            )

            # ── Attribute boosts ──────────────────────────────────────────────
            boost = 1.0

            prod_color    = prod.get("color", "").lower()
            prod_material = prod.get("material", "").lower()
            prod_style    = prod.get("style", "").lower()
            prod_tags     = prod.get("tags", "").lower()
            prod_category = prod.get("category", "")

            for color in parsed["colors"]:
                if color in prod_color or color in prod_tags:
                    boost  *= 2.5
                    tfidf  += 6.0

            for mat in parsed["materials"]:
                if mat in prod_material or mat in prod_tags:
                    boost  *= 1.8
                    tfidf  += 3.0

            for style in parsed["styles"]:
                if style in prod_style or style in prod_tags:
                    boost  *= 1.5
                    tfidf  += 2.0

            if parsed["category"] and prod_category == parsed["category"]:
                boost  *= 2.0
                tfidf  += 4.0

            final = tfidf * boost
            if final > 0.05:
                scores[pid] = round(final, 3)

        # Sort descending by score
        sorted_hits = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        result_products = []
        for pid, score in sorted_hits:
            prod = dict(self._products.get(pid, {}))
            prod["matchScore"] = score
            prod["price"]      = float(prod.get("current_price") or prod.get("base_price") or 0)
            result_products.append(prod)

        return {
            "products":     result_products,
            "query_parsed": parsed,
            "total":        len(result_products),
            "status":       "warm",
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        tokens = text.split()
        stemmed = []
        for t in tokens:
            if len(t) > 4:
                if t.endswith("ing"):
                    t = t[:-3]
                elif t.endswith("ed"):
                    t = t[:-2]
                elif t.endswith("s") and not t.endswith("ss"):
                    t = t[:-1]
            stemmed.append(t)
        return [t for t in stemmed if len(t) >= 2]

    @staticmethod
    def _expand_synonyms(tokens: list[str]) -> list[str]:
        expanded = list(tokens)
        for t in tokens:
            if t in SYNONYMS:
                expanded.extend(SYNONYMS[t])
        return expanded

    @staticmethod
    def _parse_query(query: str) -> dict:
        tokens = re.sub(r"[^a-z\s]", "", query.lower()).split()
        parsed: dict = {
            "colors":    [],
            "materials": [],
            "styles":    [],
            "category":  None,
            "keywords":  [],
        }
        for token in tokens:
            if token in COLORS:
                parsed["colors"].append(token)
            elif token in MATERIALS:
                parsed["materials"].append(token)
            elif token in STYLES:
                parsed["styles"].append(token)
            elif token in CATEGORY_ALIASES:
                parsed["category"] = CATEGORY_ALIASES[token]
            else:
                parsed["keywords"].append(token)
        return parsed


# ── Global singleton ──────────────────────────────────────────────────────────
semantic_engine = SemanticSearchEngine()
