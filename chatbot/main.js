// =================================================================
// KONFIGURASI DAN INICIALISASI
// =================================================================

// Ganti dengan endpoint FastAPI Non-Streaming Anda
const FASTAPI_NON_STREAMING_ENDPOINT = "http://127.0.0.1:8001/generate"; 

// DOM Elements
const floatingContainer = document.querySelector(".floating-chat-container");
const chatWindow = document.getElementById("chatWindow");
const messagesBox = document.getElementById("messages");
const textInput = document.getElementById("textInput");
const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const previewContainer = document.getElementById("previewContainer");
const chatHint = document.getElementById("chatHint");

// STATE MANAGEMENT
let selectedImage = null; // Menyimpan objek File
let chatHistory = []; // Menyimpan riwayat percakapan untuk konteks

// =================================================================
// FUNGSI UTILITY (Tampilan dan State)
// =================================================================

// Fungsi untuk membuka chat window
function openChat() {
    chatWindow.style.display = "flex";
    // PENTING: Menyembunyikan floating container untuk menghindari konflik z-index
    floatingContainer.style.display = "none"; 
    
    // Memberi sambutan saat chat dibuka (jika belum ada history)
    if (messagesBox.children.length === 0) {
        addMessage("Halo! Saya AI-NOID Assistant. Bagaimana saya bisa membantu Anda hari ini?", "bot");
    }
    messagesBox.scrollTop = messagesBox.scrollHeight;
    textInput.focus();
}

// Fungsi untuk menutup chat window (dipanggil dari tombol X)
function toggleChat() { 
    chatWindow.style.display = "none";
    // Menampilkan kembali floating container
    floatingContainer.style.display = "flex"; 
    chatHint.style.opacity = '1';
    chatHint.style.pointerEvents = 'auto';
}

// Fungsi untuk mereset seluruh sesi chat (Dipanggil dari tombol 🔄)
function resetChat() {
    chatHistory = []; // Reset History
    messagesBox.innerHTML = ""; // Bersihkan tampilan
    textInput.value = "";
    clearImagePreview();
    addMessage("Sesi chat baru telah dimulai. Silakan bertanya!", "bot");
    textInput.focus();
}

// Menghapus pratinjau gambar
function clearImagePreview() {
    selectedImage = null;
    imageInput.value = ""; 
    preview.src = "";
    previewContainer.style.display = "none";
}

// Handler pratinjau gambar
imageInput.onchange = function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert("File yang diunggah harus berupa gambar.");
        clearImagePreview();
        return;
    }

    selectedImage = file;
    const url = URL.createObjectURL(file);
    preview.src = url;
    previewContainer.style.display = "block";
};

// Utility function to convert File to Base64
function toBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Ambil Data URL lengkap
            const dataUrl = reader.result;
            // Pisahkan untuk mendapatkan Base64 murni (bagian setelah koma)
            const base64String = dataUrl.split(',')[1];   
            // Verifikasi: Jika pemisahan gagal atau hasilnya kosong, tolak Promise.
            if (!base64String) {
                return reject(new Error("Gagal mengurai Base64 dari Data URL."));
            }   
            resolve(base64String); // Mengembalikan Base64 murni
        };
        
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

// Menambahkan pesan ke tampilan UI
function addMessage(text, sender = "bot", imgURL = null, messageId = null, is_loading = false) {
    const div = document.createElement("div");
    div.className = `msg ${sender}`;

    if (messageId) {
        div.id = messageId;
    }

    if (imgURL) {
        const im = document.createElement("img");
        im.src = imgURL;
        im.alt = "Gambar terlampir";
        div.appendChild(im);
    }
    
    // *** Perbaikan: Tambahkan kontainer span untuk teks agar Markdown rendering rapi ***
    const textContent = document.createElement("span");
    textContent.className = "message-text";
    div.appendChild(textContent);
    // *** Akhir Perbaikan ***

    if (text) {
        if (is_loading) {
            const loadingDiv = document.createElement("div");
            loadingDiv.className = "loading-message";
            loadingDiv.innerHTML = `${text}<span></span><span></span><span></span>`;
            textContent.appendChild(loadingDiv);
        } else {
            // Merender Markdown untuk balasan Bot
            if (sender === "bot") {
                textContent.innerHTML = marked.parse(text); 
            } else {
                textContent.innerText = text; // Untuk user, teks murni
            }
        }
    }

    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    // Mengembalikan elemen div utama (untuk kebutuhan penghapusan loading)
    return div; 
}


// =================================================================
// FUNGSI UTAMA (Interaksi API - NON-STREAMING ke FastAPI Proxy)
// =================================================================

async function sendMsg() {
    const text = textInput.value.trim();
    if (!text && !selectedImage) return;

    const fileToProcess = selectedImage; 
    const imgURL = fileToProcess ? URL.createObjectURL(fileToProcess) : null;

    // Tampilkan pesan user di UI
    addMessage(text, "user", imgURL);

    // Bersihkan input dan preview
    textInput.value = "";
    clearImagePreview(); 
    textInput.disabled = true; // Nonaktifkan input selama proses

    // --- LOGIKA PESAN LOADING ---
    const loadingMessageId = "loading-" + Date.now();
    const loadingElement = addMessage("Sedang memproses", "bot", null, loadingMessageId, true);
    // ----------------------------

    // 1. Build parts untuk pesan user saat ini
    const userParts = [];
    if (text) userParts.push({ text });

    // Konversi gambar ke Base64 jika ada
    if (fileToProcess) {
        try {
            const base64 = await toBase64(fileToProcess); 
                userParts.push({
                    inline_data: {
                        mime_type: fileToProcess.type,
                        data: base64 
                    }
            });
        } catch (e) {
            loadingElement.remove();
            addMessage("⚠️ Gagal memproses gambar.", "bot");
            console.error("Error konversi Base64:", e);
            textInput.disabled = false;
            return;
        }
    }
    
    // 2. Tambahkan pesan user saat ini ke history
    chatHistory.push({ role: "user", parts: userParts });

    // 3. Persiapkan body request: Kirim seluruh history sebagai konteks
    const requestBody = { contents: chatHistory };
    
    // 4. Panggilan API (fetch) ke FastAPI Proxy
    try {
        const resp = await fetch(
            FASTAPI_NON_STREAMING_ENDPOINT, // TARGET FASTAPI NON-STREAMING
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody)
            }
        );

        // Jika respons HTTP bukan 200/201, baca detail error dari body FastAPI
        if (!resp.ok) {
            let errorDetail = `HTTP Error: ${resp.status}`;
            try {
                const errorData = await resp.json();
                errorDetail = errorData.detail || errorDetail;
            } catch {}
            throw new Error(errorDetail);
        }

        // Baca respons JSON dari FastAPI (Mengharapkan {"text": "..."})
        const data = await resp.json();
        const botReply = data.text || "⚠️ Tidak ada respon teks dari proxy.";
        
        loadingElement.remove(); // Hapus pesan loading
        
        // Tampilkan balasan bot
        addMessage(botReply, "bot");
        
        // 5. Simpan balasan Bot ke history 
        chatHistory.push({ 
            role: "model", 
            parts: [{ text: botReply }] 
        });
        
    } catch (err) {
        loadingElement.remove(); 
        addMessage(`⚠️ Terjadi error: ${err.message || 'API gagal merespons.'}`, "bot");
        console.error("Fetch Error:", err);
        
        // Jika API gagal, hapus pesan user terakhir dari history 
        chatHistory.pop(); 
    } finally {
        textInput.disabled = false;
        textInput.focus();
    }
}

// Agar tombol 'Kirim' juga berfungsi dengan Enter
textInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) { 
        event.preventDefault();
        sendMsg();
    }
});
