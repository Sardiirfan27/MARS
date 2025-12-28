from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class SearchRequest(BaseModel):
    query_text: str
    image_mime_type: Optional[str] = Field(
        None,
        description="image/png, image/jpeg, image/webp, dll"
    )
    image_base64: Optional[str] = Field(
        None,
        description="Gambar dalam format base64 (tanpa prefix data:image/*)"
    )
    image_bytes: Optional[bytes] = Field(
    None,
    description="File gambar mentah (bytes) jika dikirim langsung"
    )
    image_url: Optional[str] = Field(
        None,
        description="URL gambar (http/https atau gs://)"
    )

class SearchResult(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any]
    
class RecommendationResult(BaseModel):
    name: str
    price: float
    description: str
    image_path: str


class SearchResponse(BaseModel):
    is_furniture: bool
    description: str
    results: List[SearchResult]
    recommendations: List[RecommendationResult]
