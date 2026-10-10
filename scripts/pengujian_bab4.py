"""
FILE: pengujian_bab4.py
DESKRIPSI: GUI Khusus Pengambilan Data Bab 4 Skripsi
TUGAS: Menjalankan YOLOv8, CNN, Segmentasi, FSM, dan menyimpan 3 jenis 
       gambar pengujian (YOLO, OCR, YOLO+OCR) saat tombol Capture ditekan.
"""

import os
import cv2
import time
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
from datetime import datetime
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QImage, QFont

# --- KONFIGURASI GLOBAL ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
DAFTAR_KARAKTER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PATH_MODEL_OCR = "best_ocr_model.h5"

# ====================================================================
# 1. LOGIKA KECERDASAN BUATAN & PEMROSESAN CITRA
# ====================================================================

def segmentasi_karakter(img_plat):
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

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)

    blur = cv2.GaussianBlur(gray_clahe, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    if cv2.countNonZero(thresh) > (thresh.shape[0] * thresh.shape[1] / 2):
        thresh = cv2.bitwise_not(thresh)
        jenis = "PUTIH"
    else: 
        jenis = "HITAM"

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
        
    kernel_close = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
    
    kernel_open = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open, iterations=1)

    # [BARU] BORDER DETACHER: Menggambar garis hitam di sekeliling gambar 
    # agar batas plat tidak menempel dan merusak karakter asli.
    cv2.rectangle(thresh, (0, 0), (thresh.shape[1]-1, thresh.shape[0]-1), (0, 0, 0), 2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes_sementara = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # [REVISI] Rasio diperlebar (0.5 s/d 8.0) agar angka tipis seperti '1' atau 'I' tidak terbuang.
        # Luas area diturunkan ke 150 agar sisa huruf mepet tidak terbuang paksa.
        if 0.5 < (h/w) < 8.0 and (w*h) > 150 and h > (gray.shape[0] * 0.30):
            boxes_sementara.append((x, y, w, h))
            
    boxes = []
    if len(boxes_sementara) > 0:
        centers_y = [y + (h // 2) for (x, y, w, h) in boxes_sementara]
        median_y = np.median(centers_y)
        toleransi_y = gray.shape[0] * 0.35
        
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


def segmentasi_karakter(img_plat):
    """ Dilengkapi Border Detacher dan Relaksasi Margin """
    if len(img_plat.shape) == 3: gray = cv2.cvtColor(img_plat, cv2.COLOR_BGR2GRAY)
    else: gray = img_plat
    
    target_height = 60 
    original_h = gray.shape[0]
    if original_h < target_height:
        scale = target_height / original_h
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif original_h < target_height * 1.5:
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    blur = cv2.GaussianBlur(gray_clahe, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    if cv2.countNonZero(thresh) > (thresh.shape[0] * thresh.shape[1] / 2):
        thresh = cv2.bitwise_not(thresh)

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
        
    kernel_close = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
    kernel_open = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open, iterations=1)

    # BORDER DETACHER
    cv2.rectangle(thresh, (0, 0), (thresh.shape[1]-1, thresh.shape[0]-1), (0, 0, 0), 2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes_sementara = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 0.5 < (h/w) < 8.0 and (w*h) > 150 and h > (gray.shape[0] * 0.30):
            boxes_sementara.append((x, y, w, h))
            
    boxes = []
    if len(boxes_sementara) > 0:
        centers_y = [y + (h // 2) for (x, y, w, h) in boxes_sementara]
        median_y = np.median(centers_y)
        toleransi_y = gray.shape[0] * 0.35
        for (x, y, w, h) in boxes_sementara:
            center_y = y + (h // 2)
            if abs(center_y - median_y) <= toleransi_y:
                boxes.append((x, y, w, h))
                
    boxes = sorted(boxes, key=lambda b: b[0])
    crops = []
    for (x, y, w, h) in boxes:
        c = thresh[max(0,y):min(thresh.shape[0],y+h), max(0,x):min(thresh.shape[1],x+w)]
        crops.append(c)
        
    return thresh, boxes, crops

# ====================================================================
# 2. THREAD KAMERA PENGUJIAN
# ====================================================================
class PengujianThread(QThread):
    sinyal_frame = pyqtSignal(QImage)
    sinyal_log = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.trigger_capture = False
        self.berjalan = True

    def minta_capture(self):
        self.trigger_capture = True

    def run(self):
        self.sinyal_log.emit("[INFO] Memuat Model YOLOv8...")
        yolo = YOLO("best.pt")
        
        self.sinyal_log.emit(f"[INFO] Memuat Model CNN OCR...")
        try:
            cnn_model = tf.keras.models.load_model(PATH_MODEL_OCR, compile=False)
            self.sinyal_log.emit("[INFO] Semua Model Siap!")
        except Exception as e:
            self.sinyal_log.emit(f"[ERROR] Gagal muat OCR: {e}")
            return 

        def resize_tanpa_distorsi(img_crop, target_size=28, padding=4):
            h, w = img_crop.shape[:2]
            skala = (target_size - (padding * 2)) / max(h, w)
            img_proporsional = cv2.resize(img_crop, (int(w * skala), int(h * skala)), interpolation=cv2.INTER_CUBIC)
            kanvas = np.zeros((target_size, target_size), dtype=np.uint8)
            pos_y = (target_size - img_proporsional.shape[0]) // 2
            pos_x = (target_size - img_proporsional.shape[1]) // 2
            kanvas[pos_y : pos_y + img_proporsional.shape[0], pos_x : pos_x + img_proporsional.shape[1]] = img_proporsional
            return kanvas

        def tebak_cnn(img):
            img_gray = cv2.cvtColor(resize_tanpa_distorsi(img, 28), cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else resize_tanpa_distorsi(img, 28)
            img_input = np.expand_dims(np.expand_dims(img_gray.astype(np.float32), axis=0), axis=-1)
            res = cnn_model.predict(img_input, verbose=0)
            return DAFTAR_KARAKTER[np.argmax(res[0])]

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        os.makedirs("Dataset_Bab4", exist_ok=True)

        while self.berjalan:
            ret, frame = cap.read()
            if not ret: continue

            frame_raw = frame.copy()
            frame_disp = frame.copy()
            
            results = yolo(frame, conf=0.5, verbose=False)
            best_box, max_area = None, 0
            
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
                
                h_plat, w_plat = plat.shape[:2]
                if w_plat >= 80 and h_plat >= 25:
                    plat_crop = plat[0:int(h_plat*0.60), :]
                    plat_crop = plat_crop[:, int(w_plat * 0.015) : w_plat - int(w_plat * 0.015)]

                    thr, bxs, crps = segmentasi_karakter(plat_crop)
                    mentah = [tebak_cnn(c) for c in crps]
                    teks_hasil = koreksi_format_indonesia(mentah, crps)
                    
                    # Menggambar untuk tampilan GUI
                    cv2.rectangle(frame_disp, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 3)
                    cv2.putText(frame_disp, teks_hasil, (b[0], b[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

                    # PROSES PENYIMPANAN 3 FILE
                    if self.trigger_capture:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path_folder = "Dataset_Bab4"
                        
                        # 1. FILE YOLO (Hanya Box)
                        img_yolo = frame_raw.copy()
                        cv2.rectangle(img_yolo, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 3)
                        cv2.imwrite(f"{path_folder}/{timestamp}_1_YOLO.jpg", img_yolo)

                        # 2. FILE OCR (Crop Plat + Segmentasi Merah + Teks Hasil)
                        img_ocr = plat_crop.copy()
                        for (x, y, w, h) in bxs:
                            cv2.rectangle(img_ocr, (x, y), (x+w, y+h), (0, 0, 255), 1)
                        # Diperbesar 3x agar bagus saat diprint di buku skripsi
                        img_ocr_besar = cv2.resize(img_ocr, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
                        cv2.putText(img_ocr_besar, teks_hasil, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                        cv2.imwrite(f"{path_folder}/{timestamp}_2_OCR.jpg", img_ocr_besar)

                        # 3. FILE YOLO + OCR (Box + Teks)
                        img_yolo_ocr = img_yolo.copy()
                        cv2.putText(img_yolo_ocr, teks_hasil, (b[0], b[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                        cv2.imwrite(f"{path_folder}/{timestamp}_3_YOLO_OCR.jpg", img_yolo_ocr)

                        self.sinyal_log.emit(f"✅ BUKTI TERSIMPAN: {teks_hasil} (3 File di Folder Dataset_Bab4)")
                        self.trigger_capture = False

            else:
                if self.trigger_capture:
                    self.sinyal_log.emit("⚠️ GAGAL CAPTURE: Tidak ada pelat yang terdeteksi di kamera!")
                    self.trigger_capture = False

            # Kirim gambar ke GUI
            rgb_img = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format.Format_RGB888).scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
            self.sinyal_frame.emit(qt_img)

        cap.release()

# ====================================================================
# 3. ANTARMUKA PENGGUNA (GUI) KHUSUS PENGUJIAN
# ====================================================================
class PengujianGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tools Pengujian Bab 4 - YOLO & OCR")
        self.resize(850, 750)

        widget_utama = QWidget()
        self.setCentralWidget(widget_utama)
        layout = QVBoxLayout(widget_utama)

        judul = QLabel("🛠️ DASHBOARD PENGAMBILAN DATA BAB 4")
        judul.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        judul.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(judul)

        self.label_video = QLabel("Memuat Kamera...")
        self.label_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_video.setMinimumSize(800, 480)
        self.label_video.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.label_video)

        self.btn_capture = QPushButton("📸 CAPTURE DATA PENGUJIAN")
        self.btn_capture.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_capture.setStyleSheet("background-color: #28a745; color: white; padding: 15px; border-radius: 5px;")
        self.btn_capture.clicked.connect(self.klik_capture)
        layout.addWidget(self.btn_capture)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: #1e1e2e; color: #a6e3a1; font-family: Consolas; font-size: 14px;")
        self.log_box.setMaximumHeight(150)
        layout.addWidget(self.log_box)

        # Menjalankan Thread
        self.thread_kamera = PengujianThread()
        self.thread_kamera.sinyal_frame.connect(self.update_video)
        self.thread_kamera.sinyal_log.connect(self.update_log)
        self.thread_kamera.start()

    def klik_capture(self):
        self.update_log("Merekam bukti pengujian...")
        self.thread_kamera.minta_capture()

    def update_video(self, frame_qt):
        self.label_video.setPixmap(from_qimage(frame_qt))

    def update_log(self, pesan):
        self.log_box.append(pesan)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.thread_kamera.berjalan = False
        self.thread_kamera.wait()
        event.accept()

# Helper PyQt6
def from_qimage(img):
    from PyQt6.QtGui import QPixmap
    return QPixmap.fromImage(img)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PengujianGUI()
    window.show()
    sys.exit(app.exec())