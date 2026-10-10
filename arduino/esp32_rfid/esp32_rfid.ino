/*
  Sistem Parkir Pintar - Modul RFID ESP32
  ========================================
  Deskripsi:
    Sketch ini membaca UID dari kartu/tag RFID menggunakan modul RC522 (SPI)
    pada mikrokontroler ESP32 dan mengirimkan data serial ke komputer
    dengan format: "RFID:<UID_HEX>" pada baud rate 115200.

  Format Serial yang diharapkan Backend Python:
    RFID:B24B2207

  Koneksi Pin ESP32 ke MFRC522:
  ---------------------------------
  MFRC522 Pin     ESP32 Pin
  -----------     ---------
  3.3V            3.3V (PERINGATAN: JANGAN HUBUNGKAN KE 5V!)
  RST             GPIO 22
  GND             GND
  IRQ             (Tidak terhubung)
  MISO            GPIO 19 (VSPI MISO)
  MOSI            GPIO 23 (VSPI MOSI)
  SCK             GPIO 18 (VSPI SCK)
  SDA (SS)        GPIO 21 (atau GPIO 5)
  ---------------------------------
*/

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  21  // SDA / SS Pin
#define RST_PIN 22  // Reset Pin
#define BUZZER_PIN 2 // Opsional: Buzzer/LED indikator (GPIO 2 bawaan built-in LED ESP32)

MFRC522 mfrc522(SS_PIN, RST_PIN);

unsigned long lastTapTime = 0;
const unsigned long debounceDelay = 1500; // Debounce 1.5 detik agar tidak membaca ganda saat kartu ditempel lama
String lastUID = "";

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Tunggu Serial monitor aktif

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  SPI.begin(18, 19, 23, SS_PIN); // SCK, MISO, MOSI, SS
  mfrc522.PCD_Init();
  delay(100);

  // Verifikasi pembacaan modul RC522
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  if (v == 0x00 || v == 0xFF) {
    Serial.println("[ERROR] MFRC522 tidak terdeteksi. Periksa pengkabelan!");
  } else {
    Serial.println("[READY] Reader RFID ESP32 Siap!");
  }
}

void loop() {
  // Cek apakah ada kartu baru di dekat reader
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Cek apakah serial nomor kartu bisa dibaca
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Susun UID menjadi string heksadesimal huruf kapital (misal: B24B2207)
  String uidStr = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uidStr += "0";
    }
    uidStr += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidStr.toUpperCase();

  // Debounce check
  unsigned long now = millis();
  if (uidStr != lastUID || (now - lastTapTime > debounceDelay)) {
    lastUID = uidStr;
    lastTapTime = now;

    // Bunyikan buzzer/LED indikator sejenak
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);

    // Kirim string ke Serial Python
    Serial.println("RFID:" + uidStr);
  }

  // Hentikan enkripsi pada kartu yang terbaca
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}
