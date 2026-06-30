import requests
import re
import os
import sys

"""
KuyScraper Pro - Python Version
Advanced Fingerprint Scraper for KuySpoof Custom Source.
Scrapes multiple Telegram channels for device property dumps.
"""

# Configuration
CHANNELS = [
    "android_dumps"
]

# GitHub Sources (Direct Raw Files - High Quality)
GITHUB_SOURCES = [
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/firmware_xiaomi_fingerprints/master/Xiaomi.txt",
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/firmware_xiaomi_fingerprints/master/Google.txt",
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/firmware_xiaomi_fingerprints/master/Realme.txt"
]


# Kedalaman scan (Set 0 untuk UNLIMITED / Sampai mentok)
SCRAPE_DEPTH = 0 

# FILTER TANGGAL (Opsional)
# Contoh: Ambil dari bulan 1 sampai bulan 5 tahun 2026
# Set None jika tidak mau filter tanggal
START_MONTH = None # Januari
END_MONTH   = 5  # Mei
YEAR        = 2026

# Regex pattern for Android Build Fingerprint
FP_PATTERN = r'[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+:[0-9.]+/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+'


from datetime import datetime

def scrape_channel(channel, depth=1):
    all_found = set()
    before_id = ""
    
    inf_mode = (depth == 0)
    limit = depth if not inf_mode else 999999
    
    print(f"[*] Scraping @{channel} (Mode: {'UNLIMITED' if inf_mode else 'Depth ' + str(depth)})...")
    if START_MONTH:
        print(f"[*] Filter Tanggal: {START_MONTH}/{YEAR} s/d {END_MONTH}/{YEAR}")
    print("[!] Press Ctrl+C to stop and save results anytime.")
    
    try:
        for i in range(limit):
            url = f"https://t.me/s/{channel}"
            if before_id:
                url += f"?before={before_id}"
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # ── Cek Tanggal Pesan (Jika Filter Aktif) ──
            if START_MONTH:
                time_tags = re.findall(r'<time datetime="([^"]+)"', response.text)
                if time_tags:
                    # Ambil tanggal pesan paling bawah di page ini
                    try:
                        # Format ISO: 2024-05-09T03:22:15+00:00
                        ts_str = time_tags[-1].split('+')[0]
                        msg_date = datetime.fromisoformat(ts_str)
                        
                        start_limit = datetime(YEAR, START_MONTH, 1)
                        end_limit = datetime(YEAR, END_MONTH, 31 if END_MONTH in [1,3,5,7,8,10,12] else 30)
                        
                        # Jika pesan sudah lebih lama dari START_MONTH, STOP CRAWL
                        if msg_date < start_limit:
                            print(f"    [!] Tanggal mencapai {msg_date.date()}. Melewati batas {START_MONTH}/{YEAR}. Berhenti.")
                            break
                            
                        # Jika pesan lebih baru dari END_MONTH, skip page ini tapi lanjut crawl (karena kita mundur ke belakang)
                        if msg_date > end_limit:
                            print(f"    [-] Pesan masih terlalu baru ({msg_date.date()}), lanjut scroll ke belakang...")
                            # Ambil ID buat scroll
                            message_ids = re.findall(rf'/{channel}/(\d+)', response.text)
                            if message_ids:
                                before_id = sorted([int(m) for m in message_ids])[0]
                            continue
                    except:
                        pass

            # Cari fingerprints
            found = re.findall(FP_PATTERN, response.text)
            added_this_page = 0
            for fp in found:
                if "test-keys" not in fp:
                    all_found.add(fp)
                    added_this_page += 1
            
            # Cari ID pesan terkecil di halaman ini buat "scroll" ke atas (before)
            message_ids = re.findall(rf'/{channel}/(\d+)', response.text)
            if message_ids:
                ids = sorted([int(m) for m in message_ids])
                if before_id and ids[0] >= int(before_id):
                    print("    [!] Reached the end of channel history.")
                    break
                before_id = ids[0]
                print(f"    [Page {i+1}] Added {added_this_page} FPs. Current Date: {msg_date.date() if 'msg_date' in locals() else 'Unknown'}")
            else:
                print("    [!] No more messages found.")
                break
                
    except KeyboardInterrupt:
        print("\n[!] Scrape dihentikan oleh user. Menyimpan hasil...")
    except Exception as e:
        print(f"    [!] Error: {e}")
            
    return all_found

def main():
    print("--- KuyScraper Pro v1.3 (Telegram + GitHub) ---")
    
    all_new_fps = set()
    
    # 1. Scrape Telegram
    for channel in CHANNELS:
        fps = scrape_channel(channel, depth=SCRAPE_DEPTH)
        if fps:
            print(f"  [+] Total from @{channel}: {len(fps)} unique release-keys.")
            all_new_fps.update(fps)
        else:
            print(f"  [-] No quality fingerprints found on @{channel}.")

    # 2. Scrape GitHub (Direct Raw)
    print("\n[*] Scraping GitHub Databases...")
    for url in GITHUB_SOURCES:
        try:
            print(f"  [+] Fetching: {url.split('/')[-1]}")
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            found = re.findall(FP_PATTERN, res.text)
            cleaned = [f for f in found if "test-keys" not in f]
            all_new_fps.update(cleaned)
            print(f"    [OK] Added {len(cleaned)} high-quality FPs.")
        except Exception as e:
            print(f"    [!] Failed to fetch GitHub source: {e}")

    # Path resolution
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(base_dir, "files", "custom_fp.txt")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    # ── CLEANING & ADDING ──
    all_fps_pool = set()
    
    # Read existing content
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # STRICT FILTER: Cuma ambil yang ada 'release-keys'
                    # Dan buang barang GSI / AOSP / Emulator
                    BLACKLIST = ["test-keys", "dev-keys", "userdebug", "amz-p", "generic_x86", "vsoc_kiwi_x86_64", "aosp_x86_64", "generic_arm64", "generic_x86_64", "gsi_gms_arm64"]
                    
                    is_junk = any(j in line.lower() for j in BLACKLIST)
                    if "release-keys" in line and not is_junk:
                        all_fps_pool.add(line)


    # Tambahkan hasil scrape baru (sudah difilter di fungsi scrape_channel)
    for fp in all_new_fps:
        if "release-keys" in fp:
            all_fps_pool.add(fp)
    
    # Sortir agar rapi
    final_list = sorted(list(all_fps_pool))

    # Tulis ulang file agar bersih total
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# List Custom Fingerprint KuySpoof (Strict Premium - Release Keys Only)\n")
        f.write("# Format: BRAND/PRODUCT/DEVICE:VERSION/ID/INC:TYPE/TAGS\n\n")
        
        for fp in final_list:
            f.write(f"{fp}\n")

    print("-" * 35)
    print(f"[*] Success!")
    print(f"[*] Strict Premium FPs kept: {len(final_list)}")
    print(f"[*] Junk (test/dev/amz/etc) removed successfully.")
    print(f"[*] Database location: {out_file}")



if __name__ == "__main__":

    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("[!] Error: 'requests' module not found.")
        print("    Install it using: pip install requests")
        sys.exit(1)
        
    main()
