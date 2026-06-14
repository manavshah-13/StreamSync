import threading
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ProductEmbedder:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ProductEmbedder, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self._encode_lock = threading.Lock()
            self._initialized = True
            logger.info("SentenceTransformer model 'all-MiniLM-L6-v2' loaded successfully.")

    def get_embedding(self, text: str) -> list[float]:
        if not self._initialized:
            raise RuntimeError("ProductEmbedder model is not initialized.")
        with self._encode_lock:
            embedding = self.model.encode(text)
            # convert numpy array to plain list of floats
            return [float(x) for x in embedding.tolist()]
