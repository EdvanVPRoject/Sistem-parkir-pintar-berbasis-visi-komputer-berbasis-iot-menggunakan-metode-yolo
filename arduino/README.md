# Modul IoT RFID (ESP32 + MFRC522)

Folder ini berisi firmware mikrokontroler ESP32 untuk membaca kartu RFID (MFRC522) yang terpasang di gerbang masuk/keluar parkir.

## Skema Pengkabelan (Wiring Pinout)

| Pin RFID RC522 | Pin ESP32 (DevKit v1) | Keterangan |
|----------------|-----------------------|------------|
| **3.3V** | **3.3V** |  **PENTING:** Jangan hubungkan ke 5V karena akan merusak modul RC522! |
| **GND** | **GND** | Ground bersama |
| **RST** | **GPIO 22** | Reset Pin |
| **SDA / SS** | **GPIO 21** | SPI Slave Select |
| **SCK** | **GPIO 18** | SPI Clock |
| **MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **MISO** | **GPIO 19** | SPI Master In Slave Out |
| **IRQ** | *(Tidak Terhubung)* | Tidak digunakan |

## Kebutuhan Library Arduino IDE

Pastikan library berikut terpasang melalui **Library Manager** di Arduino IDE (`Ctrl + Shift + I`):
1. **MFRC522** by *GithubCommunity* (versi 1.4.10 atau terbaru).

## Konfigurasi Board Arduino IDE
1. Board: **DOIT ESP32 DEVKIT V1** (atau modul ESP32 generic Anda).
2. Upload Speed: `921600` (atau `115200`).
3. Port: Sesuaikan dengan port COM ESP32 Anda (misal `COM3`, `COM4`, `COM5`, `COM8`).

## Format Komunikasi Serial
ESP32 mengirimkan data pembacaan UID kartu ke komputer melalui kabel USB Serial dengan kecepatan **115200 baud**:
```text
RFID:B24B2207
```
Format prefix `RFID:` ini langsung dikenali oleh backend Python (`MainProgramTA.py`).
