# 📱 Samsung Android PIN Bruteforce Tool

> Via USB HID (Android Open Accessory 2.0)  
> Platform: **Kali Linux** & **Termux**  
> Support: **4-digit** & **6-digit** PIN Samsung  
> **NEW:** Auto-detect device + Stealth Mode

---

## ⚠️ DISCLAIMER

> Tool ini **HANYA** untuk digunakan pada perangkat **milik sendiri**.  
> Penggunaan pada perangkat orang lain adalah **ILEGAL** dan dapat dikenakan sanksi hukum.  
> Penulis tidak bertanggung jawab atas penyalahgunaan tool ini.

---

## 🆕 Fitur Baru

### 🔍 Auto-Detect Device
Tool sekarang secara otomatis mendeteksi Samsung device yang terhubung via USB dan menampilkan informasi lengkap:

```
╔══════════════════════════════════════════════════════════════╗
║                    📱 DEVICE DETECTED                        ║
╠══════════════════════════════════════════════════════════════╣
║  Device Name    : Samsung Galaxy A55 5G                      ║
║  Model          : SM-A556B                                   ║
║  Codename       : a55x                                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Android        : 14 (original) → 16 (current)               ║
║  One UI         : 6.1 (original) → 8.0 (current)             ║
║  ─────────────────────────────────────────────────────────── ║
║  Screen         : 6.6" (1080x2340)                           ║
║  Chipset        : Exynos 1480                                ║
║  Release Year   : 2024                                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Lockout Policy : 5 attempts → 30s cooldown                  ║
╚══════════════════════════════════════════════════════════════╝
```

### 🕵️ Stealth Mode
Mode tersembunyi untuk menghindari deteksi sistem:
- **Delay natural** dengan random jitter - seperti ketikan manusia
- **Tidak ada countdown lockout** yang terlihat di terminal
- **Aktivitas tap random** untuk menghindari timeout
- **Waktu tunggu tersebar** dalam beberapa segmen

```bash
# Aktifkan stealth mode
sudo python3 src/main.py -p 4 --stealth
```

---

## 🔧 Cara Kerja

Tool ini memanfaatkan protokol **Android Open Accessory (AOA) 2.0** untuk mensimulasikan perangkat HID (touchscreen) melalui USB. Komputer/laptop yang menjalankan script ini akan terdeteksi sebagai "aksesori" oleh Android, lalu mengirimkan event sentuhan virtual untuk mencoba PIN satu per satu.

```
[Kali Linux / Termux] ──USB──► [Samsung Android]
   Python Script                  Lock Screen
   (HID Events)                   (PIN Keypad)
```

### Alur kerja:
1. Script mendeteksi Android device via USB
2. **Mengidentifikasi device dan menampilkan info lengkap**
3. Mengirim sinyal AOA untuk switch ke accessory mode
4. Mendaftarkan HID touchscreen virtual
5. **Menggunakan koordinat keypad yang sesuai untuk device**
6. Mensimulasikan ketukan pada keypad PIN lock screen
7. **Stealth mode: menangani lockout secara tersembunyi**
8. Menyimpan progress otomatis (bisa di-resume)

---

## 📋 Requirements

### Hardware
- Kabel USB (bukan OTG) dari laptop/PC ke Samsung
- Samsung Android yang **terkunci** (lock screen PIN aktif)
- USB Debugging **TIDAK perlu aktif**

### Software - Kali Linux
```bash
sudo apt install python3 python3-pip libusb-1.0-0
pip3 install pyusb
```

### Software - Termux
```bash
pkg install python python-pip libusb
pip install pyusb
```

---

## 🚀 Instalasi

```bash
# Clone / ekstrak tool
cd android-bruteforce-samsung

# Jalankan installer otomatis
chmod +x install.sh
./install.sh
```

---

## 📖 Penggunaan

### Quick Start

```bash
# Test koneksi dan lihat info device
./test_connection.sh

# Bruteforce 4-digit PIN (standard mode)
./run_4pin.sh

# Bruteforce dengan STEALTH MODE (rekomendasi)
sudo python3 src/main.py -p 4 --stealth

# Bruteforce 6-digit PIN
./run_6pin.sh
```

### Melihat Daftar Device yang Didukung

```bash
sudo python3 src/main.py --list-devices
```

Output:
```
═══════════════════════════════════════════════════════════════════
  DAFTAR SAMSUNG DEVICES YANG DIDUKUNG
═══════════════════════════════════════════════════════════════════
Model           Device Name                    Android      One UI    
───────────────────────────────────────────────────────────────────
SM-A556B        Samsung Galaxy A55 5G          16           8.0       
SM-A556E        Samsung Galaxy A55 5G          16           8.0       
SM-A546B        Samsung Galaxy A54 5G          15           7.0       
SM-A536B        Samsung Galaxy A53 5G          14           6.1       
SM-S928B        Samsung Galaxy S24 Ultra       15           7.0       
...
```

### Manual (langsung via Python)

```bash
# 4-digit PIN dengan stealth mode (REKOMENDASI)
sudo python3 src/main.py -p 4 --stealth

# 6-digit PIN dengan stealth mode
sudo python3 src/main.py -p 6 --stealth

# Standard mode (dengan countdown lockout)
sudo python3 src/main.py -p 4

# Verbose mode (tampilkan semua detail)
sudo python3 src/main.py -p 4 --stealth --verbose

# Mulai dari awal (reset progress)
sudo python3 src/main.py -p 4 --stealth --reset

# Coba hanya 50 PIN pertama (untuk test)
sudo python3 src/main.py -p 4 --stealth --limit 50

# Mulai dari PIN tertentu
sudo python3 src/main.py -p 4 --stealth --start-pin 5000

# Coba satu PIN saja
sudo python3 src/main.py --single-pin 1234

# Dry run (simulasi tanpa device)
sudo python3 src/main.py -p 4 --dry-run --limit 20

# Custom delay (lebih lambat = lebih aman)
sudo python3 src/main.py -p 4 --stealth --delay 2000 --key-delay 100

# Pakai file PIN custom
sudo python3 src/main.py -p 4 -f /path/to/my-pins.txt
```

### Semua opsi

```
  -p, --pin-length   Panjang PIN: 4 atau 6 (default: 4)
  -f, --pin-file     Path file PIN kustom
  -v, --verbose      Output debug detail
  --stealth          Aktifkan STEALTH MODE (tidak terdeteksi sistem)
  --delay            Delay ms setelah setiap PIN (default: 1200)
  --key-delay        Delay ms antar ketukan (default: 80)
  --reset            Reset progress, mulai dari awal
  --test-connection  Test koneksi USB dan tampilkan info device
  --dry-run          Simulasi tanpa hardware
  --limit N          Batasi N percobaan
  --start-pin PIN    Mulai dari PIN tertentu
  --single-pin PIN   Coba satu PIN saja
  --list-devices     Tampilkan daftar device yang didukung
```

---

## 🔢 PIN List

Tool ini menyediakan beberapa jenis PIN list yang bisa dipakai:

### PIN List yang Tersedia

| File | Total PIN | Deskripsi |
|------|-----------|-----------|
| `pins-4-digit.txt` | 10,000 | Semua kombinasi 4-digit, diurutkan dari yang paling populer |
| `pins-4-smart.txt` | 649 | PIN 4-digit prioritas tinggi (rekomendasi untuk test awal) |
| `pins-6-digit.txt` | 1,000,000 | Semua kombinasi 6-digit, diurutkan dari yang paling populer |
| `pins-6-smart.txt` | 13,609 | PIN 6-digit prioritas tinggi (rekomendasi untuk test awal) |

### PIN Prioritas Tinggi (Smart List)

PIN smart list berisi PIN yang paling sering digunakan orang:
- **Pattern patterns**: 1234, 0000, 1111, 1212, dst
- **Tahun lahir**: 1990-2024
- **Tanggal**: MMDD format (0101, 1212, dst)
- **Keyboard patterns**: 2580 (kolom tengah), 1379, dst
- **Repeated patterns**: 1122, 3344, 5566, dst

### Generate PIN List Custom

Gunakan `pin_generator.py` untuk membuat PIN list custom:

```bash
# Generate semua PIN list
python3 src/pin_generator.py --all

# Generate hanya 4-digit PIN
python3 src/pin_generator.py -p 4 -o pins/my-pins.txt

# Generate smart list (prioritas tinggi)
python3 src/pin_generator.py -p 4 --smart -o pins/my-smart-pins.txt

# Generate dengan custom PIN di awal
python3 src/pin_generator.py -p 4 --custom "1234,5678,9999,0000" -o pins/custom.txt

# Lihat statistik
python3 src/pin_generator.py -p 4 --stats
```

### Menggunakan PIN List Custom

```bash
# Pakai file PIN custom
sudo python3 src/main.py -p 4 -f pins/pins-4-smart.txt --stealth

# Pakai file PIN dengan custom PIN di awal
sudo python3 src/main.py -p 4 -f pins/custom.txt --stealth
```

---

## 📁 Struktur Project

```
android-bruteforce-samsung/
├── src/
│   ├── main.py           # Entry point utama
│   ├── bruteforce.py     # Engine bruteforce (progress, stealth mode)
│   ├── touchscreen.py    # Controller HID touchscreen
│   ├── usb_accessory.py  # USB AOA connection + auto-detect
│   ├── device_database.py # Database device Samsung
│   └── hid_descriptor.py # HID report descriptor & AOA constants
├── pins/
│   ├── pins-4-digit.txt  # 10,000 PIN 4-digit (sorted by frequency)
│   ├── pins-4-smart.txt  # 649 PIN 4-digit prioritas tinggi (rekomendasi)
│   ├── pins-6-digit.txt  # 1,000,000 PIN 6-digit (sorted by frequency)
│   └── pins-6-smart.txt  # 13,609 PIN 6-digit prioritas tinggi (rekomendasi)
├── src/
│   ├── pin_generator.py  # Tool untuk generate PIN list custom
├── logs/
│   ├── progress.txt      # Resume progress (auto)
│   ├── found.txt         # PIN yang ditemukan (auto)
│   └── bruteforce.log    # Log lengkap
├── install.sh            # Installer otomatis
├── run_4pin.sh           # Launcher 4-digit
├── run_6pin.sh           # Launcher 6-digit
├── test_connection.sh    # Test koneksi USB
└── README.md
```

---

## 📱 Samsung Galaxy A55 5G - Spesifikasi Lengkap

| Spesifikasi | Detail |
|-------------|--------|
| Model | SM-A556B / SM-A556E / SM-A556B/DS |
| Nama | Samsung Galaxy A55 5G |
| Android (Original) | 14 |
| Android (Current) | 16 |
| One UI (Original) | 6.1 |
| One UI (Current) | 8.0 |
| Layar | 6.6" Super AMOLED, 1080x2340 |
| Chipset | Exynos 1480 |
| Lockout Policy | 5 attempts → 30 detik cooldown |

---

## ⚙️ Koordinat Keypad Samsung

Koordinat keypad otomatis dihitung berdasarkan resolusi layar device yang terdeteksi. Untuk Samsung A55 5G (1080x2340):

```
┌─────────────────────────────────────┐
│     Lock Screen Samsung             │
│                                     │
│  ┌─────────┬─────────┬─────────┐    │
│  │    1    │    2    │    3    │    │
│  ├─────────┼─────────┼─────────┤    │
│  │    4    │    5    │    6    │    │
│  ├─────────┼─────────┼─────────┤    │
│  │    7    │    8    │    9    │    │
│  ├─────────┼─────────┼─────────┤    │
│  │   DEL   │    0    │         │    │
│  └─────────┴─────────┴─────────┘    │
└─────────────────────────────────────┘
```

Koordinat di-normalisasi ke 0-10000 (HID standard).

---

## 📊 Estimasi Waktu

| PIN Length | Total kombinasi | Standard Mode | Stealth Mode |
|------------|----------------|---------------|--------------|
| 4-digit    | 10,000          | ~2 jam        | ~1.5 jam    |
| 6-digit    | 1,000,000       | ~8 hari       | ~5 hari     |

> Catatan: Samsung lockout 30 detik setiap 5 percobaan salah  
> Stealth mode lebih cepat karena delay natural tanpa countdown

---

## 🔄 Resume / Lanjut dari Checkpoint

Jika proses terhenti (Ctrl+C, putus listrik, dll), progress tersimpan di `logs/progress.txt`. Jalankan lagi perintah yang sama untuk lanjut otomatis:

```bash
./run_4pin.sh        # Otomatis lanjut dari progress terakhir
./run_6pin.sh        # Sama
```

Untuk mulai dari awal:

```bash
./run_4pin.sh --reset
```

---

## 🐛 Troubleshooting

### "Device tidak ditemukan"
```bash
# Cek apakah device terdeteksi
lsusb | grep -i samsung

# Cek permissions
sudo chmod 666 /dev/bus/usb/*/*

# Atau pakai sudo
sudo python3 src/main.py -p 4 --stealth
```

### "Gagal switch ke AOA mode"
- Pastikan kabel USB berfungsi baik (bukan kabel charge-only)
- Coba cabut-colok kabel USB
- Pastikan Android masih di lock screen

### "Ketukan tidak tepat sasaran"
- Tool otomatis menggunakan koordinat yang sesuai untuk device
- Gunakan `--single-pin 1234` untuk test posisi
- Tambah delay: `--delay 2000 --key-delay 150`

### "Sistem mendeteksi brute force"
- Gunakan `--stealth` mode
- Tool akan menggunakan delay natural dengan jitter random
- Tidak ada countdown lockout yang terlihat

---

## 📝 Notes

- Tool ini bekerja **tanpa USB Debugging** aktif
- Tidak perlu root pada target device
- Perlu root/sudo di Kali Linux untuk akses libusb
- Di Termux, tidak perlu root (USB host langsung diakses)
- PIN list diurutkan dari yang paling sering dipakai orang
- **Stealth mode** direkomendasikan untuk menghindari deteksi

---

## 🔒 Keamanan & Privasi

Tool ini dirancang untuk:
- Recovery PIN pada device milik sendiri
- Testing keamanan device sendiri
- Edukasi tentang keamanan Android

**TIDAK untuk:**
- Membuka kunci device orang lain
- Aktivitas ilegal apapun

---

## 📜 Lisensi

Tool ini dibuat untuk tujuan edukasi. Pengguna bertanggung jawab penuh atas penggunaan tool ini.

---

## 🙏 Credits

- Android Open Accessory Protocol
- Samsung Device Database
- HID Touchscreen Implementation