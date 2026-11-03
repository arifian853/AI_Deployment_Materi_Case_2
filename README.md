# Case 2 — Chatbot Customer Service dengan Groq dan PDF

Backend FastAPI untuk chatbot CS berbahasa Indonesia. **PDF disediakan oleh sistem di `knowledge/base_knowledge.pdf`**, bukan diunggah atau dipilih oleh pengguna API. Aplikasi membaca file tersebut saat startup, mengekstrak teks setiap halaman, lalu mengirim seluruh teksnya sebagai konteks ke model Groq `openai/gpt-oss-120b` pada setiap request. Ini bukan RAG: tidak ada embedding, vector database, chunk retrieval, atau proses indexing.

Model ID dan contoh penggunaan Python SDK mengikuti [dokumentasi resmi Groq](https://console.groq.com/docs/model/openai/gpt-oss-120b). Setiap panggilan API mengirim isi PDF ke Groq, sehingga ukuran dokumen memengaruhi latensi, biaya, dan penggunaan token. Gunakan hanya dokumen yang boleh dikirim ke layanan tersebut.

## File proyek

| File | Fungsi |
| --- | --- |
| `app.py` | Endpoint `/health` dan `/chat`, validasi input, panggilan Groq. |
| `knowledge.py` | Ekstraksi teks PDF beserta penanda halaman. |
| `requirements.txt` | Dependensi instalasi dengan pip. |
| `.env.example` | Contoh konfigurasi. Salin menjadi `.env`. |
| `knowledge/base_knowledge.pdf` | PDF tetap milik sistem, dibaca saat server menyala. |

## Menjalankan

Gunakan Python 3.11 atau lebih baru. Dari direktori `case_2`, di PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Di macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Isi `GROQ_API_KEY` di `.env` dengan kunci Groq milik Anda. PDF sudah tersedia di `knowledge/base_knowledge.pdf`. Pengguna chatbot hanya mengirim pertanyaan ke `/chat`; mereka tidak mengirim file PDF. Lalu jalankan:

```sh
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Buka `http://127.0.0.1:8000/docs` untuk mencoba API. Jika PDF tidak tersedia atau API key belum diisi, server tetap menyala agar dokumentasi dapat dibuka, tetapi `/health` dan `/chat` mengembalikan HTTP 503. Setelah mengganti PDF atau `.env`, **restart server** agar konten dimuat ulang.

`.env` dan PDF di folder `knowledge` diabaikan oleh Git. Jangan masukkan API key ke kode atau request. API ini belum menyediakan autentikasi untuk pengunjung; pasang gateway/autentikasi dan HTTPS sebelum diekspos ke internet.

## Konfigurasi `.env`

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `GROQ_API_KEY` | tidak ada | Wajib untuk memanggil Groq. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model Groq yang dipanggil. |
| `MAX_PDF_CHARS` | `60000` | Batas karakter teks ekstraksi. Dokumen yang melampaui batas ditolak, tidak dipotong diam-diam. Minimal 1000. |

PDF saat ini berisi 2 halaman dengan sekitar 3.672 karakter teks yang dapat diekstrak. Judulnya **“SOP Pengadaan Barang dan Penggunaan AI”**, berstatus **draf untuk persetujuan manajemen**. Karena itu chatbot diarahkan menyebut status draf bila relevan dan tidak menganggap isinya sebagai kebijakan final. Dokumen ini membahas SOP internal, sehingga pertanyaan CS di luar topik tersebut kemungkinan akan dijawab sebagai informasi yang belum tersedia. Jawaban model diarahkan untuk menyebut nomor halaman; tetap periksa jawabannya karena model bahasa dapat keliru. Jika PDF kelak diganti dengan hasil scan/gambar, lakukan OCR terlebih dahulu.

## API

### `GET /health`

Mengembalikan `status`, `model`, dan `knowledge_file` jika siap. HTTP 503 memuat daftar masalah konfigurasi atau PDF.

### `POST /chat`

Body JSON:

```json
{
  "message": "Bagaimana cara mengajukan komplain?",
  "history": [
    {"role": "user", "content": "Halo"},
    {"role": "assistant", "content": "Halo, ada yang bisa saya bantu?"}
  ]
}
```

`message` wajib, panjang 1–4000 karakter, dan tidak boleh hanya spasi. `history` opsional, paling banyak 10 pesan. Tiap pesan history berisi `role` (`user` atau `assistant`) dan `content` 1–4000 karakter. Kirim history berurutan dari pesan terlama ke terbaru. Backend tidak menyimpan sesi: aplikasi klien menyimpan percakapan dan mengirim ulang history yang diperlukan pada setiap request. Pesan dengan role `system` dan field tambahan ditolak (HTTP 422).

Contoh PowerShell:

```powershell
$body = @{ message = "Bagaimana cara mengajukan komplain?"; history = @() } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -ContentType "application/json" -Body $body
```

Respons sukses:

```json
{
  "answer": "Teks jawaban dari model berdasarkan PDF, bila tersedia.",
  "model": "openai/gpt-oss-120b",
  "knowledge_file": "base_knowledge.pdf"
}
```

Contoh di atas menunjukkan **bentuk respons**, bukan jawaban aktual. HTTP 502 berarti panggilan Groq atau respons model gagal; HTTP 503 berarti konfigurasi/PDF belum siap; HTTP 422 berarti input tidak valid.

## Batasan pendekatan

Seluruh PDF dikirim pada setiap request, sehingga pendekatan ini sesuai untuk dokumen teks yang relatif singkat. Jika teks melebihi `MAX_PDF_CHARS`, layanan tidak siap sampai dokumennya diringkas atau arsitekturnya diubah. Teks dari PDF bersifat referensi dan tidak boleh dipercaya sebagai instruksi; prompt sudah meminta model mengabaikan perintah di dalam dokumen, tetapi itu bukan jaminan keamanan mutlak. Untuk informasi CS yang penting, verifikasi jawaban dan sediakan eskalasi ke petugas manusia.
