from typing import Tuple, List
from vertexai.vision_models import MultiModalEmbeddingModel, Image
import requests
from io import BytesIO
import base64
# from PIL import Image

def decode_base64_image(b64: str) -> bytes:
    try:
        return base64.b64decode(b64, validate=True)
    except Exception:
        raise ValueError("Invalid base64 image string")

class VertexAIMultiModalEmbeddings:
    def __init__(self, model_name="multimodalembedding@001", dimension=128):
        
        self.model = MultiModalEmbeddingModel.from_pretrained(model_name)
        self.dimension = dimension


    def embed_text(
        self,
        contextual_text: str
    ) -> List[float]:
        
        result = self.model.get_embeddings(
            contextual_text=contextual_text,
            dimension=self.dimension,
        )
        return result.text_embedding
    
    def embed_image(
        self,
        image_input: str
    ) -> List[float]:
    
        if not image_input:
            raise ValueError("image_input is required for embed_image")

        # URL
        if image_input.startswith(("http://", "https://")):
            response = requests.get(image_input, timeout=10)
            response.raise_for_status()
            image = Image(image_bytes=response.content)
        
         # Penanganan jika image_input adalah GCS (gs://)
        elif image_input.startswith("gs://"):
            image = Image.load_from_file(image_input)

        # Penanganan jika image_input adalah Local File
        else:
            image = Image.load_from_file(image_input)

        # Eksekusi embedding
        result = self.model.get_embeddings(
            image=image,
            dimension=self.dimension,
        )
        
        return result.image_embedding
    

    
    def embed_image_and_text(
        self,
        image_input: str,
        contextual_text: str
    ) -> Tuple[List[float], List[float]]:
        
        if image_input in [None, ""]:
            image = None
    
        # Penaganan jika image_input BASE64
        elif decode_base64_image(image_input):
            image_bytes = decode_base64_image(image_input)
            image = Image(image_bytes=image_bytes)
        
        # Penanganan jika image_input adalah URL (http/https)
        elif image_input.startswith(("http://", "https://")):
            try:
                response = requests.get(image_input, timeout=10)
                response.raise_for_status() # Pastikan download berhasil
                
                # Load image dari bytes (Memory Buffer)
                image = Image(image_bytes=response.content)
            except Exception as e:
                raise Exception(f"Gagal mengunduh gambar dari URL: {str(e)}")
       
        # Penanganan jika image_input adalah GCS (gs://)
        elif image_input.startswith("gs://"):
            image = Image.load_from_file(image_input)
        
        # Jika image_input upload (bytes)
        elif isinstance(image_input, bytes):
            image = Image(image_bytes=image_input)

        else:
            raise ValueError("Format image_input tidak didukung")
        # Eksekusi embedding
        result = self.model.get_embeddings(
            image=image,
            contextual_text=contextual_text,
            dimension=self.dimension,
        )
        
        return result.image_embedding, result.text_embedding
    
