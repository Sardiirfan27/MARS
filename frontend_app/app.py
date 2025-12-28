import streamlit as st
import requests
from PIL import Image
import base64

import streamlit.components.v1 as components
from PIL import Image as PILImage
from io import BytesIO


image_base64 = None
image_url = None
image_mime_type = None

    
# Load CSS (optional)
with open('style/style.css',"r", encoding="utf-8") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def image_to_base64(uploaded_file) -> str:
    uploaded_file.seek(0)  # penting!
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

def resize_image_input(image_input: str, size=(512, 512)) -> str:
    """
    Resize image input (base64 string) menjadi ukuran tertentu.
    Mengembalikan base64 string.
    """
    try:
        image_bytes = base64.b64decode(image_input, validate=True)
        pil_image = PILImage.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        # Jika bukan base64, kembalikan as-is (misal URL)
        return image_input

    # Resize sambil mempertahankan aspect ratio
    pil_image.thumbnail(size, PILImage.Resampling.LANCZOS)

    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


FASTAPI_URL = "http://localhost:8000/search"

st.set_page_config(
    page_title="MARS (Multimodal AI-Powered Furniture Recommender System)",
    layout="wide"
)

st.title("🪑 MARS (Multimodal AI-Powered Furniture Recommender System)")
st.caption("Upload image + text → Search furniture")

# =========================
# Session state
# =========================
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

if "response_data" not in st.session_state:
    st.session_state.response_data = None

# =========================
# SIDEBAR — INPUT
# =========================
with st.sidebar:
    st.header("🔍 Input")

    with st.expander("💡 Contoh Prompt"):
        if st.button("🪑 Rekomendasi meja kayu"):
            st.session_state.query_text = "Berikan saya rekomendasi meja kayu"

        if st.button("🎮 Rekomendasi kursi gaming"):
            st.session_state.query_text = "Berikan saya rekomendasi kursi gaming"

        if st.button("🎮 Kursi gaming warna kuning"):
            st.session_state.query_text = "Berikan saya rekomendasi kursi gaming warna kuning"

        if st.button("🏠 Kursi untuk ruang tamu"):
            st.session_state.query_text = (
                "Berikan saya rekomendasi kursi yang cocok untuk ruangan tamu berikut"
            )

    query_text = st.text_area(
        "Masukan Detail Produk Yang Ingin Dicari",
        value=st.session_state.query_text,
        height=160,
        placeholder="Contoh: kursi gaming warna hitam dengan sandaran tinggi"
    )

    st.session_state.query_text = query_text

    uploaded_file = st.file_uploader(
        "Upload Image (optional)",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file:
        image_preview = Image.open(uploaded_file)
        image_bytes = uploaded_file.getvalue()  # ✅ SAFE
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_mime_type = uploaded_file.type 
        

        st.image(image_preview, caption="Preview", width="stretch")

    search_clicked = st.button("🚀 Search", width="stretch", key='search-button')

# =========================
# SEARCH ACTION
# =========================
if search_clicked:

    if not query_text.strip():
        st.error("Query text wajib diisi")
        st.stop()


    if uploaded_file:
        image_base64 = image_to_base64(uploaded_file)

    # image_preview = image_preview.convert("RGB")
    # image_preview.thumbnail((512, 512), Image.Resampling.LANCZOS)  # Resize
    # # Convert ke bytes & base64
    # buffered = BytesIO()
    # image_preview.save(buffered, format="JPEG")
    # image_bytes = buffered.getvalue()
    # image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "query_text": query_text,
        "image_base64": image_base64,
        "image_url": image_url,         # biasanya None
        "image_mime_type": image_mime_type
    }

    with st.spinner("Searching furniture..."):
        response = requests.post(FASTAPI_URL, json=payload)

    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    st.session_state.response_data = response.json()

# =========================
# MAIN AREA — OUTPUT
# =========================
if st.session_state.response_data:

    data = st.session_state.response_data

    st.subheader("🧠 Analysis")
    # st.write("**Is Furniture:**", data["is_furniture"])
    st.write("**Deskripsi:**", data["description"])

    st.divider()
    st.subheader("📦 Search Results")

    for r in data["results"]:
        with st.expander(r["metadata"].get("name", "Unknown")):
            st.write("**Score:**", r["score"])
            st.json(r["metadata"])

    st.divider()
    st.subheader("⭐ Recommendations")

    cols = st.columns(3, gap="medium")
    for i, rec in enumerate(data["recommendations"]):
        with cols[i % 3]:
            st.markdown(f"### {rec['name']}")
            st.write(f"💰 Rp {rec['price']:,}")
            st.write(rec["description"])

            if rec.get("image_path"):
                img_url = "https://storage.googleapis.com/" + rec["image_path"].replace("gs://", "")
                st.image(img_url, width="stretch")

def federated_chatbot_component(url, height=600):
    """
    Fungsi reusable untuk embedding chatbot dengan styling yang benar.
    """
    html_code = f""" 
    <div class="chatbot-float" style="z-index: 9999; position: fixed; width: 100%; height: {height}px; overflow: hidden; border-radius: 10px;">
        <iframe 
            src="{url}" 
            width="100%" 
            height="{height}" 
            frameborder="0" 
            style="border:none; overflow:hidden;"
            allowfullscreen>
        </iframe>
    </div>
    """
    return components.html(html_code, height=height + 20)

chatbot_url = "http://127.0.0.1:5500/chatbot/chatbot-standalone.html    "
federated_chatbot_component(chatbot_url)