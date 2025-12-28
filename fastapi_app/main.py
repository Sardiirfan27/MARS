from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi_app.schemas import SearchRequest, SearchResponse
from fastapi_app.services.llm import analyze_image_and_text, recommend_products
from fastapi_app.services.embeddings import VertexAIMultiModalEmbeddings
from fastapi_app.services.search import search_multimodal

from functools import lru_cache


app = FastAPI(title="Multimodal Furniture Search API")

embeddings = VertexAIMultiModalEmbeddings()
@lru_cache(maxsize=2048)
def cached_image_and_text_embedding(image_url: str, text: str, embedder):
    return embedder.embed_image_and_text(image_url, text)

@app.get("/")
def welcome():
    return {
        "message": "Welcome to Multimodal Furniture Search API 🚀",
        "usage": {
            "docs": "/docs",
            "search_endpoint": "/search",
            "method": "POST"
        },
        "note": "Gunakan endpoint /search dengan upload image + query text"
    }
    
@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    
    # cek apakah ada input teks, jika tidak ada maka berikan peringatan 
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")
    
    # =========================
    # Tentukan image input
    # =========================
    image_input = None
    if request.image_base64:
        image_input = request.image_base64   # PRIORITAS
    elif request.image_url:
        image_input = request.image_url
        
    # Validasi apakah furniture atau tidak
    analysis = analyze_image_and_text(
        image_input=image_input,
        query_text=request.query_text,
        image_mime_type=request.image_mime_type
    )
    # print(analysis)
    # STOP jika bukan furniture
    if not analysis.get("is_furniture", False):
        return {
            "is_furniture": False,
            "description": analysis.get("description", ""),
            "results": [],
            "recommendations": []
        }
    
    
    img_vec, txt_vec = cached_image_and_text_embedding(
        image_url=image_input,
        text=request.query_text,
        embedder=embeddings
    )

    # lakaukan pencarian top K products yang cocok
    results = search_multimodal(query_vector_text=txt_vec, query_vector_image=img_vec) 
    # Ambil beberapa key di metadata agar tidak terlalu besar
    context_str = [
        {
            # "id": r["id"],
            "name": r["metadata"].get("name", "Unknown Product"),
            "price": r["metadata"].get("price", "Unknown Price"),
            "description": r["metadata"].get("description", ""),
            "image_path": r["metadata"].get("image_path", ""),
        }
        for r in results
    ]
    products = recommend_products(
        query_text=request.query_text,
        description=analysis["description"],
        context_str=context_str
    )
    
    # print(products)
    return {
        "is_furniture": analysis["is_furniture"],
        "description": analysis["description"],
        "results": results,
        'recommendations': products
    }
