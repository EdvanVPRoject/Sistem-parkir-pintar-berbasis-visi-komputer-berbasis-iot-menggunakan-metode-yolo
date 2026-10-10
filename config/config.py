"""
Konfigurasi Terpusat untuk Sistem Parkir Pintar
==============================================
Gunakan file ini untuk menyesuaikan pengaturan kamera, serial hardware,
database, dan path model tanpa perlu mengubah kode inti.
"""

import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# --- MODEL AI ---
YOLO_MODEL_PATH = str(BASE_DIR / "best.pt")
OCR_MODEL_PATH = str(BASE_DIR / "best_ocr_model.h5")
CHAR_LIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# --- KAMERA ---
CAMERA_INDEX = 0
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30

# --- SERIAL ARDUINO / ESP32 ---
SERIAL_PORTS = ['COM5', 'COM8', 'COM3', 'COM4']
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 0.1

# --- DATABASE & STORAGE ---
SQLITE_DB_PATH = str(BASE_DIR / "data_parkir_unikom.db")
CAPTURE_DIR = str(BASE_DIR / "hasil_capture")
FIREBASE_KEY_PATH = str(BASE_DIR / "kunci-firebase.json")
FIREBASE_DB_URL = "https://taparkir-4d34d-default-rtdb.asia-southeast1.firebasedatabase.app"

# Pastikan folder penyimpanan foto capture tersedia
os.makedirs(CAPTURE_DIR, exist_ok=True)
