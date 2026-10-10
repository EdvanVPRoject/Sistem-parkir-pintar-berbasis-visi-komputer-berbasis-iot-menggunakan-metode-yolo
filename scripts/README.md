# Skrip Pelatihan, Pengujian, dan Analisis (Bab 4 Skripsi)

Direktori ini berisi skrip eksperimen pendukung yang digunakan selama penelitian dan penyusunan Tugas Akhir:

## 1. `train_ocr.py` (Pelatihan Model CNN OCR)
- **Fungsi:** Melatih model arsitektur Convolutional Neural Network (CNN) untuk mengenali 36 kelas karakter plat nomor Indonesia (`0-9` dan `A-Z`).
- **Fitur:** 
  - Deteksi dan akselerasi GPU NVIDIA (CUDA) dengan proteksi *VRAM Memory Growth*.
  - Callback *EarlyStopping*, *ModelCheckpoint*, dan *ReduceLROnPlateau*.
  - Evaluasi akurasi dan penyimpanan grafik pelatihan (`grafik_pelatihan_ocr.png`).
- **Output:** Menyimpan model bobot akhir `best_ocr_model.h5`.

## 2. `balance_dataset.py` (Penyeimbangan Dataset Karakter)
- **Fungsi:** Melakukan augmentasi data (rotasi, zoom, pergeseran) pada dataset karakter (`dataset_seimbang/`) untuk memastikan jumlah sampel per-kelas karakter seimbang sebelum pelatihan CNN.

## 3. `pengujian_bab4.py` (GUI Pengambilan Data Uji)
- **Fungsi:** Aplikasi GUI berbasis PyQt6 untuk pengujian performa sistem di lapangan saat penyusunan Bab 4.
- **Fitur:**
  - Menjalankan pipeline lengkap (YOLOv8 + CLAHE + Deskewing PCA + CNN + FSM).
  - Menyimpan 3 kategori gambar pembuktian saat tombol *Capture* ditekan:
    1. Deteksi area plat (YOLO).
    2. Segmentasi karakter individual (OCR).
    3. Fusi deteksi + teks prediksi (YOLO + OCR).

## 4. `dashboard_analisis.py` (Super Dashboard Analisis Computer Vision)
- **Fungsi:** Dashboard visual interaktif untuk menginspeksi setiap tahapan pemrosesan citra tingkat lanjut:
  - CLAHE (Contrast Limited Adaptive Histogram Equalization).
  - Edge cleanser & Safe vertical morphology.
  - Auto-deskewing berbasis PCA (Principal Component Analysis).
  - FSM Anti-Domino dan deteksi kontur pinggang huruf (*waistline detection*) untuk membedakan karakter mirip ('B' vs '8', 'O' vs '0').
