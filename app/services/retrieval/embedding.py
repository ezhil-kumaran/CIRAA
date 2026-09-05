import logfire
from app.config import settings

BATCH_SIZE = 50
_EMBEDDING_DIM = 768  # sentence-transformers/all-mpnet-base-v2

_active_model = None
_model_type = None


# ── Model initialisation ───────────────────────────────────────────────────────

def _load_model():
    from sentence_transformers import SentenceTransformer
    logfire.info("Loading sentence-transformers embedding model (all-mpnet-base-v2, 768-dim).")
    return SentenceTransformer("all-mpnet-base-v2")


def _init():
    """Initialise embedding model once per process. Called lazily on first use."""
    global _active_model, _model_type
    if _active_model is not None:
        return
    _active_model = _load_model()
    _model_type = "fallback"


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_embedding_dim() -> int:
    """Return the vector dimension for the active model. Call after _init()."""
    _init()
    return _EMBEDDING_DIM


# ── Batch embedding ────────────────────────────────────────────────────────────

def _embed_batch(batch: list[str]) -> list[list[float]]:
    return _active_model.encode(batch, show_progress_bar=False).tolist()


# ── Public API (same signatures as before) ─────────────────────────────────────

def embed_query(query: str) -> list[float]:
    _init()
    return _active_model.encode([query])[0].tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    _init()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        with logfire.span("Embed batch", model="sentence-transformers", start=i, size=len(batch)):
            all_embeddings.extend(_embed_batch(batch))
    return all_embeddings
