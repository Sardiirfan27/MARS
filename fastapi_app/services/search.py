from collections import defaultdict
import operator
from fastapi_app.config import pinecone_index


# Default jumlah hasil yang dikembalikan
TOP_K = 4


def process_pinecone_results(
    results,
    combined_scores: dict,
    vector_type: str,
    min_score: float
):
    """
    Memproses hasil query Pinecone untuk satu modalitas (text atau image)
    dan menggabungkannya ke dalam dictionary skor gabungan.

    Fungsi ini:
    - Memfilter hasil berdasarkan skor minimum (min_score)
    - Mengelompokkan hasil berdasarkan product_id
    - Menyimpan skor sesuai modalitas (text_score / image_score)
    - Menyimpan metadata produk (hanya sekali per product)

    Args:
        results:
            Hasil query dari Pinecone (index.query).
        combined_scores (dict):
            Dictionary agregasi skor antar modalitas.
            Struktur:
            {
              product_id: {
                "text_score": float,
                "image_score": float,
                "metadata": dict | None
              }
            }
        vector_type (str):
            Jenis vektor yang diproses.
            Nilai yang valid: "text" atau "image".
        min_score (float):
            Skor minimum per modalitas agar hasil dipertimbangkan.
    """
    for match in results.matches:
        # Lewati hasil dengan skor rendah
        if match.score < min_score:
            continue

        # Ambil product_id (tanpa suffix -text / -image)
        product_id = match.id.rsplit("-", 1)[0]

        # Simpan metadata hanya sekali
        if not combined_scores[product_id]["metadata"]:
            combined_scores[product_id]["metadata"] = match.metadata

        # Simpan skor sesuai modalitas
        combined_scores[product_id][f"{vector_type}_score"] = match.score


def search_multimodal(
    query_vector_text,
    query_vector_image,
    text_weight: float = 1.0,
    image_weight: float = 1.0,
    min_score: float = 0.5,
    top_k: int = TOP_K
):
    """
    Melakukan pencarian multimodal (Text + Image) di Pinecone dan
    mengembalikan hasil yang sudah di-rerank berdasarkan skor gabungan.

    Alur proses:
    1. Query Pinecone menggunakan embedding teks dan gambar jika ada
    2. Gabungkan skor kemiripan berdasarkan teks dan gambar
    3. Hitung skor gabungan berbobot, jika tidak ada query gambar tapi ada teks maka weight_sum = 1, jika ada gambar dan teks maka weight_sum =2
    4. Filter & urutkan hasil berdasarkan skor akhir

    Args:
        query_vector_text:
            Embedding vektor teks hasil query.
        query_vector_image:
            Embedding vektor gambar hasil query.
        text_weight (float):
            Bobot kontribusi skor teks.
        image_weight (float):
            Bobot kontribusi skor gambar.
        min_score (float):
            Skor minimum (per modalitas dan gabungan).
        top_k (int):
            Jumlah hasil akhir yang dikembalikan.

    Returns:
        List[dict]:
            Daftar hasil pencarian terurut, masing-masing berisi:
            {
              "id": str,
              "score": float,
              "metadata": dict
            }
    """

    # Dictionary agregasi skor text & image per produk
    combined_scores = defaultdict(lambda: {
        "text_score": 0.0,
        "image_score": 0.0,
        "metadata": None
    })

    
    # --- Query berbasis teks ---
    if query_vector_text:
        text_results = pinecone_index.query(
            vector=query_vector_text,
            top_k=top_k,
            include_metadata=True,
            filter={"vector_type": "text"}
        )
        process_pinecone_results(
            text_results, combined_scores, "text", min_score
        )

    # --- Query berbasis gambar ---
    if query_vector_image:
        image_results = pinecone_index.query(
            vector=query_vector_image,
            top_k=top_k,
            include_metadata=True,
            filter={"vector_type": "image"}
        )
        process_pinecone_results(
            image_results, combined_scores, "image", min_score
        )

       # --- Reranking (dynamic weight per product) ---
    results = []

    for product_id, data in combined_scores.items():
        score_sum = 0.0
        weight_sum = 0.0

        if query_vector_text is not None and data["text_score"] > 0:
            score_sum += data["text_score"] * text_weight
            weight_sum += text_weight # tambah 1 jika ada teks

        if query_vector_image is not None and data["image_score"] > 0:
            score_sum += data["image_score"] * image_weight
            weight_sum += image_weight # tambahkan 1 lagi jika ada gambar

        # Tidak ada kontribusi sama sekali
        if weight_sum == 0:
            continue

        combined_score = score_sum / weight_sum

        if combined_score >= min_score:
            results.append({
                "id": product_id,
                "score": combined_score,
                "metadata": data["metadata"]
            })

    # --- Sort & Top-K ---
    return sorted(
        results,
        key=operator.itemgetter("score"),
        reverse=True
    )[:top_k]
