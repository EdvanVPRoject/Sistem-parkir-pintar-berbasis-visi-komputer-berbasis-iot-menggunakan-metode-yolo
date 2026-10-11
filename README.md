# 🏍️ Sistem Parkir Pintar Berbasis IoT dan Visi Komputer Menggunakan Metode YOLO

[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-taparkir--4d34d.web.app-blue?style=for-the-badge&logo=firebase)](https://taparkir-4d34d.web.app/)
[![Python Version](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![AI-ObjectDetection](https://img.shields.io/badge/YOLO-v8_Nano-yellow.svg)](https://github.com/ultralytics/ultralytics)
[![AI-OCR](https://img.shields.io/badge/OCR-TensorFlow%2FKeras%20CNN-orange.svg)](https://www.tensorflow.org/)
[![IoT Hardware](https://img.shields.io/badge/Hardware-ESP32%20%2B%20RC522-red.svg)](https://www.espressif.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20Firebase-brightgreen.svg)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Aplikasi desktop cerdas berbasis **Windows** untuk otomasi gerbang parkir **kendaraan bermotor roda dua (sepeda motor)** dengan sistem **Autentikasi Ganda (*Dual-Layer Authentication*)**: memvalidasi identitas pengguna melalui **UID e-KTP (RFID RC522 + ESP32)** dengan identitas fisik kendaraan melalui **Pengenalan Pelat Nomor (YOLOv8 Nano + CNN OCR + FSM Rule-Based Correction)**, didukung arsitektur **Hybrid Database** (Offline-First SQLite lokal + Cloud Firebase Realtime Database) serta **Website Dashboard IoT**.

🌐 **Akses Dashboard Web Real-time:** [https://taparkir-4d34d.web.app/](https://taparkir-4d34d.web.app/)

---

## 📌 Daftar Isi
- [Live Web Monitoring](#-live-web-monitoring)
- [Perancangan & Arsitektur Sistem (Bab 3 Skripsi)](#-perancangan--arsitektur-sistem-bab-3-skripsi)
  - [Blok Diagram Sistem Keseluruhan](#1-blok-diagram-sistem-keseluruhan-gambar-31-skripsi)
  - [Alur Komunikasi Perangkat Keras](#2-alur-perangkat-keras-gambar-32-skripsi)
  - [Diagram Alir Sistem Utama (Flowchart)](#3-diagram-alir-sistem-utama-gambar-33-skripsi)
  - [Alur Pra-pemrosesan, Segmentasi, dan Pengenalan Karakter CNN](#4-alur-pra-pemrosesan-segmentasi-dan-pengenalan-karakter-cnn-gambar-36-skripsi)
  - [Arsitektur Model CNN untuk Klasifikasi Karakter](#5-arsitektur-model-cnn-untuk-klasifikasi-karakter-gambar-37-skripsi)
  - [Diagram Alir Rule-Based Correction](#6-diagram-alir-rule-based-correction-gambar-38-skripsi)
  - [Struktur Database Firebase](#7-struktur-database-firebase-gambar-39-skripsi)
- [Angka-Angka Hasil Pengujian Sistem (Bab 4 Skripsi)](#-angka-angka-hasil-pengujian-sistem-bab-4-skripsi)
  - [Hasil Pelatihan YOLOv8 Nano](#1-hasil-pengujian-model-yolov8-nano-gambar-48-skripsi)
  - [Hasil Pelatihan OCR CNN](#2-hasil-pengujian-model-ocr-cnn-gambar-410-skripsi)
  - [Hasil Pengujian Terintegrasi Lapangan](#3-hasil-pengujian-sistem-terintegrasi-lapangan-tabel-45-skripsi)
  - [Hasil Pengujian Respons RFID RC522](#4-hasil-pengujian-modul-rfid-rc522--esp32-tabel-41--42-skripsi)
  - [Hasil Pengujian Integrasi Autentikasi Ganda](#5-hasil-pengujian-integrasi-autentikasi-ganda-tabel-46-skripsi)
- [Struktur Repositori](#-struktur-repositori)
- [Kebutuhan Perangkat](#-kebutuhan-perangkat)
- [Panduan Instalasi & Penggunaan](#-panduan-instalasi--penggunaan)
- [Konfigurasi Firebase](#-konfigurasi-firebase)
- [Integrasi Perangkat Keras ESP32](#-integrasi-perangkat-keras-esp32)
- [Lisensi](#-lisensi)

---

## 🌐 Live Web Monitoring

Sistem terhubung langsung ke cloud untuk kebutuhan monitoring jarak jauh tanpa mengganggu kecepatan operasional gerbang lokal:

👉 **URL Dashboard Resmi:** [https://taparkir-4d34d.web.app/](https://taparkir-4d34d.web.app/)

Fitur pemantauan pada website:
1. **Log Status & Peringatan Keamanan**: Merekam rekam jejak insiden penolakan akses (seperti ketidakcocokan UID e-KTP dengan pelat nomor sepeda motor).
2. **Data Kendaraan Parkir Aktif**: Menampilkan jumlah dan daftar sepeda motor yang sedang berada di dalam area parkir.
3. **Data Riwayat Parkir**: Mencatat seluruh riwayat transaksi masuk dan keluar beserta bukti visual foto tangkapan kamera.

---

## 🏛️ Perancangan & Arsitektur Sistem (Bab 3 Skripsi)

Seluruh arsitektur, diagram blok, alur perangkat keras, flowchart, dan rancangan model di bawah ini diambil langsung dari dokumen resmi Skripsi:

### 1. Blok Diagram Sistem Keseluruhan (Gambar 3.1 Skripsi)

Menggambarkan hubungan antara perangkat masukan (*input*), unit pemrosesan utama (*proses*), penyimpanan data hybrid (*database*), dan media keluaran (*output*):

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_1_Blok_Diagram.png" alt="Gambar 3.1 Blok Diagram Sistem" width="750"/>
</p>

*Gambar 3.1: Blok Diagram Sistem Keseluruhan*

---

### 2. Alur Perangkat Keras (Gambar 3.2 Skripsi)

Menunjukkan integrasi komunikasi fisik antara kartu e-KTP, sensor pembaca RFID, mikrokontroler, kamera, dan komputer:

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_2_Alur_Perangkat_Keras.png" alt="Gambar 3.2 Alur Perangkat Keras" width="750"/>
</p>

*Gambar 3.2: Alur Komunikasi Antarperangkat Keras*

- **Kartu e-KTP ke Modul RFID RC522**: Gelombang Radio Frekuensi RF 13,56 MHz (ISO/IEC 14443A).
- **Modul RFID RC522 ke ESP32**: Jalur komunikasi SPI (*Serial Peripheral Interface*).
- **ESP32 ke Laptop**: Komunikasi Serial via Kabel USB (Baudrate 115200).
- **Webcam ke Laptop**: Koneksi USB DirectShow (Resolusi 1920 × 1080 piksel, target 30 FPS).
- **Laptop ke Speaker**: Media audio output notifikasi suara validasi gerbang.

---

### 3. Diagram Alir Sistem Utama (Gambar 3.3 Skripsi)

Menggambarkan alur logika eksekusi perangkat lunak dari mulai deteksi kendaraan hingga keputusan pembukaan gerbang:

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_3_Diagram_Alir_Sistem_Utama.png" alt="Gambar 3.3 Diagram Alir Sistem Utama" width="500"/>
</p>

*Gambar 3.3: Diagram Alir Sistem Utama (Flowchart)*

---

### 4. Alur Pra-pemrosesan, Segmentasi, dan Pengenalan Karakter CNN (Gambar 3.6 Skripsi)

Tahap pengenalan karakter dilakukan melalui pipeline bertahap:
1. **Langkah 1: Citra Input** (Hasil crop ROI dari bounding box YOLOv8).
2. **Langkah 2: Binerisasi** (Konversi Grayscale, CLAHE pencahayaan, Gaussian Blur, dan Otsu Thresholding).
3. **Langkah 3: Segmentasi** (Ekstraksi kontur karakter dengan auto-deskewing PCA & penyelarasan sumbu-Y).
4. **Langkah 4: Hasil Klasifikasi** (Inferensi CNN 36 kelas karakter alfanumerik `0-9` dan `A-Z`).

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_6_Alur_Pengenalan_Karakter_CNN.png" alt="Gambar 3.6 Alur Pra-pemrosesan, Segmentasi, dan Pengenalan Karakter CNN" width="750"/>
</p>

*Gambar 3.6: Alur Pra-pemrosesan, Segmentasi, dan Pengenalan Karakter CNN*

---

### 5. Arsitektur Model CNN untuk Klasifikasi Karakter (Gambar 3.7 Skripsi)

Arsitektur model CNN yang digunakan:
- Input citra grayscale 28 × 28 × 1 kanal.
- **Conv2D (1)**: 32 filter 3×3 + ReLU $\rightarrow$ **MaxPooling2D** (Pool 2×2).
- **Conv2D (2)**: 64 filter 3×3 + ReLU $\rightarrow$ **MaxPooling2D** (Pool 2×2).
- **Flatten** (1.600 vektor fitur) $\rightarrow$ **Dense** (128 neuron + ReLU) $\rightarrow$ **Dropout (0.5)**.
- **Output Layer**: Dense 36 neuron dengan fungsi aktivasi **Softmax**.

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_7_Arsitektur_Model_CNN.png" alt="Gambar 3.7 Arsitektur Model CNN untuk Klasifikasi Karakter" width="750"/>
</p>

*Gambar 3.7: Arsitektur Model CNN untuk Klasifikasi Karakter*

---

### 6. Diagram Alir Rule-Based Correction (Gambar 3.8 Skripsi)

Memperbaiki kesalahan klasifikasi visual huruf dan angka yang mirip berdasarkan struktur Tanda Nomor Kendaraan Bermotor (TNKB) Indonesia (Kode Wilayah $\rightarrow$ Nomor Registrasi $\rightarrow$ Huruf Seri):

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_8_Diagram_Alir_Rule_Based_Correction.png" alt="Gambar 3.8 Diagram Alir Rule-Based Correction" width="750"/>
</p>

*Gambar 3.8: Diagram Alir Logika Rule-Based Correction*

- Dilengkapi **Sensor Kontur Pinggang (*Waistline Sensor*)** untuk membedakan karakter berlekuk `B` vs `8` dan `O` vs `0` berdasarkan profil tepi kanan biner.

---

### 7. Struktur Database Firebase (Gambar 3.9 Skripsi)

Struktur data NoSQL pada Firebase Realtime Database dibagi menjadi 3 node utama:

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Gambar_3_9_Struktur_Tabel_Firebase.png" alt="Gambar 3.9 Struktur Tabel Firebase" width="650"/>
</p>

*Gambar 3.9: Struktur Node Data pada Firebase Realtime Database*

- `log_keamanan`: Menyimpan insiden penolakan (`<id_log>`, `foto_url`, `keterangan`, `plat_nomor`, `rfid_uid`, `status`, `waktu`).
- `parkir_aktif`: Menyimpan kendaraan yang sedang di dalam (`<rfid_uid>`, `foto_url`, `plat_nomor`, `waktu_masuk`).
- `riwayat_parkir`: Menyimpan log transaksi selesai (`<id_transaksi>`, `foto_url`, `plat_nomor`, `rfid_uid`, `status`, `waktu_masuk`, `waktu_keluar`).

---

## 📊 Angka-Angka Hasil Pengujian Sistem (Bab 4 Skripsi)

Seluruh angka hasil pengujian di bawah ini diambil langsung dari hasil evaluasi resmi pada laporan Tugas Akhir:

### 1. Hasil Pengujian Model YOLOv8 Nano (Gambar 4.8 Skripsi)

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Grafik_Pelatihan_YOLOv8.png" alt="Gambar 4.8 Grafik Hasil Pelatihan Model YOLOv8" width="750"/>
</p>

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

<p align="center">
  <img src="https://taparkir-4d34d.web.app/assets/images/Grafik_Pelatihan_OCR_CNN.png" alt="Gambar 4.10 Grafik Hasil Pelatihan Model OCR CNN" width="750"/>
</p>

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
| **Total Pengujian Lapangan** | `30` | **100,00%** | Pengujian langsung pada gerbang sepeda motor |
| **Pelat Berhasil Dideteksi YOLO** | `30` | **100,00%** | 30 dari 30 pelat berhasil dilokalisasi |
| **Pelat Gagal Dideteksi YOLO** | `0` | **0,00%** | Tidak ada kegagalan deteksi bounding box |
| **Pengenalan Pelat Utuh Sesuai (OCR Benar)** | `25` | **83,33%** | 25 dari 30 pelat dikenali utuh tanpa salah karakter |
| **Pengenalan Pelat Tidak Sesuai (OCR Gagal)** | `5` | **16,67%** | Kesalahan minor pada karakter mirip |

---

### 4. Hasil Pengujian Modul RFID RC522 & ESP32 (Tabel 4.1 & 4.2 Skripsi)

| Parameter Pengujian | Nilai Capaian | Keterangan |
| :--- | :---: | :--- |
| **Jumlah Sampel UID e-KTP Berbeda** | `11 UID` | Pengujian multi-kartu identitas e-KTP |
| **Total Pengujian Berulang** | `55 kali` | Setiap kartu diuji sebanyak 5 kali |
| **Pembacaan Berhasil** | `55 kali (100,00%)` | Seluruh pembacaan hardware berhasil |
| **Pembacaan Gagal** | `0 kali (0,00%)` | Keandalan hardware sempurna |
| **Waktu Respons Minimum** | `5,00 ms` | Kecepatan pembacaan tercepat |
| **Waktu Respons Maksimum** | `6,00 ms` | Kecepatan pembacaan terlambat |
| **Rata-rata Waktu Respons** | **5,64 ms** | Rata-rata transmisi serial ESP32 ke laptop |

---

### 5. Hasil Pengujian Integrasi Autentikasi Ganda (Tabel 4.6 Skripsi)

| No | Skenario Pengujian Gerbang | Respon yang Diharapkan | Respon Aktual Sistem | Status |
| :-: | :--- | :--- | :--- | :-: |
| 1 | UID baru + Plat nomor belum aktif | Akses Masuk Diterima | Akses Masuk Diterima | **Sesuai (100%)** |
| 2 | UID baru + Plat nomor sudah ada di dalam | Akses Ditolak (*Anti-Passback*) | Akses Ditolak | **Sesuai (100%)** |
| 3 | UID aktif + Plat saat keluar sesuai saat masuk | Akses Keluar Diterima | Akses Keluar Diterima | **Sesuai (100%)** |
| 4 | UID aktif + Plat saat keluar beda saat masuk | Akses Ditolak (*Anti-Pencurian*) | Akses Ditolak | **Sesuai (100%)** |

---

## 📁 Struktur Repositori

```text
SistemParkir/
├── MainProgramTA.py                    # Backend core: MesinParkirThread, AI, IoT, DB
├── main_gui.py                         # Frontend GUI desktop (PyQt6)
├── best.pt                             # Model deteksi pelat nomor (YOLOv8 Nano)
├── best_ocr_model.h5                   # Model OCR karakter pelat (CNN Keras)
├── requirements.txt                    # Daftar dependency Python
├── .gitignore                          # Aturan ignore kredensial, DB lokal, dan cache
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
│   ├── fonts/                          # Font pelat nomor untuk pengujian
│   │   ├── font_plat.ttf
│   │   └── font_plat_standar.ttf
│   └── images/                         # Diagram resmi arsitektur & grafik pelatihan skripsi
│       ├── Gambar_3_1_Blok_Diagram.png
│       ├── Gambar_3_2_Alur_Perangkat_Keras.png
│       ├── Gambar_3_3_Diagram_Alir_Sistem_Utama.png
│       ├── Gambar_3_6_Alur_Pengenalan_Karakter_CNN.png
│       ├── Gambar_3_7_Arsitektur_Model_CNN.png
│       ├── Gambar_3_8_Diagram_Alir_Rule_Based_Correction.png
│       ├── Gambar_3_9_Struktur_Tabel_Firebase.png
│       ├── Grafik_Pelatihan_YOLOv8.png
│       └── Grafik_Pelatihan_OCR_CNN.png
│
├── scripts/                            # Skrip penelitian Bab 4 Skripsi
│   ├── README.md                       # Dokumentasi skrip penelitian
│   ├── train_ocr.py                    # Pelatihan model CNN OCR
│   ├── balance_dataset.py              # Augmentasi dataset karakter seimbang
│   ├── pengujian_bab4.py               # GUI pengambilan data pengujian evaluasi
│   └── dashboard_analisis.py           # Dashboard analisis computer vision
│
└── hasil_capture/                      # Direktori penyimpanan foto bukti masuk/keluar
    └── .gitkeep
```

---

## 💻 Kebutuhan Perangkat

### Software
- **Sistem Operasi**: Windows 10 / 11 (64-bit).
- **Python**: Python 3.10.
- **Arduino IDE**: Versi 2.0+ (dengan board ESP32 & library MFRC522 terpasang).
- **Driver USB**: CP210x atau CH340 sesuai modul USB-to-UART pada ESP32.

### Hardware
- **Webcam / Kamera USB**: Resolusi 1080p disarankan (minimal 720p).
- **Mikrokontroler**: ESP32 DevKit V1 (30 atau 38 pin).
- **Modul RFID**: MFRC522 13.56 MHz + Kartu e-KTP / Tag RFID Mifare 1K.
- **Kabel Jumper & Kabel Data USB**.

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Clone Repositori
```powershell
git clone https://github.com/EdvanNr/Sistem-parkir-pintar-berbasis-visi-komputer-berbasis-iot-menggunakan-metode-yolo-.git
Set-Location Sistem-parkir-pintar-berbasis-visi-komputer-berbasis-iot-menggunakan-metode-yolo-
```

### 2. Buat dan Aktifkan Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

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
2. Buat **Realtime Database** pada lokasi `asia-southeast1` (Singapura).
3. Buka **Project Settings** > **Service accounts**.
4. Klik **Generate new private key**, lalu simpan file JSON tersebut dengan nama `kunci-firebase.json` di root folder aplikasi.
5. ⚠️ **PERINGATAN KEAMANAN:** File `kunci-firebase.json` asli secara otomatis diabaikan oleh `.gitignore` sehingga aman dari kebocoran ke publik.

---

## 🔌 Integrasi Perangkat Keras ESP32

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

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi **MIT License** - lihat berkas [LICENSE](LICENSE) untuk rincian lengkap.
