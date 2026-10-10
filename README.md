# 🚗 Sistem Parkir Pintar (Dual-Layer Authentication: IoT RFID + Computer Vision ALPR)

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![AI-ObjectDetection](https://img.shields.io/badge/YOLO-v8-yellow.svg)](https://github.com/ultralytics/ultralytics)
[![AI-OCR](https://img.shields.io/badge/OCR-TensorFlow%2FKeras%20CNN-orange.svg)](https://www.tensorflow.org/)
[![IoT Hardware](https://img.shields.io/badge/IoT-ESP32%20%2B%20MFRC522-red.svg)](https://www.espressif.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20Firebase%20RTDB-brightgreen.svg)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Aplikasi desktop cerdas berbasis **Windows** untuk otomasi gerbang parkir dengan sistem **Keamanan Autentikasi Ganda (*Dual-Layer Authentication*)**: mencocokkan identitas kartu **RFID (IoT ESP32)** dengan **Plat Nomor Kendaraan (Computer Vision: YOLOv8 + CNN OCR)**, didukung arsitektur **Hybrid Database** (Offline-First SQLite lokal + Cloud Firebase Realtime Database) serta **Web Monitoring Dashboard**.

---

## 📌 Daftar Isi
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Fitur Utama](#-fitur-utama)
- [Pipeline Computer Vision & Kecerdasan Buatan](#-pipeline-computer-vision--kecerdasan-buatan)
- [Struktur Repositori](#-struktur-repositori)
- [Kebutuhan Perangkat](#-kebutuhan-perangkat)
- [Panduan Instalasi & Penggunaan](#-panduan-instalasi--penggunaan)
- [Konfigurasi Firebase](#-konfigurasi-firebase)
- [Integrasi Perangkat Keras (ESP32 RFID)](#-integrasi-perangkat-keras-esp32-rfid)
- [Dashboard Web Monitoring](#-dashboard-web-monitoring)
- [Skrip Penelitian Bab 4 Skripsi](#-skrip-penelitian-bab-4-skripsi)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph IoT["Perangkat Keras IoT"]
        A[Kartu RFID] -->|Tap| B[Sensor MFRC522]
        B -->|SPI| C[ESP32 Microcontroller]
        C -->|Serial USB 115200| D[Backend Python]
    end

    subgraph Vision["Computer Vision & AI"]
        Cam[Kamera 1080p] -->|Frame Real-time| D
        D -->|Lokalisasi Plat| YOLO["YOLOv8 (best.pt)"]
        YOLO -->|Plat Crop| Preprocess["Pre-processing: CLAHE + PCA Deskewing"]
        Preprocess -->|Karakter Satuan| CNN["Keras CNN (best_ocr_model.h5)"]
        CNN -->|Voting & FSM Koreksi| PlateResult["Hasil Plat Nomor Valid"]
    end

    subgraph Core["Backend & Logika Keamanan"]
        D --> Match{"Validasi RFID + Plat"}
        Match -->|Masuk: Plat Baru| AllowIn["✅ Gerbang Masuk Buka"]
        Match -->|Masuk: Plat Sudah Ada| DenyIn["⛔ Akses Ditolak (Kloning Plat)"]
        Match -->|Keluar: Plat Cocok| AllowOut["✅ Gerbang Keluar Buka"]
        Match -->|Keluar: Plat Beda| DenyOut["⛔ Akses Ditolak (Pencurian)"]
    end

    subgraph Storage["Penyimpanan Hybrid"]
        AllowIn & AllowOut --> SQLite[("SQLite Lokal (Offline-First)")]
        AllowIn & AllowOut & DenyIn & DenyOut --> Cloud[("Firebase Cloud RTDB")]
        D --> LocalDisk["Folder Bukti Foto (hasil_capture/)"]
    end

    subgraph UI["Antarmuka Pengguna"]
        D --> GUI["Desktop GUI PyQt6"]
        Cloud --> Web["Web Monitoring Dashboard"]
    end
```

---

## ✨ Fitur Utama

1. **Autentikasi Ganda (*Dual Authentication*)**: Mencegah kecurangan tiket/kartu hilang dengan memvalidasi pasangan identitas RFID dan visual plat nomor kendaraan.
2. **Anti-Tapping Palsu (*Anti-Passback*)**: Menolak akses masuk jika plat nomor yang sama terdeteksi masih berada di dalam area parkir.
3. **Pencegahan Pencurian Kendaraan**: Saat keluar, sistem memverifikasi apakah plat nomor kendaraan yang keluar 100% cocok dengan plat saat kartu tersebut pertama kali masuk.
4. **Offline-First SQLite**: Sistem gerbang tetap bekerja lancar dan cepat tanpa ketergantungan koneksi internet.
5. **Real-time Cloud Sync (Firebase)**: Otomatis mengirim data transaksi dan representasi foto Base64 ke Firebase Realtime Database saat terhubung internet.
6. **GUI Modern PyQt6 (Multi-threaded)**: Video streaming 60/30 FPS lancar di thread terpisah (`QThread`) tanpa freeze saat inferensi AI.
7. **Simulasi Tap RFID**: Tersedia tombol simulasi tap pada GUI untuk pengujian alur perangkat lunak tanpa modul hardware.
8. **Web Dashboard Terintegrasi**: Dashboard berbasis web untuk memantau kendaraan aktif, riwayat transaksi, dan rekaman peringatan keamanan dari mana saja.

---

## 📊 Hasil Evaluasi & Grafik Pelatihan Model (Bab 4 Skripsi)

Berdasarkan hasil pengujian pada dokumen skripsi:

### 1. Evaluasi Model YOLOv8 Nano (Lokalisasi Plat)
- **Dataset:** 500 citra kendaraan roda dua ([Roboflow Dataset](https://universe.roboflow.com/best-zwljf/tugasakhir-rvuug)).
- **Hasil Metrik:**
  - **Precision:** 98,03%
  - **Recall:** 95,90%
  - **mAP@0.50:** 98,51%
  - **mAP@0.50:0.95:** 92,99%
  - **Akurasi Deteksi Lapangan (30 Kendaraan):** 100% (30/30 pelat berhasil dilokalisasi).

![Grafik Pelatihan YOLOv8](assets/images/Grafik_Pelatihan_YOLOv8.png)
*Gambar: Grafik Box Loss & Mean Average Precision (mAP) YOLOv8 (Gambar 4.8 Skripsi)*

---

### 2. Evaluasi Model CNN (Klasifikasi Karakter OCR)
- **Dataset:** 47.985 citra karakter dalam 36 kelas alfanumerik `0-9` dan `A-Z` ([Kaggle Dataset](https://www.kaggle.com/datasets/caasperart/haarcascadeplatenumber)).
- **Hasil Metrik:**
  - **Training Accuracy:** 94,46% (Loss: 0,1936)
  - **Validation Accuracy:** 88,07% (Loss: 0,6317)
  - **Akurasi Pengenalan Pelat Utuh Lapangan (End-to-End):** 83,33% (25/30 pelat terbaca 100% tepat).

![Grafik Pelatihan OCR CNN](assets/images/Grafik_Pelatihan_OCR_CNN.jpg)
*Gambar: Grafik Akurasi & Loss Pelatihan vs Validasi CNN (Gambar 4.10 Skripsi)*

---


1. **Deteksi Plat (YOLOv8)**:
   - Menggunakan bobot terlatih `best.pt` dengan confidence threshold `0.5`.
   - Mengambil bounding box dengan area terbesar (kendaraan paling dekat gerbang).
2. **Prapemrosesan Citra Tingkat Lanjut**:
   - **Pemotongan Margin**: Menghilangkan 3% sisi kiri dan 1.5% sisi kanan plat untuk membuang bingkai putih yang berpotensi keliru terbaca huruf `'I'`.
   - **CLAHE (*Contrast Limited Adaptive Histogram Equalization*)**: Meratakan kontras pada kondisi plat kusam atau pencahayaan ekstrem.
   - **Otsu Binarization**: Segmentasi adaptif hitam-putih.
   - **Auto-Deskewing (PCA)**: Menghitung vektor kemiringan karakter menggunakan *Principal Component Analysis* dan merotasi otomatis jika kemiringan berkisar antara 3° s/d 40°.
   - **Y-Axis Median Alignment**: Memfilter kontur baut, emblem, atau logo Korlantas berdasarkan ketinggian median karakter utama.
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
├── best.pt                             # Model deteksi plat nomor (YOLOv8)
├── best_ocr_model.h5                   # Model OCR karakter plat (CNN Keras)
├── requirements.txt                    # Daftar dependency Python
├── .gitignore                          # Aturan ignore file rahasia & temporer
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
│   └── images/                         # Grafik hasil evaluasi Bab 4
│       ├── Grafik_Evaluasi_Final.png
│       ├── Grafik_Evaluasi_GPU.png
│       └── grafik_pelatihan_ocr.png
│
├── scripts/                            # Skrip penelitian Bab 4 Skripsi
│   ├── README.md                       # Dokumentasi skrip penelitian
│   ├── train_ocr.py                    # Pelatihan model CNN OCR (test.py)
│   ├── balance_dataset.py              # Augmentasi dataset karakter (dataseimbang.py)
│   ├── pengujian_bab4.py               # GUI pengambilan data pengujian (uji.py)
│   └── dashboard_analisis.py           # Dashboard analisis computer vision (analisis.py)
│
└── hasil_capture/                      # Direktori penyimpanan foto bukti masuk/keluar
    └── .gitkeep
```

---

## 💻 Kebutuhan Perangkat

### Software
- **Sistem Operasi**: Windows 10 / 11 (64-bit direkomendasikan).
- **Python**: Python 3.9, 3.10, atau 3.11.
- **Arduino IDE**: Versi 2.0+ (dengan board ESP32 & library MFRC522 terpasang).
- **Driver USB**: CP210x atau CH340 sesuai modul USB-to-UART pada ESP32 Anda.

### Hardware
- **Webcam / Kamera USB**: Resolusi minimal 720p (disarankan 1080p).
- **Mikrokontroler**: ESP32 DevKit V1 (30 atau 38 pin).
- **Modul RFID**: MFRC522 13.56 MHz + Kartu/Tag RFID Mifare 1K.
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
Buka file `kunci-firebase.json` dan ganti isinya dengan kunci privat Service Account dari proyek Firebase Console Anda (lihat [Konfigurasi Firebase](#-konfigurasi-firebase)).

### 5. Jalankan Aplikasi
Pastikan kamera dan ESP32 sudah terhubung, lalu jalankan:
```powershell
python main_gui.py
```

---

## 🔐 Konfigurasi Firebase

Proyek ini menggunakan **Firebase Realtime Database** untuk sinkronisasi data cloud.

1. Buka [Firebase Console](https://console.firebase.google.com/) dan buat proyek baru.
2. Buat **Realtime Database** pada lokasi `asia-southeast1` (Singapura) dengan mode pengujian (*test mode*) atau aturan baca-tulis autentikasi.
3. Buka **Project Settings** > **Service accounts**.
4. Klik **Generate new private key**, lalu simpan file JSON tersebut dengan nama `kunci-firebase.json` di root folder aplikasi ini.
5. ⚠️ **PERINGATAN KEAMANAN:** File `kunci-firebase.json` asli sudah dimasukkan ke `.gitignore` agar tidak pernah ter-commit ke GitHub publik.

---

## 🔌 Integrasi Perangkat Keras (ESP32 RFID)

Hubungkan pin modul **MFRC522** ke **ESP32** sesuai tabel berikut:

| Pin RC522 | Pin ESP32 | Keterangan |
|-----------|-----------|------------|
| 3.3V      | 3.3V      | ⚠️ **Jangan hubungkan ke 5V!** |
| RST       | GPIO 22   | Reset |
| GND       | GND       | Ground |
| MISO      | GPIO 19   | VSPI MISO |
| MOSI      | GPIO 23   | VSPI MOSI |
| SCK       | GPIO 18   | VSPI SCK |
| SDA (SS)  | GPIO 21   | Slave Select |

Buka sketch pada `arduino/esp32_rfid/esp32_rfid.ino` di Arduino IDE, lalu upload ke board ESP32 Anda. Penjelasan lengkap tersedia di [arduino/README.md](arduino/README.md).

---

## 🌐 Dashboard Web Monitoring

Dashboard web yang berada di folder `web_dashboard/` dapat dijalankan secara lokal atau di-deploy ke Firebase Hosting:

### Menjalankan Lokal:
Cukup buka file `web_dashboard/index.html` langsung melalui browser web Anda.

### Deploy ke Firebase Hosting:
```powershell
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

---

## 🧪 Skrip Penelitian Bab 4 Skripsi

Untuk mereproduksi hasil pelatihan atau pengujian pada laporan Skripsi/Tugas Akhir:

- `python scripts/train_ocr.py` : Melatih model CNN untuk mengenali karakter plat nomor.
- `python scripts/balance_dataset.py` : Menyeimbangkan dataset karakter sebelum training.
- `python scripts/pengujian_bab4.py` : GUI khusus untuk mengambil foto uji Bab 4 (YOLO, OCR, Gabungan).
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
