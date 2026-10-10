# 🚗 Sistem Parkir Pintar (Dual-Layer Authentication: IoT RFID + Computer Vision ALPR)

[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-taparkir--4d34d.web.app-blue?style=for-the-badge&logo=firebase)](https://taparkir-4d34d.web.app/)
[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![AI-ObjectDetection](https://img.shields.io/badge/YOLO-v8-yellow.svg)](https://github.com/ultralytics/ultralytics)
[![AI-OCR](https://img.shields.io/badge/OCR-TensorFlow%2FKeras%20CNN-orange.svg)](https://www.tensorflow.org/)
[![IoT Hardware](https://img.shields.io/badge/IoT-ESP32%20%2B%20MFRC522-red.svg)](https://www.espressif.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20Firebase%20RTDB-brightgreen.svg)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Aplikasi desktop cerdas berbasis **Windows** untuk otomasi gerbang parkir dengan sistem **Keamanan Autentikasi Ganda (*Dual-Layer Authentication*)**: memvalidasi identitas kartu **RFID e-KTP (IoT ESP32)** dengan **Plat Nomor Kendaraan (Computer Vision: YOLOv8 + CNN OCR)**, didukung arsitektur **Hybrid Database** (Offline-First SQLite lokal + Cloud Firebase Realtime Database) serta **Web Monitoring Dashboard**.

🌐 **Akses Dashboard Web Real-time:** [https://taparkir-4d34d.web.app/](https://taparkir-4d34d.web.app/)

---

## 📌 Daftar Isi
- [Live Web Monitoring](#-live-web-monitoring)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Hasil Evaluasi & Grafik Pelatihan Model (Bab 4 Skripsi)](#-hasil-evaluasi--grafik-pelatihan-model-bab-4-skripsi)
- [Fitur Utama](#-fitur-utama)
- [Pipeline Computer Vision & Kecerdasan Buatan](#-pipeline-computer-vision--kecerdasan-buatan)
- [Struktur Repositori](#-struktur-repositori)
- [Kebutuhan Perangkat](#-kebutuhan-perangkat)
- [Panduan Instalasi & Penggunaan](#-panduan-instalasi--penggunaan)
- [Konfigurasi Firebase](#-konfigurasi-firebase)
- [Integrasi Perangkat Keras (ESP32 RFID)](#-integrasi-perangkat-keras-esp32-rfid)
- [Skrip Penelitian Bab 4 Skripsi](#-skrip-penelitian-bab-4-skripsi)
- [Troubleshooting](#-troubleshooting)

---

## 🌐 Live Web Monitoring

Sistem terhubung langsung ke cloud untuk kebutuhan monitoring jarak jauh:

👉 **URL Dashboard Resmi:** [https://taparkir-4d34d.web.app/](https://taparkir-4d34d.web.app/)

Fitur pemantauan pada website:
1. **Panel Log & Peringatan Keamanan**: Merekam insiden penolakan akses secara *real-time* (misalnya jika kartu RFID ditap pada kendaraan yang berbeda dari data saat masuk).
2. **Panel Kendaraan Parkir Aktif**: Menampilkan jumlah dan daftar kendaraan yang saat ini sedang berada di dalam area parkir.
3. **Panel Riwayat Transaksi**: Mencatat seluruh histori masuk dan keluar kendaraan beserta bukti foto tangkapan kamera.

---

## 🏗️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph IoT["Perangkat Keras IoT"]
        A[Kartu RFID e-KTP] -->|Tap| B[Sensor MFRC522]
        B -->|SPI| C[ESP32 Microcontroller]
        C -->|Serial USB 115200| D[Backend Python]
    end

    subgraph Vision["Computer Vision & AI"]
        Cam[Kamera 1080p] -->|Frame Real-time| D
        D -->|Lokalisasi Plat| YOLO["YOLOv8 Nano (best.pt)"]
        YOLO -->|Plat Crop| Preprocess["Pre-processing: CLAHE + PCA Deskewing"]
        Preprocess -->|Karakter Satuan| CNN["Keras CNN (best_ocr_model.h5)"]
        CNN -->|Voting & FSM Koreksi| PlateResult["Hasil Plat Nomor Valid"]
    end

    subgraph Core["Backend & Logika Keamanan"]
        D --> Match{"Validasi RFID + Plat"}
        Match -->|Masuk: Plat Baru| AllowIn["✅ Gerbang Masuk Buka"]
        Match -->|Masuk: Plat Sudah Ada| DenyIn["⛔ Akses Ditolak (Kloning Plat)"]
        Match -->|Keluar: Plat Cocok| AllowOut["✅ Gerbang Keluar Buka"]
        Match -->|Keluar: Plat Beda| DenyOut["⛔ Akses Ditolak (Pencegahan Pencurian)"]
    end

    subgraph Storage["Penyimpanan Hybrid"]
        AllowIn & AllowOut --> SQLite[("SQLite Lokal (Offline-First)")]
        AllowIn & AllowOut & DenyIn & DenyOut --> Cloud[("Firebase Cloud RTDB")]
        D --> LocalDisk["Folder Bukti Foto (hasil_capture/)"]
    end

    subgraph UI["Antarmuka Pengguna"]
        D --> GUI["Desktop GUI PyQt6"]
        Cloud --> Web["Web Monitoring Dashboard (taparkir-4d34d.web.app)"]
    end
```

---

## 📊 Angka-Angka Hasil Pengujian Sistem (Bab 4 Skripsi)

Seluruh angka hasil pengujian di bawah ini diambil langsung dari hasil evaluasi resmi pada laporan Tugas Akhir:

### 1. Hasil Pengujian Model YOLOv8 Nano (Gambar 4.8 Skripsi)

![Grafik Pelatihan YOLOv8](assets/images/Grafik_Pelatihan_YOLOv8.png)
*Gambar 4.8: Grafik Box Loss & Mean Average Precision (mAP) YOLOv8 Nano*

| Metrik Evaluasi | Nilai Numerik | Persentase | Keterangan |
| :--- | :---: | :---: | :--- |
| **Precision** | `0,98034` | **98,03%** | Tingkat ketepatan deteksi bounding box |
| **Recall** | `0,95897` | **95,90%** | Tingkat keberhasilan menemukan area plat |
| **mAP@0.50** | `0,98508` | **98,51%** | Rata-rata presisi pada threshold IoU 0,50 |
| **mAP@0.50:0.95** | `0,92985` | **92,99%** | Rata-rata presisi pada rentang IoU 0,50 s/d 0,95 |
| **Training Box Loss (Akhir)** | `0,29206` | - | Nilai error posisi box pada data training |
| **Validation Box Loss (Akhir)** | `0,39947` | - | Nilai error posisi box pada data validasi |
| **Keberhasilan Deteksi (50 Data Testing)** | `50 / 50` | **100,00%** | Seluruh citra uji berhasil dilokalisasi |

---

### 2. Hasil Pengujian Model OCR CNN (Gambar 4.10 Skripsi)

![Grafik Pelatihan OCR CNN](assets/images/Grafik_Pelatihan_OCR_CNN.jpg)
*Gambar 4.10: Grafik Akurasi & Loss Pelatihan vs Validasi Model CNN*

| Metrik Evaluasi | Nilai Numerik | Persentase | Keterangan |
| :--- | :---: | :---: | :--- |
| **Training Accuracy (Akhir)** | `0,9446` | **94,46%** | Akurasi klasifikasi pada data latih |
| **Validation Accuracy (Akhir)** | `0,8807` | **88,07%** | Akurasi klasifikasi karakter individual |
| **Training Loss (Akhir)** | `0,1936` | - | Nilai loss error data latih |
| **Validation Loss (Akhir)** | `0,6317` | - | Nilai loss error data validasi |

---

### 3. Hasil Pengujian Sistem Terintegrasi Lapangan (Tabel 4.5 Skripsi)

| Parameter Pengujian | Jumlah Sampel | Persentase | Status |
| :--- | :---: | :---: | :--- |
| **Total Pengujian Lapangan** | `30` | **100,00%** | Pengujian langsung menggunakan kamera gerbang |
| **Pelat Berhasil Dideteksi YOLO** | `30` | **100,00%** | 30 dari 30 plat berhasil dilokalisasi |
| **Pelat Gagal Dideteksi YOLO** | `0` | **0,00%** | Tidak ada kegagalan deteksi bounding box |
| **Pengenalan Pelat Utuh Sesuai (OCR Benar)** | `25` | **83,33%** | 25 dari 30 pelat dikenali utuh tanpa salah karakter |
| **Pengenalan Pelat Tidak Sesuai (OCR Gagal)** | `5` | **16,67%** | Kesalahan minor pada karakter mirip |

---

### 4. Hasil Pengujian Modul RFID RC522 & ESP32 (Tabel 4.1 & 4.2 Skripsi)

| Parameter Pengujian | Nilai Capaian | Keterangan |
| :--- | :---: | :--- |
| **Jumlah Sampel UID e-KTP Berbeda** | `11 UID` | Pengujian multi-kartu identitas |
| **Total Pengujian Berulang** | `55 kali` | Setiap kartu diuji sebanyak 5 kali |
| **Pembacaan Berhasil** | `55 kali (100,00%)` | Seluruh pembacaan sukses tanpa kegagalan |
| **Pembacaan Gagal** | `0 kali (0,00%)` | Keandalan hardware sempurna |
| **Waktu Respons Minimum** | `5,00 ms` | Kecepatan pembacaan tercepat |
| **Waktu Respons Maksimum** | `6,00 ms` | Kecepatan pembacaan terlambat |
| **Rata-rata Waktu Respons** | **5,64 ms** | Rata-rata transmisi serial ESP32 ke laptop |

---

### 5. Hasil Pengujian Integrasi Autentikasi Ganda (Tabel 4.6 Skripsi)

| No | Skenario Pengujian Gerbang | Respon yang Diharapkan | Respon Aktual Sistem | Status |
| :-: | :--- | :--- | :--- | :-: |
| 1 | UID baru + Plat nomor belum aktif | Akses Masuk Diterima | Akses Masuk Diterima | **Sesuai (100%)** |
| 2 | UID baru + Plat nomor sudah ada di dalam | Akses Ditolak (Anti-Passback) | Akses Ditolak | **Sesuai (100%)** |
| 3 | UID aktif + Plat saat keluar sesuai saat masuk | Akses Keluar Diterima | Akses Keluar Diterima | **Sesuai (100%)** |
| 4 | UID aktif + Plat saat keluar beda saat masuk | Akses Ditolak (Anti-Pencurian) | Akses Ditolak | **Sesuai (100%)** |

---

## ✨ Fitur Utama

1. **Autentikasi Ganda (*Dual Authentication*)**: Mencegah kecurangan kartu hilang/ditukar dengan mencocokkan identitas UID RFID dan identitas visual plat kendaraan.
2. **Anti-Tapping Palsu (*Anti-Passback*)**: Menolak akses masuk jika plat nomor yang sama terdeteksi masih tercatat berada di dalam area parkir.
3. **Pencegahan Pencurian Kendaraan**: Saat keluar, sistem memverifikasi apakah plat kendaraan yang keluar 100% cocok dengan plat saat kartu tersebut pertama kali masuk.
4. **Offline-First SQLite**: Sistem gerbang tetap bekerja lancar dan cepat tanpa ketergantungan koneksi internet.
5. **Real-time Cloud Sync (Firebase)**: Otomatis mengirim data transaksi dan representasi foto Base64 ke Firebase Realtime Database saat terhubung internet.
6. **GUI Modern PyQt6 (Multi-threaded)**: Video streaming real-time di thread terpisah (`QThread`) tanpa freeze saat inferensi AI.
7. **Simulasi Tap RFID**: Tombol simulasi tap pada GUI untuk pengujian alur perangkat lunak tanpa modul hardware.
8. **Perlindungan Privasi**: Data sensitif pada dokumentasi disamarkan untuk keamanan dan kepatuhan privasi data.

---

## 🧠 Pipeline Computer Vision & Kecerdasan Buatan

1. **Deteksi Plat (YOLOv8 Nano)**:
   - Menggunakan bobot terlatih `best.pt` dengan confidence threshold `0.5`.
   - Mengambil bounding box dengan area terbesar (kendaraan paling depan/dekat gerbang).
2. **Prapemrosesan Citra Tingkat Lanjut**:
   - **Pemotongan Margin**: Menghilangkan 3% sisi kiri dan 1.5% sisi kanan plat untuk membuang bingkai putih yang berpotensi keliru terbaca huruf `'I'`.
   - **CLAHE (*Contrast Limited Adaptive Histogram Equalization*)**: Meratakan kontras pada kondisi plat kusam atau pencahayaan ekstrem.
   - **Otsu Binarization**: Segmentasi adaptif hitam-putih.
   - **Auto-Deskewing (PCA)**: Menghitung sudut kemiringan karakter menggunakan *Principal Component Analysis* dan merotasi otomatis (rentang 3° s/d 40°).
   - **Y-Axis Median Alignment**: Memfilter kontur baut, emblem, atau logo berdasarkan ketinggian median karakter utama.
3. **Pengenalan Karakter (CNN Keras)**:
   - Klasifikasi 36 kelas karakter alphanumeric (`0-9` dan `A-Z`) menggunakan `best_ocr_model.h5`.
   - Normalisasi kanvas 28×28 piksel dengan *proportional padding* 4 piksel agar ujung lengkungan angka tidak terpotong.
4. **FSM & Heuristic Post-Processing**:
   - Menyesuaikan pola plat Indonesia: Karakter awal pasti Huruf Wilayah, karakter tengah pasti Angka, karakter akhir pasti Huruf Suffix.
   - **Sensor Kontur Pinggang (*Waistline Sensor*)**: Menganalisis kurva batas kanan karakter untuk membedakan huruf berlekuk `'B'` vs angka `'8'`, serta `'O'` vs `'0'`.
   - **Voting Temporal Multi-frame**: Menstabilkan hasil deteksi dari beberapa frame berturut-turut menggunakan `collections.Counter`.

---

## 📁 Struktur Repositori

```text
SistemParkir/
├── MainProgramTA.py                    # Backend core: MesinParkirThread, AI, IoT, DB
├── main_gui.py                         # Frontend GUI desktop (PyQt6)
├── best.pt                             # Model deteksi plat nomor (YOLOv8 Nano)
├── best_ocr_model.h5                   # Model OCR karakter plat (CNN Keras)
├── requirements.txt                    # Daftar dependency Python
├── .gitignore                          # Aturan ignore file kredensial, DB lokal, dan cache
├── LICENSE                             # Lisensi proyek (MIT)
├── README.md                           # Dokumentasi utama proyek
│
├── config/
│   ├── config.py                       # Konfigurasi terpusat (kamera, port, path)
│   └── kunci-firebase.json.example     # Template kredensial Firebase Service Account
│
├── arduino/
│   ├── README.md                       # Panduan lengkap wiring & setup ESP32
│   └── esp32_rfid/
│       └── esp32_rfid.ino              # Firmware Arduino IDE untuk ESP32 + RC522
│
├── web_dashboard/                      # Monitoring dashboard berbasis web (Firebase)
│   ├── index.html                      # Halaman antarmuka web monitoring
│   ├── style.css                       # Desain tampilan dashboard web
│   ├── 404.html                        # Halaman fallback 404
│   ├── firebase.json                   # Konfigurasi Firebase Hosting
│   └── .firebaserc                     # Inisialisasi ID proyek Firebase
│
├── assets/
│   ├── fonts/                          # Font plat nomor untuk pengujian
│   │   ├── font_plat.ttf
│   │   └── font_plat_standar.ttf
│   └── images/                         # Grafik resmi hasil pelatihan (Bab 4 Skripsi)
│       ├── Grafik_Pelatihan_YOLOv8.png # Gambar 4.8 Skripsi (Box Loss & mAP)
│       └── Grafik_Pelatihan_OCR_CNN.jpg# Gambar 4.10 Skripsi (Akurasi & Loss CNN)
│
├── scripts/                            # Skrip penelitian Bab 4 Skripsi
│   ├── README.md                       # Dokumentasi skrip penelitian
│   ├── train_ocr.py                    # Pelatihan model CNN OCR
│   ├── balance_dataset.py              # Augmentasi dataset karakter seimbang
│   ├── pengujian_bab4.py               # GUI pengambilan data pengujian Bab 4
│   └── dashboard_analisis.py           # Dashboard analisis computer vision
│
└── hasil_capture/                      # Direktori penyimpanan foto bukti masuk/keluar
    └── .gitkeep
```

---

## 💻 Kebutuhan Perangkat

### Software
- **Sistem Operasi**: Windows 10 / 11 (64-bit).
- **Python**: Python 3.9, 3.10, atau 3.11.
- **Arduino IDE**: Versi 2.0+ (dengan board ESP32 & library MFRC522 terpasang).
- **Driver USB**: CP210x atau CH340 sesuai modul USB-to-UART pada ESP32 Anda.

### Hardware
- **Webcam / Kamera USB**: Resolusi 1080p disarankan (minimal 720p).
- **Mikrokontroler**: ESP32 DevKit V1 (30 atau 38 pin).
- **Modul RFID**: MFRC522 13.56 MHz + Kartu e-KTP / Tag RFID Mifare 1K.
- **Kabel Jumper & Kabel Data USB**.

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Clone Repositori
```powershell
git clone https://github.com/USERNAME/SistemParkir.git
Set-Location SistemParkir
```

### 2. Buat dan Aktifkan Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> *Catatan:* Jika eksekusi skrip dibatasi oleh sistem Windows, jalankan perintah berikut:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

### 3. Instal Dependency
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Konfigurasi Kredensial Firebase
Salin file template konfigurasi ke root direktori proyek:
```powershell
Copy-Item .\config\kunci-firebase.json.example .\kunci-firebase.json
```
Isi file `kunci-firebase.json` dengan kunci privat Service Account dari Firebase Console Anda (lihat [Konfigurasi Firebase](#-konfigurasi-firebase)).

### 5. Jalankan Aplikasi Desktop
Pastikan kamera dan ESP32 sudah terhubung, lalu jalankan:
```powershell
python main_gui.py
```

---

## 🔐 Konfigurasi Firebase

Proyek ini menggunakan **Firebase Realtime Database** untuk sinkronisasi data cloud.

1. Buka [Firebase Console](https://console.firebase.google.com/) dan buat proyek baru.
2. Buat **Realtime Database** pada lokasi `asia-southeast1` (Singapura) dengan aturan baca-tulis yang sesuai.
3. Buka **Project Settings** > **Service accounts**.
4. Klik **Generate new private key**, lalu simpan file JSON tersebut dengan nama `kunci-firebase.json` di root folder aplikasi.
5. ⚠️ **PERINGATAN KEAMANAN:** File `kunci-firebase.json` asli secara otomatis diabaikan oleh `.gitignore` sehingga tidak akan terunggah ke repositori publik.

---

## 🔌 Integrasi Perangkat Keras (ESP32 RFID)

Hubungkan pin modul **MFRC522** ke **ESP32** sesuai tabel berikut:

| Pin RC522 | Pin ESP32 | Keterangan |
|-----------|-----------|------------|
| 3.3V      | 3.3V      | ⚠️ **Jangan hubungkan ke 5V!** |
| RST       | GPIO 22   | Reset Pin |
| GND       | GND       | Ground Bersama |
| MISO      | GPIO 19   | VSPI MISO |
| MOSI      | GPIO 23   | VSPI MOSI |
| SCK       | GPIO 18   | VSPI SCK |
| SDA (SS)  | GPIO 21   | Slave Select (SS) |

Buka sketch pada `arduino/esp32_rfid/esp32_rfid.ino` di Arduino IDE, lalu upload ke board ESP32 Anda. Penjelasan lengkap tersedia di [arduino/README.md](arduino/README.md).

---

## 🧪 Skrip Penelitian Bab 4 Skripsi

Untuk mereproduksi hasil pelatihan atau pengujian:

- `python scripts/train_ocr.py` : Melatih model CNN untuk mengenali karakter plat nomor.
- `python scripts/balance_dataset.py` : Menyeimbangkan dataset karakter sebelum pelatihan.
- `python scripts/pengujian_bab4.py` : GUI khusus pengambilan data pengujian evaluasi.
- `python scripts/dashboard_analisis.py` : Dashboard visual untuk menganalisis akurasi segmentasi citra.

Dokumentasi rinci skrip ini dapat dibaca di [scripts/README.md](scripts/README.md).

---

## ❓ Troubleshooting

| Masalah | Penyebab Umum | Solusi |
|---------|---------------|--------|
| `ModuleNotFoundError` | Virtual environment belum aktif atau library belum terinstal | Pastikan prompt terminal menampilkan `(.venv)` lalu jalankan `pip install -r requirements.txt`. |
| `Modul RFID tidak terdeteksi` | Port COM tidak cocok atau kabel USB belum terpasang | Cek port COM ESP32 di Device Manager, lalu sesuaikan port pada list `SERIAL_PORTS` di `MainProgramTA.py`. Gunakan tombol **Simulasi Tap RFID** di GUI untuk pengujian cepat. |
| `Kamera tidak terbuka` | Indeks kamera salah atau kamera sedang dipakai aplikasi lain | Tutup aplikasi lain yang memakai kamera. Ubah indeks `cv2.VideoCapture(0)` menjadi `1` atau `2` jika menggunakan webcam eksternal. |
| `Gagal koneksi Firebase` | File `kunci-firebase.json` belum diisi atau tidak ditemukan | Salin template `config/kunci-firebase.json.example` ke root dengan nama `kunci-firebase.json` dan isi dengan kredensial asli. |

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi **MIT License** - lihat berkas [LICENSE](LICENSE) untuk rincian lengkap.
