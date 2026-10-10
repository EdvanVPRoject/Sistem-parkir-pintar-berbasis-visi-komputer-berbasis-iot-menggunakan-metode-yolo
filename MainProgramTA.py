import os
import cv2
import time
import sqlite3
import serial
import warnings
import base64
from datetime import datetime
from collections import Counter
import numpy as np
import tensorflow as tf
from ultralytics import YOLO

import firebase_admin
from firebase_admin import credentials, db

from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QImage

# --- KONFIGURASI GLOBAL ---
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Menyembunyikan peringatan TensorFlow yang tidak penting
DAFTAR_KARAKTER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PATH_MODEL_OCR = "best_ocr_model.h5"

# --- INISIALISASI KONEKSI CLOUD FIREBASE ---
NAMA_FILE_KUNCI = "kunci-firebase.json"
try:
    if not os.path.exists(NAMA_FILE_KUNCI):
        print(f"[PERINGATAN] File '{NAMA_FILE_KUNCI}' tidak ditemukan!")
        
    if not firebase_admin._apps:
        cred = credentials.Certificate(NAMA_FILE_KUNCI)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://taparkir-4d34d-default-rtdb.asia-southeast1.firebasedatabase.app'
        })
    print("[INISIALISASI] Firebase Realtime Database Berhasil Terhubung!")
except Exception as e:
    print(f"\n[ERROR FATAL FIREBASE] Gagal koneksi ke Cloud: {e}")

# ====================================================================
# 1. FUNGSI TEKS, GAMBAR & KOREKSI
# ====================================================================

def frame_ke_base64(img_cv):
    """
    LOGIKA BASE64: Mengubah gambar OpenCV menjadi teks panjang.
    Mengapa? Karena Firebase Realtime DB tidak bisa menyimpan file foto secara langsung. 
    Daripada menyewa Firebase Storage (berbayar), kita kompres foto ini jadi teks dan 
    menyimpannya secara 100% gratis dan proses pengirimannya jauh lebih ringan/cepat.
    """
    try:
        h, w = img_cv.shape[:2]
        max_w = 400
        # Kompres ukuran gambar jika terlalu besar agar teks Base64 tidak membebani memori
        if w > max_w:
            scale = max_w / w
            img_cv = cv2.resize(img_cv, (int(w * scale), int(h * scale)))
        
        _, buffer = cv2.imencode('.jpg', img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        teks_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{teks_base64}"
    except Exception as e:
        return ""

def koreksi_format_indonesia(tebakan_list, boxes, crops):

    h_ke_a = {'O': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6', 'A': '4', 'D': '0', 'T': '7', 'J': '5', 'U': '0', 'Q': '0'}
    a_ke_h = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '6': 'G', '4': 'A', '7': 'T', '3': 'J'}

    hasil = list("".join(tebakan_list))
    n = len(hasil)
    if n < 3: return "".join(hasil) # Plat tidak valid jika kurang dari 3 karakter

    for i in range(n):
        char = hasil[i]
        crop_img = crops[i]
        H, W = crop_img.shape

        # Menganalisis garis batas paling kanan dari gambar huruf
        right_profile = []
        for y in range(H):
            row = crop_img[y, :]
            whites = np.where(row > 0)[0]
            if len(whites) > 0:
                right_profile.append(whites[-1]) # Catat piksel putih terluar
            else:
                right_profile.append(0)

        # Hitung rata-rata posisi batas kanan di area Atas, Tengah, dan Bawah
        if H > 10:
            top_avg = np.mean(right_profile[int(H*0.20) : int(H*0.35)])
            mid_avg = np.mean(right_profile[int(H*0.45) : int(H*0.55)])
            bot_avg = np.mean(right_profile[int(H*0.65) : int(H*0.80)])
        else:
            top_avg, mid_avg, bot_avg = 0, 0, 0

        # Menghitung Cekungan (Pinggang)
        dip_top = top_avg - mid_avg
        dip_bot = bot_avg - mid_avg
        # Jika cekungan lebih dalam dari 6% total lebar, maka itu pasti B atau 8
        is_berpinggang = (dip_top > W * 0.025) and (dip_bot > W * 0.025)

        # Koreksi Karakter Pertama (Pasti Huruf Wilayah)
        if i == 0:
            char = a_ke_h.get(char, char)
            if char in ['0', 'O', 'Q', 'C']: char = 'D'
            hasil[i] = char
            
        # Koreksi Karakter Suffix (Huruf di bagian paling belakang)
        elif i >= n - 2: 
            char = a_ke_h.get(char, char)
            if char in ['B', 'O', 'D', 'Q', 'G', '8', '0']:
                if is_berpinggang:
                    char = 'B' # Berpinggang mutlak B
                else:
                    if char == 'B' or char == '8': 
                        char = 'O' # AI nebak B, tapi bodinya cembung. Paksa jadi O!
            hasil[i] = char
            
        # Koreksi Kasus Spesial 3 Karakter di Belakang
        elif i == n - 3 and not tebakan_list[i].isdigit():
            hasil[i] = a_ke_h.get(char, char)
            
        # Koreksi Karakter Nomor Seri Tengah (Pasti Angka)
        else: 
            if char.isalpha():
                char = h_ke_a.get(char, char)
            if char in ['8', '0', '6', 'B', 'O']:
                if is_berpinggang:
                    char = '8' # Berpinggang mutlak 8
                else:
                    if char == '8' or char == 'B':
                        char = '0' # AI nebak 8, tapi bodinya cembung. Paksa jadi 0!
            hasil[i] = char

    return "".join(hasil)

def segmentasi_karakter(img_plat):
    """
    LOGIKA SEGMENTASI (Pemisahan Karakter):
    Fungsi ini membersihkan gambar dari *noise* dan memecah plat menjadi huruf satuan.
    """
    if len(img_plat.shape) == 3: 
        gray = cv2.cvtColor(img_plat, cv2.COLOR_BGR2GRAY)
    else: 
        gray = img_plat
    
    target_height = 60 
    original_h = gray.shape[0]
    if original_h < target_height:
        scale = target_height / original_h
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif original_h < target_height * 1.5:
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # 1. TEKNOLOGI CLAHE: Meratakan pencahayaan agar plat hitam yang kusam tidak pudar saat diubah ke hitam putih.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)

    blur = cv2.GaussianBlur(gray_clahe, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    if cv2.countNonZero(thresh) > (thresh.shape[0] * thresh.shape[1] / 2):
        thresh = cv2.bitwise_not(thresh)
        jenis = "PUTIH"
    else: 
        jenis = "HITAM"

    # 2. LOGIKA PCA (Auto-Deskewing): Matematika tingkat tinggi untuk meluruskan plat miring.
    # Mencari kumpulan piksel putih (huruf), menarik garis lurus (eigenvectors),
    # lalu merotasi gambar jika kemiringannya antara 3 hingga 40 derajat.
    coords = np.column_stack(np.where(thresh > 0)[::-1])
    if len(coords) > 0:
        _, eigenvectors = cv2.PCACompute(coords.astype(np.float32), mean=None)
        sudut_miring = np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0]) * (180.0 / np.pi)
        
        if sudut_miring > 90: sudut_miring -= 180
        elif sudut_miring < -90: sudut_miring += 180
            
        if 3 < abs(sudut_miring) < 40:
            h_img, w_img = thresh.shape[:2]
            pusat = (w_img // 2, h_img // 2)
            M = cv2.getRotationMatrix2D(pusat, sudut_miring, 1.0)
            thresh = cv2.warpAffine(thresh, M, (w_img, h_img), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            gray = cv2.warpAffine(gray, M, (w_img, h_img), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
    # 3. MORFOLOGI RINGAN: Menyambung huruf yang terputus (Closing) & membersihkan noise kecil (Opening)
    kernel_close = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
    
    kernel_open = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open, iterations=1)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes_sementara = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 1.2 < (h/w) < 5.0 and (w*h) > 150 and h > (gray.shape[0] * 0.35):
            boxes_sementara.append((x, y, w, h))
            
    # 4. Y-AXIS ALIGNMENT: Membuang noise (seperti baut/logo Korlantas) yang tingginya tidak sejajar dengan huruf utama.
    boxes = []
    if len(boxes_sementara) > 0:
        centers_y = [y + (h // 2) for (x, y, w, h) in boxes_sementara]
        median_y = np.median(centers_y)
        toleransi_y = gray.shape[0] * 0.15
        
        for (x, y, w, h) in boxes_sementara:
            center_y = y + (h // 2)
            if abs(center_y - median_y) <= toleransi_y:
                boxes.append((x, y, w, h))
                
    boxes = sorted(boxes, key=lambda b: b[0])
    crops = []
    for (x, y, w, h) in boxes:
        c = thresh[max(0,y):min(thresh.shape[0],y+h), max(0,x):min(thresh.shape[1],x+w)]
        crops.append(c)
        
    return thresh, boxes, crops, jenis

# 2. THREAD MESIN UTAMA
class MesinParkirThread(QThread):
    """
    LOGIKA THREADING (QThread):
    Fungsi ini berjalan di jalur pemrosesan terpisah dari GUI. Tujuannya agar saat 
    kamera memproses AI atau internet Firebase sedang lambat, tampilan layar (tombol, video)
    TIDAK ikut macet (Not Responding).
    """
    # Sinyal untuk berkomunikasi (mengirim data) dari Backend ke Frontend GUI
    sinyal_kamera_utama = pyqtSignal(QImage)
    sinyal_log = pyqtSignal(str)
    sinyal_refresh_db = pyqtSignal() 
    sinyal_status_utama = pyqtSignal(str, str) 

    def run(self):
        # Membuka koneksi database lokal untuk arsitektur Offline-First
        conn = sqlite3.connect('data_parkir_unikom.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS parkir_aktif (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, rfid_uid TEXT, plat_nomor TEXT, waktu_masuk DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS riwayat_parkir (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, rfid_uid TEXT, plat_nomor TEXT, 
                            waktu_masuk DATETIME, waktu_keluar DATETIME, keterangan TEXT)''')
        conn.commit()

        self.sinyal_log.emit("[SISTEM] Memuat Model YOLOv8 (Lokalisasi Plat)...")
        yolo = YOLO("best.pt")
        
        self.sinyal_log.emit(f"[SISTEM] Memuat AI Karakter (CNN) dari: {PATH_MODEL_OCR}...")
        try:
            cnn_model = tf.keras.models.load_model(PATH_MODEL_OCR, compile=False)
            self.sinyal_log.emit("[SISTEM] Model CNN (.h5) Berhasil Dimuat!")
        except Exception as e:
            self.sinyal_log.emit(f"[ERROR] GAGAL MEMUAT MODEL OCR .h5: {e}")
            return 

        def resize_tanpa_distorsi(img_crop, target_size=28, padding=4):
            """
            LOGIKA CNN PADDING: Model AI benci gambar yang menempel batas tepi. 
            Mengecilkan potongan huruf menjadi 20x20 lalu memberinya bingkai hitam (padding) 
            4 piksel di sekelilingnya menjadi 28x28 agar ujung lengkungan angka tidak terpotong.
            """
            h, w = img_crop.shape[:2]
            ukuran_ruang = target_size - (padding * 2)
            skala = ukuran_ruang / max(h, w)
            baris_baru = int(h * skala)
            kolom_baru = int(w * skala)
            interp = cv2.INTER_AREA if skala < 1.0 else cv2.INTER_CUBIC
            img_proporsional = cv2.resize(img_crop, (kolom_baru, baris_baru), interpolation=interp)
            kanvas = np.zeros((target_size, target_size), dtype=np.uint8)
            pos_y = (target_size - baris_baru) // 2
            pos_x = (target_size - kolom_baru) // 2
            kanvas[pos_y : pos_y + baris_baru, pos_x : pos_x + kolom_baru] = img_proporsional
            return kanvas

        def tebak_cnn(img):
            # Normalisasi gambar sebelum disuapkan ke Otak AI (CNN)
            try:
                img_28 = resize_tanpa_distorsi(img, 28)
                if len(img_28.shape) == 3:
                    img_gray = cv2.cvtColor(img_28, cv2.COLOR_BGR2GRAY)
                else:
                    img_gray = img_28
                
                img_input = img_gray.astype(np.float32)
                img_input = np.expand_dims(img_input, axis=0)
                img_input = np.expand_dims(img_input, axis=-1)
                
                res = cnn_model.predict(img_input, verbose=0)
                return DAFTAR_KARAKTER[np.argmax(res[0])]
            except Exception as e: 
                return "?"

        # Inisialisasi Modul ESP32 RFID via Serial USB
        self.simulasi_rfid_uid = ""
        ser = None
        for port in ['COM5', 'COM8', 'COM3', 'COM4']:
            try:
                ser = serial.Serial(port, 115200, timeout=0.1) 
                self.sinyal_log.emit(f"[SISTEM] ESP32 RFID Terhubung di {port}")
                break
            except Exception:
                continue
        if not ser:
            self.sinyal_log.emit("[PERINGATAN] Modul RFID Hardware tidak terdeteksi. Gunakan tombol Simulasi.")

        # Inisialisasi Kamera 1080p
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 30)

        self.sinyal_log.emit("\n>> KAMERA REAL-TIME FULL HD 1080p AKTIF.\n")
        self.sinyal_status_utama.emit("SILAHKAN TAP KARTU ANDA!", "#a6e3a1")

        waktu_reset_status = time.time() - 10 
        buffer_plat_voting = []
        waktu_terakhir_deteksi = time.time()
        frame_for_saving = None

        # --- LOOP UTAMA
        while True:
            ret, frame = cap.read()
            if not ret: break

            if time.time() - waktu_reset_status > 5.0:
                self.sinyal_status_utama.emit("SILAHKAN TAP KARTU ANDA!", "#a6e3a1")
                waktu_reset_status = time.time() + 999999 

            frame_display = frame.copy()
            results = yolo(frame, conf=0.5, verbose=False)
            best_box = None
            max_area = 0
            
            # Mencari plat nomor dengan ukuran area terluas (paling dekat dengan kamera)
            for res in results:
                for box in res.boxes:
                    b = box.xyxy[0].cpu().numpy().astype(int)
                    area = (b[2] - b[0]) * (b[3] - b[1])
                    if area > max_area:
                        max_area = area
                        best_box = b
                        
            if best_box is not None:
                b = best_box
                plat = frame[b[1]:b[3], b[0]:b[2]]
                
                if plat.size > 0:
                    h_plat, w_plat = plat.shape[:2]
                    if w_plat >= 80 and h_plat >= 25:
                        # Buang teks bulan.tahun di bagian bawah plat
                        plat_crop = plat[0:int(h_plat*0.60), :]
                        
                        # LOGIKA MARGIN CROP: Membuang 3% sisi kiri dan 1.5% sisi kanan agar 
                        # garis border putih plat tidak terbaca 'I'.
                        margin_kiri = int(w_plat * 0.03) 
                        margin_kanan = int(w_plat * 0.015) 
                        plat_crop = plat_crop[:, margin_kiri : w_plat - margin_kanan]

                        thr, bxs, crps, jns = segmentasi_karakter(plat_crop)
                        mentah = [tebak_cnn(c) for c in crps]
                        temp_format = koreksi_format_indonesia(mentah, bxs, crps)
                        
                        if temp_format and len(temp_format) >= 3:
                            waktu_terakhir_deteksi = time.time()
                            frame_for_saving = frame.copy()
                            buffer_plat_voting.append(temp_format)
                            

                            if len(buffer_plat_voting) > 5: 
                                buffer_plat_voting.pop(0)
                            teks_stabil = Counter(buffer_plat_voting).most_common(1)[0][0]
                            
                            cv2.rectangle(frame_display, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 3)
                            cv2.putText(frame_display, teks_stabil, (b[0], b[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            if time.time() - waktu_terakhir_deteksi > 3.0:
                buffer_plat_voting.clear() # Kosongkan memori jika tidak ada plat > 3 detik

            # Kirim gambar ke GUI (Frontend)
            rgb_image = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            frame_qt = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).scaled(960, 540, Qt.AspectRatioMode.KeepAspectRatio)
            self.sinyal_kamera_utama.emit(frame_qt)

            # Membaca Tap RFID masuk
            rfid_trigger = False
            last_rfid = ""
            if ser and ser.in_waiting > 0:
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("RFID:"):
                        last_rfid = line.split(":")[1].strip()
                        rfid_trigger = True

            if self.simulasi_rfid_uid != "":
                last_rfid = self.simulasi_rfid_uid
                rfid_trigger = True
                self.simulasi_rfid_uid = ""

            # JIKA ADA MOBIL TAP KARTU
            if rfid_trigger:
                self.sinyal_log.emit(f"\n[!] TAP KARTU RFID TERDETEKSI: {last_rfid}")
                self.sinyal_status_utama.emit("🔍 MEMVALIDASI PLAT NOMOR...", "#89b4fa")
                
                # Paksa sistem mencari plat minimal 5 kali jepretan akurat saat tap
                if len(buffer_plat_voting) < 5:
                    for _ in range(10):
                        ret_ext, frame_ext = cap.read()
                        if not ret_ext: continue
                        res_ext = yolo(frame_ext, conf=0.5, verbose=False)
                        for r_ext in res_ext:
                            for b_ext in r_ext.boxes:
                                box_coord = b_ext.xyxy[0].cpu().numpy().astype(int)
                                p_img = frame_ext[box_coord[1]:box_coord[3], box_coord[0]:box_coord[2]]
                                if p_img.shape[1] >= 80 and p_img.shape[0] >= 25:
                                    p_img_crop = p_img[0:int(p_img.shape[0]*0.60), :]
                                    m_kiri = int(p_img.shape[1] * 0.03)
                                    m_kanan = int(p_img.shape[1] * 0.015)
                                    p_img_crop = p_img_crop[:, m_kiri : p_img.shape[1] - m_kanan]
                                    
                                    _, bxs_ext, crps_ext, _ = segmentasi_karakter(p_img_crop)
                                    txt_ext = koreksi_format_indonesia([tebak_cnn(c) for c in crps_ext], bxs_ext, crps_ext)
                                    
                                    if len(txt_ext) >= 3:
                                        buffer_plat_voting.append(txt_ext)
                                        frame_for_saving = frame_ext.copy()
                                        if len(buffer_plat_voting) > 5: buffer_plat_voting.pop(0)
                        if len(buffer_plat_voting) >= 5: break
                
                # Proses Validasi Data ke SQLite & Sinkronisasi
                if len(buffer_plat_voting) > 0 and frame_for_saving is not None:
                    hasil_terbanyak = Counter(buffer_plat_voting).most_common(1)[0]
                    formatted_plate = hasil_terbanyak[0] 
                    
                    self.sinyal_log.emit(f"=== HASIL VOTING: {formatted_plate} ===")
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute("SELECT id, plat_nomor, waktu_masuk FROM parkir_aktif WHERE rfid_uid = ?", (last_rfid,))
                    aktif_rfid = cursor.fetchone()
                    cursor.execute("SELECT rfid_uid FROM parkir_aktif WHERE plat_nomor = ?", (formatted_plate,))
                    aktif_plat = cursor.fetchone()

                    os.makedirs("hasil_capture", exist_ok=True)
                    nama_file_foto = f"Log_{formatted_plate}_{int(time.time())}.jpg"
                    cv2.imwrite(f"hasil_capture/{nama_file_foto}", frame_for_saving)
                    url_foto_cloud = frame_ke_base64(frame_for_saving)

                    # KENDARAAN MASUK
                    if aktif_rfid is None: 
                        # Ditolak jika plat sudah terdeteksi di dalam area (Anti Tapping Palsu)
                        if aktif_plat is not None: 
                            self.sinyal_status_utama.emit(f"⛔ AKSES DITOLAK!\nPLAT {formatted_plate} SUDAH DI DALAM", "#f38ba8")
                            try: db.reference('log_keamanan').push({'rfid_uid': last_rfid, 'plat_nomor': formatted_plate, 'waktu': ts, 'keterangan': "Akses Ditolak (Plat Sudah Ada)", 'status': 'DITOLAK', 'foto_url': url_foto_cloud})
                            except Exception: pass
                        else:
                            # Akses Diterima (Disimpan di SQLite lokal lalu dikirim ke Cloud)
                            cursor.execute("INSERT INTO parkir_aktif (rfid_uid, plat_nomor, waktu_masuk) VALUES (?,?,?)", (last_rfid, formatted_plate, ts))
                            cursor.execute("INSERT INTO riwayat_parkir (rfid_uid, plat_nomor, waktu_masuk, keterangan) VALUES (?,?,?,?)", (last_rfid, formatted_plate, ts, "MASUK"))
                            conn.commit()
                            self.sinyal_status_utama.emit(f"✅ AKSES DITERIMA - MASUK\nPLAT: {formatted_plate}", "#a6e3a1")
                            self.sinyal_refresh_db.emit()
                            try:
                                db.reference('parkir_aktif').child(last_rfid).set({'rfid_uid': last_rfid, 'plat_nomor': formatted_plate, 'waktu_masuk': ts, 'foto_url': url_foto_cloud})
                                db.reference('riwayat_parkir').push({'rfid_uid': last_rfid, 'plat_nomor': formatted_plate, 'waktu_masuk': ts, 'waktu_keluar': '-', 'status': 'MASUK', 'foto_url': url_foto_cloud})
                            except Exception: pass
                    
                    # KENDARAAN KELUAR
                    else: 
                        #P lat saat masuk wajib 100% cocok dengan plat saat keluar
                        if aktif_rfid[1] == formatted_plate:
                            cursor.execute("DELETE FROM parkir_aktif WHERE id = ?", (aktif_rfid[0],))
                            cursor.execute("UPDATE riwayat_parkir SET waktu_keluar = ?, keterangan = 'SELESAI' WHERE rfid_uid = ? AND waktu_keluar IS NULL", (ts, last_rfid))
                            conn.commit()
                            self.sinyal_status_utama.emit(f"✅ AKSES DITERIMA - KELUAR\nPLAT: {formatted_plate}", "#89b4fa")
                            self.sinyal_refresh_db.emit()
                            try:
                                db.reference('parkir_aktif').child(last_rfid).delete()
                                db.reference('riwayat_parkir').push({'rfid_uid': last_rfid, 'plat_nomor': formatted_plate, 'waktu_masuk': aktif_rfid[2], 'waktu_keluar': ts, 'status': 'SELESAI', 'foto_url': url_foto_cloud})
                            except Exception: pass
                        else:
                            # Akses ditolak karena yang keluar beda motor dengan yang masuk
                            self.sinyal_status_utama.emit("⛔ AKSES DITOLAK!\nPLAT BERBEDA DENGAN SAAT MASUK", "#f38ba8")
                            try: db.reference('log_keamanan').push({'rfid_uid': last_rfid, 'plat_nomor': formatted_plate, 'waktu': ts, 'keterangan': f"Akses Ditolak (Beda Plat - Masuk: {aktif_rfid[1]})", 'status': 'DITOLAK', 'foto_url': url_foto_cloud})
                            except Exception: pass
                    buffer_plat_voting.clear()
                else:
                    self.sinyal_status_utama.emit("⚠️ GAGAL!\nPLAT TIDAK TERBACA/DITEMUKAN", "#fab387")
                    
                waktu_reset_status = time.time()

        if ser: ser.close()
        cap.release()
        conn.close()