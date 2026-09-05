import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI

from app.config import settings


# Production gateway config:
#   - Fallback: primary @rag/llama-3.3-70b-versatile → @brag/llama-3.1-8b-instant on failure
#   - Cache: semantic mode (requires Portkey Enterprise — silently falls back to simple on free/starter)
#   - Retry: 2 attempts on rate limit / server error before triggering the fallback target
# If a Portkey Config ID (e.g., 'pc-...') is provided in .env, use it;
# otherwise, omit inline config to prevent 'inline_config_blocked' errors from Portkey.
PORTKEY_CONFIG = settings.PORTKEY_CONFIG_ID if settings.PORTKEY_CONFIG_ID else None

if PORTKEY_CONFIG:
    portkey_client = Portkey(
        api_key=settings.PORTKEY_API_KEY,
        config=PORTKEY_CONFIG
    )
else:
    portkey_client = Portkey(
        api_key=settings.PORTKEY_API_KEY
    )


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Returns a Portkey-backed ChatOpenAI — a drop-in for ChatGroq in LangChain nodes.
    """
    header_kwargs = {
        "api_key": settings.PORTKEY_API_KEY,
        "metadata": {
            "feature": feature,
            "_user": "rag-system",
            "environment": "production"
        }
    }
    if PORTKEY_CONFIG:
        header_kwargs["config"] = PORTKEY_CONFIG

    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}",
        temperature=0,
        default_headers=createHeaders(**header_kwargs)
    )

def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey response headers.
    """
    if hasattr(response, "get_headers") and callable(response.get_headers):
        try:
            headers = response.get_headers() or {}
            status = headers.get("cache-status") or headers.get("x-portkey-cache-status") or ""
            if status:
                return status.upper()
        except Exception:
            pass

    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"