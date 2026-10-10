import os
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

# 0. INISIALISASI & DETEKSI GPU (CUDA)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print("==================================================")
print("🔍 MEMERIKSA KETERSEDIAAN CUDA / GPU...")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        # Mengaktifkan Memory Growth agar GPU tidak crash kehabisan VRAM
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"✅ GPU TERDETEKSI: {len(gpus)} GPU Ditemukan!")
        for gpu in gpus:
            print(f"   -> {gpu.name}")
        print("🚀 TRAINING AKAN MENGGUNAKAN AKSELERASI RTX (CUDA)!")
    except RuntimeError as e:
        print(f"⚠️ Error konfigurasi GPU: {e}")
else:
    print("❌ GPU TIDAK TERDETEKSI. TensorFlow akan berjalan lambat menggunakan CPU.")
print("==================================================\n")


# 1. KONFIGURASI DATASET & HYPERPARAMETER
DIR_DATASET = "dataset_seimbang"
UKURAN_GAMBAR = (28, 28)
BATCH_SIZE = 32
EPOCHS = 100

print(f"🚀 Memuat Dataset dari: {DIR_DATASET}")

# 2. PEMBAGIAN DATA & AUGMENTASI REAL-TIME
# GENERATOR UNTUK TRAINING: Gambar akan diacak (putar, geser, zoom) setiap kali dipanggil
datagen_training = ImageDataGenerator(
    rescale=1./255,
    rotation_range=10,      # Putar acak maksimal 10 derajat
    zoom_range=0.1,         # Perbesar/perkecil acak 10%
    width_shift_range=0.1,  # Geser kiri/kanan acak 10%
    height_shift_range=0.1, # Geser atas/bawah acak 10%
    fill_mode='nearest',
    validation_split=0.2 
)

# GENERATOR UNTUK VALIDASI: Gambar TIDAK BOLEH dimanipulasi agar ujiannya adil dan murni
datagen_validasi = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2 
)

# Catatan: Penggunaan seed=42 SANGAT PENTING di sini agar gambar training 
# dan validasi tidak bocor / tertukar antar generator.
data_training = datagen_training.flow_from_directory(
    DIR_DATASET,
    target_size=UKURAN_GAMBAR,
    color_mode="grayscale", 
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training",
    seed=42
)

data_validasi = datagen_validasi.flow_from_directory(
    DIR_DATASET,
    target_size=UKURAN_GAMBAR,
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation",
    seed=42
)

jumlah_kelas = data_training.num_classes
print(f"Ditemukan {jumlah_kelas} kelas karakter unik.\n")

# 3. ARSITEKTUR MODEL CNN
model = Sequential([
    # Ekstraksi Fitur 1
    Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
    MaxPooling2D(pool_size=(2, 2)),
    
    # Ekstraksi Fitur 2
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(pool_size=(2, 2)),
    
    # Otak Pengambil Keputusan
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5), # Hukuman mematikan 50% neuron agar AI tidak menghafal
    Dense(jumlah_kelas, activation='softmax')
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# 4. CALLBACKS
# Rem darurat: Berhenti jika loss validasi gagal membaik selama 8 epoch
penghenti_dini = EarlyStopping(
    monitor='val_loss',
    patience=8, 
    restore_best_weights=True,
    verbose=1
)

# Menyimpan HANYA model yang berhasil memecahkan rekor nilai terendah
penyimpan_model = ModelCheckpoint(
    'best_ocr_model.h5',
    monitor='val_loss',
    save_best_only=True,
    verbose=1
)

# 5. PROSES PELATIHAN (TRAINING)
print("🔥 MEMULAI PELATIHAN MODEL CNN...")
history = model.fit(
    data_training,
    validation_data=data_validasi,
    epochs=EPOCHS,
    callbacks=[penghenti_dini, penyimpan_model],
    verbose=1
)


# 6. VISUALISASI HASIL PELATIHAN (GRAFIK)
print("\n📊 Membuat Grafik Hasil Evaluasi...")
plt.figure(figsize=(14, 5))

# Grafik Akurasi
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Akurasi Training', color='blue', linewidth=2)
plt.plot(history.history['val_accuracy'], label='Akurasi Validasi', color='orange', linewidth=2)
plt.title('Grafik Akurasi CNN (Augmentasi Real-Time)')
plt.xlabel('Epoch')
plt.ylabel('Akurasi')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

# Grafik Loss
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Loss Training', color='red', linewidth=2)
plt.plot(history.history['val_loss'], label='Loss Validasi', color='green', linewidth=2)
plt.title('Grafik Loss CNN (Augmentasi Real-Time)')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('Grafik_Evaluasi_Final.png')
print("🎉 PELATIHAN SELESAI! Model terbaik telah disimpan secara otomatis sebagai 'best_ocr_model.h5'.")
plt.show()