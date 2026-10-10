import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTextEdit, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QPixmap, QImage, QFont

import firebase_admin
from firebase_admin import db

# Mengimpor Logika AI/Thread Utama dari file mesin_backend.py
from MainProgramTA import MesinParkirThread

class AplikasiParkir(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistem Parkir Pintar (TA - UNIKOM)")
        self.resize(1020, 800) 
        
        # LOGIKA DESAIN GUI (Menggunakan QSS): Memberikan gaya modern dengan skema warna yang nyaman di mata
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            QTabWidget::pane { border: 1px solid #313244; border-radius: 5px; }
            QTabBar::tab { background: #313244; color: #a6adc8; padding: 10px 25px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; }
            QGroupBox { border: 2px solid #313244; border-radius: 8px; margin-top: 1.5ex; font-weight: bold; color: #89b4fa; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
            QPushButton { border-radius: 8px; font-weight: bold; }
            QPushButton:hover { opacity: 0.8; }
            QTextEdit { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; padding: 5px; color: #a6e3a1; }
            QTableWidget { background-color: #181825; border: 2px solid #313244; border-radius: 6px; gridline-color: #313244; color: #cdd6f4; }
            QHeaderView::section { background-color: #313244; color: white; padding: 6px; font-weight: bold; border: none; }
        """)

        # Mengatur Menu Tab (Tampilan Utama, Database, Terminal Log)
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tab_dashboard = QWidget()
        self.tab_database = QWidget()
        self.tab_log = QWidget()
        
        self.tabs.addTab(self.tab_dashboard, "Tampilan Utama")
        self.tabs.addTab(self.tab_database, "Database Parkir")
        self.tabs.addTab(self.tab_log, "Terminal Log")
        main_layout.addWidget(self.tabs)

        # Memanggil struktur layout per-halaman tab
        self.setup_tab_dashboard()
        self.setup_tab_log()
        self.setup_tab_database()

        # LOGIKA JEMBATAN KOMUNIKASI (Signals & Slots):
        # Menghubungkan Backend (MesinParkirThread) ke GUI (AplikasiParkir).
        # Setiap kali Mesin mendeteksi hal baru, ia "mengetuk pintu" fungsi-fungsi di bawah ini untuk mengupdate layar.
        self.mesin_thread = MesinParkirThread()
        self.mesin_thread.sinyal_kamera_utama.connect(self.update_kamera_utama) # Update Gambar Kamera
        self.mesin_thread.sinyal_log.connect(self.update_log) # Tambah Teks ke Terminal
        self.mesin_thread.sinyal_refresh_db.connect(self.muat_data_database) # Reload Tabel GUI
        self.mesin_thread.sinyal_status_utama.connect(self.update_status_utama) # Update Teks Kotak Status Masuk/Keluar
        self.mesin_thread.start()

    def setup_tab_dashboard(self):
        # Layout untuk halaman Tampilan Utama (Streaming Video)
        layout = QVBoxLayout(self.tab_dashboard)
        group_cam = QGroupBox("Kamera Pemantau Utama")
        cam_layout = QVBoxLayout()
        self.label_kamera = QLabel()
        self.label_kamera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_kamera.setMinimumSize(960, 540)
        self.label_kamera.setStyleSheet("background-color: #000000; border-radius: 5px;")
        cam_layout.addWidget(self.label_kamera)
        group_cam.setLayout(cam_layout)
        layout.addWidget(group_cam, stretch=4)

        # Layout kotak notifikasi (Diterima / Ditolak)
        group_status = QGroupBox("Status Gerbang")
        status_layout = QVBoxLayout()
        self.label_status_utama = QLabel("INISIALISASI SISTEM...")
        self.label_status_utama.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status_utama.setStyleSheet("font-size: 24px; font-weight: bold; background-color: #11111b; border: 2px solid #f9e2af; border-radius: 8px; padding: 20px;")
        status_layout.addWidget(self.label_status_utama)
        group_status.setLayout(status_layout)
        layout.addWidget(group_status, stretch=1)

        btn_layout = QHBoxLayout()
        btn_buka_folder = QPushButton("📂 Buka Folder Bukti")
        btn_buka_folder.setStyleSheet("background-color: #f9e2af; color: #1e1e2e; padding: 15px;")
        btn_buka_folder.clicked.connect(lambda: os.startfile("hasil_capture") if os.path.exists("hasil_capture") else None)
        self.btn_keluar = QPushButton("⛔ Matikan Sistem")
        self.btn_keluar.setStyleSheet("background-color: #f38ba8; color: #1e1e2e; padding: 15px;")
        self.btn_keluar.clicked.connect(self.close)
        btn_layout.addWidget(btn_buka_folder)
        btn_layout.addWidget(self.btn_keluar)
        layout.addLayout(btn_layout)

    def setup_tab_database(self):
        # Layout untuk halaman Tabel Riwayat & Sinkronisasi
        layout = QVBoxLayout(self.tab_database)
        header_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setStyleSheet("background-color: #89b4fa; color: #1e1e2e; padding: 8px;")
        btn_refresh.clicked.connect(self.muat_data_database)
        
        btn_sinkron = QPushButton("☁️ Sinkron Firebase")
        btn_sinkron.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; padding: 8px;") 
        btn_sinkron.clicked.connect(self.sinkron_sqlite_ke_firebase)
        
        header_layout.addWidget(btn_refresh)
        header_layout.addWidget(btn_sinkron)
        layout.addLayout(header_layout)

        group_aktif = QGroupBox("Kendaraan Parkir (aktif)")
        layout_aktif = QVBoxLayout()
        self.tabel_aktif = QTableWidget()
        self.tabel_aktif.setColumnCount(4)
        self.tabel_aktif.setHorizontalHeaderLabels(["ID", "UID RFID", "Plat Nomor", "Waktu Masuk"])
        self.tabel_aktif.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout_aktif.addWidget(self.tabel_aktif)
        group_aktif.setLayout(layout_aktif)

        group_riwayat = QGroupBox("Riwayat Parkir")
        layout_riwayat = QVBoxLayout()
        self.tabel_riwayat = QTableWidget()
        self.tabel_riwayat.setColumnCount(6)
        self.tabel_riwayat.setHorizontalHeaderLabels(["ID", "UID", "Plat", "Masuk", "Keluar", "Status"])
        self.tabel_riwayat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout_riwayat.addWidget(self.tabel_riwayat)
        group_riwayat.setLayout(layout_riwayat)

        layout.addWidget(group_aktif)
        layout.addWidget(group_riwayat)

    def setup_tab_log(self):
        # Layout halaman terminal log & Tombol Simulasi
        layout = QVBoxLayout(self.tab_log)
        self.btn_sim_rfid = QPushButton("📡 Simulasi Tap RFID")
        self.btn_sim_rfid.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; padding: 12px;")
        self.btn_sim_rfid.clicked.connect(lambda: setattr(self.mesin_thread, 'simulasi_rfid_uid', "B24B2207"))
        layout.addWidget(self.btn_sim_rfid)

        self.teks_log = QTextEdit()
        self.teks_log.setReadOnly(True)
        self.teks_log.setFont(QFont("Consolas", 10))
        layout.addWidget(self.teks_log)

    @pyqtSlot()
    def sinkron_sqlite_ke_firebase(self):
        """
        LOGIKA HYBRID OFFLINE-FIRST (Skripsi Focus):
        Memungkinkan administrator untuk menimpa/backup secara utuh isi database lokal (SQLite)
        menuju ke Firebase Cloud (Online).
        """
        try:
            conn = sqlite3.connect('data_parkir_unikom.db')
            cursor = conn.cursor()
            
            # Sync tabel yang sedang parkir
            cursor.execute("SELECT rfid_uid, plat_nomor, waktu_masuk FROM parkir_aktif")
            rows_aktif = cursor.fetchall()
            ref_aktif = db.reference('parkir_aktif')
            ref_aktif.set({}) # Bersihkan db cloud sebelum sinkronisasi ulang
            for r in rows_aktif:
                ref_aktif.child(r[0]).set({'rfid_uid': r[0], 'plat_nomor': r[1], 'waktu_masuk': r[2]})

            # Sync tabel riwayat komplit
            cursor.execute("SELECT * FROM riwayat_parkir")
            rows_riwayat = cursor.fetchall()
            ref_riwayat = db.reference('riwayat_parkir')
            ref_riwayat.set({}) 
            for row in rows_riwayat:
                ref_riwayat.push({'id_sqlite': row[0], 'rfid_uid': row[1], 'plat_nomor': row[2], 'waktu_masuk': row[3], 'waktu_keluar': row[4] if row[4] else "-", 'status': row[5]})
            conn.close()
            self.update_log("[SINKRONISASI SUKSES] Sinkronisasi Selesai.")
        except Exception as e:
            self.update_log(f"[ERROR] {e}")

    @pyqtSlot()
    def muat_data_database(self):
        """Membaca isi database lokal SQLite dan menempelkannya ke baris-baris UI Tabel."""
        try:
            conn = sqlite3.connect('data_parkir_unikom.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parkir_aktif")
            rows = cursor.fetchall()
            self.tabel_aktif.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabel_aktif.setItem(i, j, item)
            
            cursor.execute("SELECT * FROM riwayat_parkir ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            self.tabel_riwayat.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val if val else "-"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabel_riwayat.setItem(i, j, item)
            conn.close()
        except: pass

    @pyqtSlot(str, str)
    def update_status_utama(self, teks, warna):
        # Update teks dengan warna khusus (Hijau/Diterima, Merah/Ditolak)
        self.label_status_utama.setText(teks)
        self.label_status_utama.setStyleSheet(f"font-size: 24px; font-weight: bold; background-color: #11111b; color: {warna}; border: 3px solid {warna}; border-radius: 8px; padding: 20px;")

    @pyqtSlot(QImage)
    def update_kamera_utama(self, image):
        # Menempelkan frame video terbaru (PixMap) ke kotak layar UI
        self.label_kamera.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(str)
    def update_log(self, text):
        # Menambahkan baris teks baru ke terminal log secara otomatis scroll-down
        if hasattr(self, 'teks_log'):
            self.teks_log.append(text)
            self.teks_log.verticalScrollBar().setValue(self.teks_log.verticalScrollBar().maximum())

    def closeEvent(self, event):
        # Mematikan Thread Backend dengan aman saat tombol exit merah di-klik
        self.mesin_thread.terminate() 
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AplikasiParkir()
    window.show()
    sys.exit(app.exec())