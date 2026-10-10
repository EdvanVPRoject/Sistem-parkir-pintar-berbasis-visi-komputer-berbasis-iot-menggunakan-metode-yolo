import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
import matplotlib.pyplot as plt

# =================================================================
# ---> KONFIGURASI AKSELERASI GPU & PROTEKSI MEMORI VRAM <---
# =================================================================
print("[INFO] Memeriksa ketersediaan Hardware GPU...")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        # Mencegah TensorFlow memonopoli 100% VRAM sejak awal (Memory Growth)
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"[SUKSES GPU] Akselerasi aktif! Menggunakan {len(gpus)} GPU terdeteksi:")
        for i, gpu in enumerate(gpus):
            print(f"  -> GPU [{i}]: {gpu.name}")
        # Memaksa TensorFlow memprioritaskan pemrosesan pada GPU pertama
        tf.config.set_visible_devices(gpus[0], 'GPU')
    except RuntimeError as e:
        print(f"[ERROR GPU] Konfigurasi memori gagal: {e}")
else:
    print("[PERINGATAN] GPU tidak terdeteksi oleh TensorFlow! Latihan akan beralih ke CPU (Lebih lambat).")
    print("-> Pastikan NVIDIA Driver, CUDA Toolkit, dan cuDNN sudah terpasang sesuai versi TensorFlow Anda.")
# =================================================================

# --- KONFIGURASI MAKSIMAL ---
FOLDER_DATASET = "dataset_plat"
BATCH_SIZE = 64
EPOCHS = 100  # Pasang tinggi (100 putaran), EarlyStopping yang akan mengontrolnya otomatis!
IMG_SIZE = (28, 28)

if not os.path.exists(FOLDER_DATASET):
    raise FileNotFoundError(f"Folder '{FOLDER_DATASET}' tidak ditemukan! Jalankan generate_dataset.py terlebih dahulu.")

print("\n[INFO] Memuat dataset gambar dari folder...")

# Memuat dataset (Grayscale 28x28)
dataset = tf.keras.utils.image_dataset_from_directory(
    FOLDER_DATASET,
    color_mode="grayscale",
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    validation_split=0.2,    # 80% Latih (Training), 20% Uji (Validation)
    seed=42,
    subset="both"
)

train_ds, val_ds = dataset
class_names = train_ds.class_names
print(f"[INFO] Terdeteksi {len(class_names)} kelas karakter: {class_names}")

# Optimasi pipeline I/O memori agar GPU tidak pernah kehabisan suplai data
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# =================================================================
# ARSITEKTUR CNN ULTIMATE (Dilengkapi Batch Normalization & Dropout)
# =================================================================
# Kita bungkus arsitektur di dalam konteks device GPU agar proses komputasi tensor terjamin di GPU
with tf.device('/GPU:0' if gpus else '/CPU:0'):
    model = models.Sequential([
        # Normalisasi piksel ke [0.0, 1.0]
        layers.Rescaling(1./255, input_shape=(28, 28, 1)),
        
        # Blok Konvolusi 1
        layers.Conv2D(32, (3, 3), padding='same', use_bias=False),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        
        # Blok Konvolusi 2
        layers.Conv2D(64, (3, 3), padding='same', use_bias=False),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        
        # Blok Konvolusi 3
        layers.Conv2D(128, (3, 3), padding='same', use_bias=False),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),  # Mencegah ketergantungan fitur spasial
        
        # Flatten & Dense Layer (Klasifikasi Puncak)
        layers.Flatten(),
        layers.Dense(256, use_bias=False),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.Dropout(0.4),  # Mencegah overfitting secara agresif
        
        # Output Layer (36 Kelas: A-Z, 0-9)
        layers.Dense(len(class_names), activation='softmax')
    ])

    # Kompilasi Model dengan Optimizer Adam
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

model.summary()

# =================================================================
# CALLBACKS PINTAR (THE HOLY TRINITY OF AI TRAINING)
# =================================================================
NAMA_MODEL_BARU = "best_ocr_model.h5"

callback_list = [
    # 1. Simpan hanya versi dengan akurasi validasi (val_accuracy) TERTINGGI
    callbacks.ModelCheckpoint(
        filepath=NAMA_MODEL_BARU,
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    ),
    
    # 2. Rem Otomatis: Turunkan learning rate menjadi setengah jika 3 epoch tidak ada kemajuan
    callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        verbose=1
    ),
    
    # 3. Stop Otomatis: Hentikan latihan jika 10 epoch stagnan, lalu kembalikan bobot terbaik!
    callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )
]

# --- PROSES TRAINING ---
print("\n[INFO] Memulai proses pelatihan AI Ultimate dengan akselerasi hardware...")
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callback_list
)

print(f"\n[SUKSES LUAR BIASA] Pelatihan selesai! Model terbaik telah diamankan di: '{NAMA_MODEL_BARU}'")

# =================================================================
# ---> GENERATOR GRAFIK PELATIHAN RESOLUSI TINGGI (300 DPI) <---
# =================================================================
print("[INFO] Menggambar grafik rekam jejak pelatihan...")

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']

# Menyesuaikan rentang epoch secara dinamis
durasi_epoch = len(acc)
rentang_epoch = range(1, durasi_epoch + 1)

plt.figure(figsize=(14, 6), dpi=300)

# 1. GRAFIK AKURASI
plt.subplot(1, 2, 1)
plt.plot(rentang_epoch, acc, 'b-o', label='Training Accuracy (Akurasi Latih)', linewidth=2, markersize=4)
plt.plot(rentang_epoch, val_acc, 'g-s', label='Validation Accuracy (Akurasi Uji)', linewidth=2, markersize=4)
plt.title('Grafik Akurasi Pelatihan vs Pengujian', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Epoch (Putaran Pelatihan)', fontsize=12)
plt.ylabel('Tingkat Akurasi (0.0 - 1.0)', fontsize=12)
plt.xticks(rentang_epoch if durasi_epoch <= 15 else np.linspace(1, durasi_epoch, 10, dtype=int))
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc='lower right', fontsize=11)
plt.ylim([max(0.6, min(min(acc), min(val_acc)) - 0.05), 1.01])

# 2. GRAFIK LOSS (KESALAHAN)
plt.subplot(1, 2, 2)
plt.plot(rentang_epoch, loss, 'r-o', label='Training Loss (Kerugian Latih)', linewidth=2, markersize=4)
plt.plot(rentang_epoch, val_loss, 'm-s', label='Validation Loss (Kerugian Uji)', linewidth=2, markersize=4)
plt.title('Grafik Loss (Tingkat Kesalahan) Pelatihan vs Pengujian', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Epoch (Putaran Pelatihan)', fontsize=12)
plt.ylabel('Nilai Loss', fontsize=12)
plt.xticks(rentang_epoch if durasi_epoch <= 15 else np.linspace(1, durasi_epoch, 10, dtype=int))
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc='upper right', fontsize=11)

plt.tight_layout()

# Simpan ke hardisk untuk lampiran Skripsi
NAMA_FILE_GRAFIK = "grafik_pelatihan_ocr.png"
plt.savefig(NAMA_FILE_GRAFIK)
print(f"[SUKSES] Grafik siap cetak telah disimpan sebagai: '{NAMA_FILE_GRAFIK}'")

# Tampilkan di layar sekarang
plt.show()