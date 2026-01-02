# MARS (*Multimodal AI-Powered Furniture Recommender System*)

**MARS** adalah aplikasi cerdas berbasis **Artificial Intelligence (AI)** yang dirancang untuk membantu pengguna menemukan furnitur yang paling sesuai dengan preferensi pribadi mereka, seperti **warna produk, bahan, gaya, dan atribut lainnya**.

Dengan menggabungkan:

* **Pemrosesan teks**
* **Analisis gambar**
* **Multimodal embeddings**

MARS mampu memahami maksud pengguna secara kontekstual dan mendalam, jauh melampaui sistem rekomendasi tradisional berbasis rule atau metadata sederhana.

🎥 **Demo Aplikasi**
👉 [https://youtu.be/WjVX-1Qbzrw?si=wmKIwiPXkVmP0qOn](https://youtu.be/WjVX-1Qbzrw?si=wmKIwiPXkVmP0qOn)

---

## 📦 Arsitektur Umum

* **Chatbot** → Interaksi natural language (Gemini API)
* **FastAPI Backend** → Sistem rekomendasi & API
* **Streamlit Frontend** → Antarmuka pengguna
* **Pinecone** → Vector database
* **Google Cloud Platform (GCP)**

  * Cloud Storage (penyimpanan gambar)
  * Vertex AI (multimodal embedding & inference)

---

## ⚙️ Setup & Installation

### 1️⃣ Membuat Virtual Environment

Buat dan aktifkan virtual environment sesuai OS Anda.

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

---

### 2️⃣ Install Dependencies

Setiap folder memiliki `requirements.txt` masing-masing.
Lakukan instalasi di **setiap folder berikut**:

* `chatbot/`
* `fastapi_app/`
* `frontend_app/`

Contoh:

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Menyiapkan Vector Database (Pinecone)

1. Jalankan notebook:

   ```
   recommender_system.ipynb
   ```
2. Notebook ini akan:

   * Memproses data
   * Membuat embedding multimodal
   * Menyimpan embedding ke **Pinecone**

⚠️ **Catatan penting:**
Sebelum menjalankan notebook, Anda **harus meng-upload folder `images/` ke Google Cloud Storage (GCS)**.

---

### 4️⃣ Konfigurasi Google Cloud Platform (GCP)

#### a. Service Account

* Buat **Service Account**
* Berikan role:

  * ✅ `Vertex AI Administrator`

(Lihat detail pada video demo aplikasi)

#### b. Aktifkan Services GCP

Jalankan perintah berikut di **terminal lokal atau Cloud Shell**:

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  logging.googleapis.com \
  storage-component.googleapis.com \
  aiplatform.googleapis.com
```

---

## 🤖 Menjalankan Chatbot

### 1️⃣ Konfigurasi Environment

* Dapatkan **Gemini API Key**
* Masukkan ke file `.env` di folder:

  ```
  chatbot/.env
  ```

### 2️⃣ Jalankan Backend Chatbot

Masuk ke folder `chatbot` lalu jalankan:

```bash
uvicorn app:app --host 0.0.0.0 --port 8001
```

⚠️ **Catatan:**
Gunakan **FastAPI + Uvicorn**, **bukan localhost-only**, agar kompatibel dengan sistem lain.

---

## 🚀 Menjalankan Recommendation System

### 1️⃣ Konfigurasi `.env` (Root Folder)

Pastikan `.env` di root folder berisi:

* API Key Pinecone
* Path JSON Service Account GCP
* `PROJECT_ID`
* `REGION`
* Konfigurasi Vertex AI

---

### 2️⃣ Jalankan FastAPI Backend

Masuk ke folder `fastapi_app`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### 3️⃣ Jalankan Frontend (Streamlit)

Masuk ke folder `frontend_app`:

```bash
streamlit run app.py
```
Buka di browser link berikut:
```
http://localhost:8501
```

---

