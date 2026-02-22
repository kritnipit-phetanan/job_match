"""
Embed Jobs — ใช้ Gemini Embedding API (gemini-embedding-001) สร้าง vector embeddings จาก JD
"""
from google import genai
from etl.config import GEMINI_API_KEY


def embed_text(text: str) -> list[float]:
    """
    สร้าง vector embedding จาก text (768 dims)
    ใช้ Gemini Embedding API (gemini-embedding-001)
    """
    if not text or text.strip() in ("", "Not Found", "Error", "No Link"):
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text[:8000],
            config={"output_dimensionality": 768}  # ให้ตรงกับ DB schema vector(768)
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"   ⚠️ Gemini Embedding error: {e}")
        return None


def embed_batch(texts: list[str]) -> list[list[float]]:
    """สร้าง embeddings จากหลาย texts พร้อมกัน"""
    results = []
    for text in texts:
        vec = embed_text(text)
        results.append(vec)
    return results
