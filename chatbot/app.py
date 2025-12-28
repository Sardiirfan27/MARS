import os
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

from google.genai.types import Part, Content, GenerateContentConfig # PENTING: Import eksplisit Part dan Content

# --- Konfigurasi API ---
# PENTING: Ambil API Key dari Environment Variable (Lebih aman dari hardcoding)
# Pastikan Anda mengatur GEMINI_API_KEY di lingkungan server Anda
# Jika tidak bisa menggunakan Environment Variable, ganti 'os.getenv("GEMINI_API_KEY")'
# dengan API Key Anda sebagai string. Contoh: client = genai.Client(api_key="AIza...")
API_KEY = os.getenv("GEMINI_API_KEY", "AIz-----") 
client = genai.Client(api_key=API_KEY)
model='gemini-2.5-flash-lite'

app = FastAPI(title="Gemini Proxy API")

# Izinkan CORS (Penting untuk akses dari frontend/web yang berbeda domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ganti dengan domain frontend Anda (misalnya: "http://localhost:5500")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Struktur data untuk request dari frontend
class Message(BaseModel):
    role: str
    parts: list[dict]

class GeminiRequest(BaseModel):
    # 'contents' menampung seluruh riwayat chat (history)
    contents: list[Message]

# Tambahkan endpoint GET untuk root, agar tidak 404
@app.get("/")
def read_root():
    return {"message": "Gemini Proxy API berjalan! Gunakan endpoint /generate untuk streaming."}

@app.post("/generate")
async def generate_content(request: GeminiRequest):
    """
    Endpoint Non-Streaming untuk meneruskan permintaan chat ke Gemini API
    """
    try:
        contents_for_sdk = []
        for msg in request.contents:
            sdk_parts = []
            
            for part in msg.parts:
                if 'text' in part and part['text']:
                    # Kasus Teks
                    sdk_parts.append(Part(text=part['text']))
                    
                elif 'inline_data' in part:
                    # Kasus Gambar (Inline Data Base64)
                    inline_data = part.get('inline_data')
                    if inline_data:
                        try:
                            # Ekstrak data base64 dan mime_type
                            base64_data = inline_data.get('data')
                            # print(base64_data)
                            # Ambil MIME Type dari payload, jika tidak ada, gunakan default JPEG (lebih umum)
                            mime_type = inline_data.get('mime_type', 'image/jpeg')
                            if base64_data is None:
                                raise ValueError("Missing 'data' field in inline_data.")
                            # # Decode base64 ke bytes
                            base64_bytes = base64.b64decode(base64_data)
                            # Membuat objek Part menggunakan data biner
                            sdk_parts.append(
                                Part.from_bytes(
                                    data=base64_bytes,
                                    mime_type=mime_type
                                )
                            )
                        except Exception as e:
                            print(f"Base64 Decode Error: {e} for MIME: {mime_type}")
                            raise HTTPException(
                                status_code=400, 
                                detail="Invalid inline image data."
                            )
                            
                
            contents_for_sdk.append(
                Content(
                    role=msg.role, 
                    parts=sdk_parts
                )
            )

        # Panggilan ke Gemini API menggunakan fungsi NON-STREAMING
        system_prompt = f'''Anda adalah AI Asisten bernama AI-NOID, Anda harus menjawab pertanyaan user dengan ramah dan emot,
        Jika pertanyaan tidak memiliki jawaban, Anda harus menjawab dengan "Maaf, saya tidak bisa menjawab pertanyaan tersebut,
        Jika bertanya apa itu MARS, jawab: MARS (Multimodal AI-Powered Furniture Recommender System) adalah aplikasi cerdas yang dapat merekomendasikan produk furniture berdasarkan pertanyaan pengguna dengan tepat dan akurat.
        Pengguna dapat memberikan input teks ataupun gambar untuk mencari produk yang sesuai.
        MARS dapat mengenali produk berdasarkan jenis produk, warna, material dan memberikan rekomendasi berdasarkan input ruangan yang anda berikan.
        Selain berkaitan dengan furniture, jangan jawab pertanyaan pengguna.
        
        '''
        
        response = client.models.generate_content(
            model=model,
            contents=contents_for_sdk,
            config=GenerateContentConfig(
                    system_instruction=system_prompt),
        )
        # cetak total token yang digunakan
        # print(f"Total prompt: {response.usage_metadata.prompt_token_count}")
        # print(f'Candidate token:{response.usage_metadata.candidates_token_count}')
        # print(f'Total token:{response.usage_metadata.total_token_count}')
        # Mengembalikan respons JSON yang bersih
        return {
            "text": response.text,
        }
        
    except APIError as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Gemini API Error (Coba lagi nanti): {str(e)}"
        )
    except Exception as e:
        # Menangkap error umum dan mencetaknya, yang membantu debugging
        print(f"Internal Server Error: {e}") 
        # Tambahkan error message ke HTTPException detail untuk debugging frontend
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# --- Jalankan Server ---
# Jalankan dengan command: uvicorn app:app --reload

# Ini akan berjalan di http://127.0.0.1:8000
