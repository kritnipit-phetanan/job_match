"""
Embed Jobs — ใช้ Ollama (nomic-embed-text) สร้าง vector embeddings จาก JD
"""
import ollama as ollama_client
from etl.config import EMBEDDING_MODEL


def embed_text(text: str, model: str = None) -> list[float]:
    """
    สร้าง vector embedding จาก text
    
    Args:
        text: ข้อความที่จะ embed (JD, Resume, etc.)
        model: ชื่อ embedding model (default: nomic-embed-text)
    
    Returns:
        list[float] — 768-dimensional vector
    """
    if not text or text.strip() in ("", "Not Found", "Error", "No Link"):
        return None

    model = model or EMBEDDING_MODEL

    try:
        response = ollama_client.embed(
            model=model,
            input=text[:8000],  # nomic-embed-text รองรับสูงสุด 8192 tokens
        )
        # ollama.embed returns {"embeddings": [[...]]}
        return response['embeddings'][0]
    except Exception as e:
        print(f"   ⚠️ Embedding error: {e}")
        return None


def embed_batch(texts: list[str], model: str = None) -> list[list[float]]:
    """
    สร้าง embeddings จากหลาย texts พร้อมกัน
    
    Returns:
        list of 768-dim vectors (None สำหรับ text ที่ embed ไม่ได้)
    """
    results = []
    for text in texts:
        vec = embed_text(text, model)
        results.append(vec)
    return results
