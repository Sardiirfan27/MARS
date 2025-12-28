import json

import base64
from typing import Union
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from fastapi_app.config import PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS

credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    credentials=credentials,
    project=PROJECT_ID,
    temperature=0.4,
    vertexai=True,
)

SYSTEM_PROMPT = (
    "Anda adalah sistem analisis produk furniture. "
    "Output harus JSON valid dengan keys: is_furniture (boolean) dan description (string). "
    "is_furniture bernilai True jika Input berkaitan dengan furniture walaupun tidak ada input gambar (meja, kursi, sofa, lemari, dll). "
    "description (<1000 karakter) harus berisi : ringkasan input user, jelaskan kegunaan produk, material produk dan warnanya jika ada."
)

def analyze_image_and_text(
    image_input: Union[str, bytes, None], 
    image_mime_type: str,
    query_text: str) -> dict:
    
    content = []

    # =====================
    # IMAGE HANDLING
    # =====================
    if image_input:
        content.append({
            "type": "image",
            "base64": image_input,
            "mime_type": image_mime_type,
        })
    # =====================
    # TEXT
    # =====================
    if query_text:
        content.append({
            "type": "text",
            "text": query_text
        })
        
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content)
    ]

    response = llm.invoke(messages)

    raw = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "is_furniture": False,
            "description": ""
        }
        
    if not isinstance(result.get("is_furniture"), bool):
        result["is_furniture"] = False

    if not isinstance(result.get("description"), str):
        result["description"] = ""

    return result


def recommend_products(
    query_text,
    description,
    context_str
):

    final_prompt_template = f"""
Anda adalah asisten rekomendasi produk furniture yang profesional dan akurat.
ATURAN WAJIB:
1. Rekomendasikan 1-3 produk PALING relevan dan Produk HARUS sesuai kebutuhan pengguna.
2. HANYA gunakan produk yang ADA di hasil pencarian.
3. Jika tidak ada produk relevan, kembalikan array kosong [].
4. Output HARUS JSON valid berupa ARRAY of object.
5. Setiap object memiliki key: name, price, description, image_path.

PERTANYAAN PENGGUNA:
{query_text}

DESKRIPSI GAMBAR INPUT PENGGUNA (HASIL ANALISIS GAMBAR):
{description}

HASIL PENCARIAN PRODUK:
{context_str}
"""

    response=llm.invoke(final_prompt_template)
    raw = response.content.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return []

    return result