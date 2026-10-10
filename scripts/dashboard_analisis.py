"""
FILE: dashboard_analisis_bab4.py
DESKRIPSI: Super Dashboard Analisis Computer Vision untuk Bab 4 Skripsi.
ALGORITMA: CLAHE + Edge Cleanser + Safe Vertical Morphology + Margin 3%
"""

import os
import cv2
import time
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
from datetime import datetime
import sys

from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QGroupBox)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QImage, QFont, QPixmap

# --- KONFIGURASI GLOBAL ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
DAFTAR_KARAKTER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PATH_MODEL_OCR = "best_ocr_model.h5"

# ====================================================================
# 1. LOGIKA KECERDASAN BUATAN & PEMROSESAN CITRA
# ====================================================================

def koreksi_format_indonesia(tebakan_list, crops):
    """ FSM Anti-Domino + Seluruh Sensor Cerdas """
    a_ke_h = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '6': 'G', '4': 'A', '7': 'T', '3': 'J'}
    n = len(tebakan_list)
    if n < 3: return "".join(tebakan_list)

    zones = []
    state = 0 
    num_count = 0

    for i, char in enumerate(tebakan_list):
        if state == 0:
            if (i > 0 and char.isdigit()) or i >= 2 or (i == 1 and char in ['J', 'Z']):
                state = 1
                zones.append('NUMBER')
                num_count = 1 if (char.isdigit() or char in ['J', 'Z']) else 0
            else:
                zones.append('LETTER')
        elif state == 1:
            if (char.isalpha() and char not in ['O', 'I', 'Z', 'S', 'B', 'G', 'D', 'Q', 'J', 'U', 'V']) or (num_count >= 4):
                state = 2
                zones.append('LETTER')
            else:
                zones.append('NUMBER')
                num_count += 1
        elif state == 2:
            zones.append('LETTER')

    zones[0] = 'LETTER'
    zones[-1] = 'LETTER'

    hasil = []
    for i in range(n):
        char = tebakan_list[i]
        zone = zones[i]
        crop_img = crops[i]
        H, W = crop_img.shape

        right_profile = [np.where(crop_img[y, :] > 0)[0][-1] if len(np.where(crop_img[y, :] > 0)[0]) > 0 else 0 for y in range(H)]
        left_profile = [np.where(crop_img[y, :] > 0)[0][0] if len(np.where(crop_img[y, :] > 0)[0]) > 0 else W for y in range(H)]
        
        if H > 10:
            top_r = np.mean(right_profile[int(H*0.15) : int(H*0.35)])
            mid_r = np.mean(right_profile[int(H*0.45) : int(H*0.55)])
            bot_r = np.mean(right_profile[int(H*0.65) : int(H*0.85)])
            top_l = np.mean(left_profile[0 : int(H*0.15)])
            mid_l = np.mean(left_profile[int(H*0.40) : int(H*0.60)])
            bot_l = np.mean(left_profile[int(H*0.85) : H])
        else:
            top_r, mid_r, bot_r = 0, 0, 0
            top_l, mid_l, bot_l = 0, 0, 0

        is_pinggang_kanan = ((top_r - mid_r) > W * 0.015) and ((bot_r - mid_r) > W * 0.015)
        is_pinggang_kiri = ((mid_l - top_l) > W * 0.015) and ((mid_l - bot_l) > W * 0.015)
        is_kiri_lurus = not ((top_l - mid_l > W * 0.04) or (bot_l - mid_l > W * 0.04))

        center_core = crop_img[int(H*0.4):int(H*0.6), int(W*0.4):int(W*0.6)]
        core_density = cv2.countNonZero(center_core) / max(center_core.size, 1)
        is_core_padat = core_density > 0.15 

        top_core = crop_img[0:int(H*0.25), int(W*0.35):int(W*0.65)]
        top_density = cv2.countNonZero(top_core) / max(top_core.size, 1)
        is_atap_terbuka = top_density < 0.35  

        tl_corner = crop_img[0:int(H*0.25), 0:int(W*0.25)]
        tl_density = cv2.countNonZero(tl_corner) / max(tl_corner.size, 1)
        is_pojok_siku = tl_density > 0.35   

        if zone == 'LETTER':
            char = a_ke_h.get(char, char)
            if i == 0:
                if char in ['A', '4', 'C', 'G', '0', 'O', 'Q', '8', '3']:
                    if is_kiri_lurus: char = 'D'
                    elif char in ['O', 'Q', 'C', '0', '8', '3']: char = 'D'
            
            elif char in ['O', 'D', 'B', 'Q', '0', '8', 'U', 'V']:
                if is_atap_terbuka: char = 'U'
                elif is_pinggang_kanan: char = 'B'
                elif is_kiri_lurus: char = 'D'
                else: char = 'O'
                    
        elif zone == 'NUMBER':
            if char in ['O', 'D', 'Q']: char = '0'
            elif char in ['B']: char = '8'
            elif char in ['I', 'L']: char = '1'
            elif char in ['Z']: char = '2'
            elif char in ['A']: char = '4'
            elif char in ['G']: char = '6'
            elif char in ['T']: char = '7'
            elif char in ['J']: char = '5'
            
            if char in ['0', '8']:
                if is_pinggang_kanan or is_pinggang_kiri or is_core_padat: 
                    char = '8'
                else: 
                    char = '0'
                    
            if char in ['3', '5']:
                if is_pojok_siku: char = '5' 
                else: char = '3' 

        hasil.append(char)
    return "".join(hasil)


def segmentasi_karakter_visual(img_plat):
    """ Versi Khusus Dashboard (Mengembalikan dict gambar, boxes, crops) """
    tahapan_visual = {}
    tahapan_visual['original'] = img_plat.copy()

    if len(img_plat.shape) == 3: gray = cv2.cvtColor(img_plat, cv2.COLOR_BGR2GRAY)
    else: gray = img_plat
    
    target_height = 60 
    original_h = gray.shape[0]
    scale = 1.0 
    
    if original_h < target_height:
        scale = target_height / original_h
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif original_h < target_height * 1.5:
        scale = 1.5 
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    tahapan_visual['clahe'] = cv2.cvtColor(gray_clahe, cv2.COLOR_GRAY2BGR)

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
        
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 8))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)

    cv2.rectangle(thresh, (0, 0), (thresh.shape[1]-1, thresh.shape[0]-1), (0, 0, 0), 4)
    tahapan_visual['biner'] = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes_sementara = []
    
    # [FILTER KETAT EDGE CLEANSER]
    max_h = gray.shape[0] * 0.90
    max_w = gray.shape[1] * 0.25
    
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 0.2 < (h/w) < 10.0 and (w*h) > 60 and (gray.shape[0] * 0.25) < h < max_h and w < max_w:
            boxes_sementara.append((x, y, w, h))
            
    boxes = []
    if len(boxes_sementara) > 0:
        centers_y = [y + (h // 2) for (x, y, w, h) in boxes_sementara]
        median_y = np.median(centers_y)
        toleransi_y = gray.shape[0] * 0.40 
        for (x, y, w, h) in boxes_sementara:
            center_y = y + (h // 2)
            if abs(center_y - median_y) <= toleransi_y:
                boxes.append((x, y, w, h))
                
    boxes = sorted(boxes, key=lambda b: b[0])
    
    img_boxes = tahapan_visual['original'].copy()
    if scale != 1.0:
        img_boxes = cv2.resize(img_boxes, (thresh.shape[1], thresh.shape[0]))

    crops = []
    for (x, y, w, h) in boxes:
        cv2.rectangle(img_boxes, (x, y), (x+w, y+h), (0, 255, 0), 1)
        c = thresh[max(0,y):min(thresh.shape[0],y+h), max(0,x):min(thresh.shape[1],x+w)]
        crops.append(c)
        
    tahapan_visual['segmentasi'] = img_boxes
        
    return tahapan_visual, boxes, crops


# ====================================================================
# 2. THREAD KAMERA PENGUJIAN
# ====================================================================
class ThreadAnalisis(QThread):
    sinyal_frame = pyqtSignal(QImage)
    sinyal_tahapan = pyqtSignal(dict, str, str)
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
                
                tinggi_box = b[3] - b[1]
                margin_atas = int(tinggi_box * 0.08)  
                
                y1_aman = max(0, b[1] - margin_atas)
                y2_aman = min(frame.shape[0], b[3])
                x1_aman = max(0, b[0])
                x2_aman = min(frame.shape[1], b[2])
                
                plat = frame[y1_aman:y2_aman, x1_aman:x2_aman]
                
                if plat.size > 0:
                    h_plat, w_plat = plat.shape[:2]
                    if w_plat >= 80 and h_plat >= 25:
                        plat_crop = plat[0:int(h_plat*0.65), :]
                        
                        # Aturan Mutlak Margin 3% Tetap Dipertahankan
                        margin_kiri = int(w_plat * 0.03) 
                        margin_kanan = int(w_plat * 0.03) 
                        plat_crop = plat_crop[:, margin_kiri : w_plat - margin_kanan]

                        tahapan_img, bxs, crps = segmentasi_karakter_visual(plat_crop)
                        
                        mentah = [tebak_cnn(c) for c in crps]
                        teks_mentah = "".join(mentah)
                        teks_hasil = koreksi_format_indonesia(mentah, crps)

                        if not teks_mentah: teks_mentah = "[TIDAK ADA KARAKTER]"
                        if not teks_hasil: teks_hasil = "[GAGAL BACA]"
                        self.sinyal_tahapan.emit(tahapan_img, teks_mentah, teks_hasil)
                        
                        if len(teks_hasil) >= 3 and teks_hasil != "[GAGAL BACA]":
                            cv2.rectangle(frame_disp, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 3)
                            cv2.putText(frame_disp, teks_hasil, (b[0], b[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

                        if self.trigger_capture:
                            os.makedirs("Analisis_Bab4", exist_ok=True)
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = teks_hasil if teks_hasil != "[GAGAL BACA]" else "GAGAL"
                            folder = f"Analisis_Bab4/{ts}_{folder_name}"
                            os.makedirs(folder, exist_ok=True)
                            
                            cv2.imwrite(f"{folder}/0_YOLO_Full.jpg", frame_disp)
                            cv2.imwrite(f"{folder}/1_Crop_Original.jpg", tahapan_img['original'])
                            cv2.imwrite(f"{folder}/2_Grayscale_CLAHE.jpg", tahapan_img['clahe'])
                            cv2.imwrite(f"{folder}/3_Binarization.jpg", tahapan_img['biner'])
                            cv2.imwrite(f"{folder}/4_Segmentasi.jpg", tahapan_img['segmentasi'])
                            
                            with open(f"{folder}/Log_Bacaan.txt", "w") as f:
                                f.write(f"Tebakan Asli CNN: {teks_mentah}\n")
                                f.write(f"Tebakan Final FSM: {teks_hasil}\n")

                            self.sinyal_log.emit(f"✅ CAPTURE BERHASIL! Disimpan di folder {folder}")
                            self.trigger_capture = False

            else:
                if self.trigger_capture:
                    self.sinyal_log.emit("⚠️ GAGAL CAPTURE: Tidak ada pelat!")
                    self.trigger_capture = False

            rgb_img = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format.Format_RGB888).scaled(750, 500, Qt.AspectRatioMode.KeepAspectRatio)
            self.sinyal_frame.emit(qt_img)

        cap.release()

# ====================================================================
# 3. ANTARMUKA PENGGUNA (GUI) SUPER DASHBOARD
# ====================================================================
class DashboardAnalisis(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Super Dashboard Analisis - Bab 4")
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #1e1e2e; color: white;")

        widget_utama = QWidget()
        self.setCentralWidget(widget_utama)
        layout_utama = QHBoxLayout(widget_utama)

        layout_kiri = QVBoxLayout()
        self.label_kamera = QLabel("Memuat Kamera...")
        self.label_kamera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_kamera.setMinimumSize(750, 500)
        self.label_kamera.setStyleSheet("background-color: black; border: 2px solid #a6e3a1;")
        layout_kiri.addWidget(self.label_kamera)

        self.btn_capture = QPushButton("📸 CAPTURE SELURUH TAHAPAN")
        self.btn_capture.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_capture.setStyleSheet("background-color: #89b4fa; color: #1e1e2e; padding: 15px; border-radius: 5px;")
        self.btn_capture.clicked.connect(self.klik_capture)
        layout_kiri.addWidget(self.btn_capture)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: black; color: #f38ba8; font-family: Consolas;")
        self.log_box.setMaximumHeight(100)
        layout_kiri.addWidget(self.log_box)
        layout_utama.addLayout(layout_kiri, stretch=2)

        box_kanan = QGroupBox("Tahapan Pra-Proses (Real-Time)")
        box_kanan.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid white; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        layout_kanan = QVBoxLayout(box_kanan)

        self.lbl_orig = self.buat_label_tahapan("1. Plat Original")
        self.lbl_clahe = self.buat_label_tahapan("2. Grayscale & CLAHE")
        self.lbl_biner = self.buat_label_tahapan("3. Hitam-Putih (Morfologi)")
        self.lbl_seg = self.buat_label_tahapan("4. Bounding Box Karakter")
        
        self.lbl_mentah = QLabel("CNN Asli: -")
        self.lbl_mentah.setStyleSheet("color: #fab387; font-size: 16px; font-weight: bold;")
        self.lbl_final = QLabel("FSM Final: -")
        self.lbl_final.setStyleSheet("color: #a6e3a1; font-size: 20px; font-weight: bold;")

        layout_kanan.addWidget(self.lbl_orig)
        layout_kanan.addWidget(self.lbl_clahe)
        layout_kanan.addWidget(self.lbl_biner)
        layout_kanan.addWidget(self.lbl_seg)
        layout_kanan.addWidget(self.lbl_mentah)
        layout_kanan.addWidget(self.lbl_final)
        layout_kanan.addStretch()

        layout_utama.addWidget(box_kanan, stretch=1)

        self.thread_kamera = ThreadAnalisis()
        self.thread_kamera.sinyal_frame.connect(self.update_kamera)
        self.thread_kamera.sinyal_tahapan.connect(self.update_tahapan)
        self.thread_kamera.sinyal_log.connect(self.update_log)
        self.thread_kamera.start()

    def buat_label_tahapan(self, teks):
        lbl = QLabel(teks)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setMinimumHeight(80)
        lbl.setStyleSheet("background-color: black; border: 1px solid gray;")
        return lbl

    def cv_to_qpixmap(self, cv_img):
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format.Format_RGB888).scaled(250, 100, Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(qt_img)

    def klik_capture(self):
        self.update_log("Merekam bukti analisis...")
        self.thread_kamera.minta_capture()

    def update_kamera(self, frame_qt):
        self.label_kamera.setPixmap(QPixmap.fromImage(frame_qt))

    def update_tahapan(self, gambar_dict, mentah, final):
        self.lbl_orig.setPixmap(self.cv_to_qpixmap(gambar_dict['original']))
        self.lbl_clahe.setPixmap(self.cv_to_qpixmap(gambar_dict['clahe']))
        self.lbl_biner.setPixmap(self.cv_to_qpixmap(gambar_dict['biner']))
        self.lbl_seg.setPixmap(self.cv_to_qpixmap(gambar_dict['segmentasi']))
        
        self.lbl_mentah.setText(f"Tebakan Asli CNN: {mentah}")
        self.lbl_final.setText(f"Koreksi Final FSM: {final}")

    def update_log(self, pesan):
        self.log_box.append(pesan)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.thread_kamera.berjalan = False
        self.thread_kamera.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardAnalisis()
    window.show()
    sys.exit(app.exec())