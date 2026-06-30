#!/usr/bin/env python3
import csv
import json
import os
import re
import random
import urllib.request

# Configuration
CSV_URL = "https://storage.googleapis.com/play_public/supported_devices.csv"
CSV_PATH = "supported_devices.csv"
DB_PATH = "files/database"

TARGET_BRANDS = [
    {"file": "samsung",  "match": "samsung"},
    {"file": "xiaomi",   "match": "xiaomi|redmi|poco|pocophone"},
    {"file": "oppo",     "match": "oppo"},
    {"file": "vivo",     "match": "vivo"},
    {"file": "realme",   "match": "realme"},
    {"file": "motorola", "match": "motorola"},
    {"file": "oneplus",  "match": "oneplus"},
    {"file": "asus",     "match": "asus"},
    {"file": "sony",     "match": "sony"},
    {"file": "google",   "match": "google"},
    {"file": "nokia",    "match": "nokia"},
    {"file": "huawei",   "match": "huawei"},
    {"file": "honor",    "match": "honor"},
    {"file": "infinix",  "match": "infinix"},
    {"file": "tecno",    "match": "tecno"},
    {"file": "advan",    "match": "advan"},
    {"file": "zte",      "match": "zte"},
    {"file": "lenovo",   "match": "lenovo"},
]

# Android Version Guessing Logic (v)
def get_android_version(brand, model, device):
    brand = brand.lower()
    m = model.upper()
    d = device.lower()

    if "samsung" in brand:
        if re.search(r"SM-S93[0-9]", m): return 15
        if re.search(r"SM-S92[0-9]", m): return 14
        if re.search(r"SM-S91[0-9]", m): return 13
        if re.search(r"SM-S90[0-9]", m): return 12
        if re.search(r"SM-G99[0-9]", m): return 13
        if re.search(r"SM-G98[0-9]", m): return 12
        if re.search(r"SM-G97[0-9]", m): return 11
        if re.search(r"SM-A[357]5", m): return 15
        if re.search(r"SM-A[357]4", m): return 14
        if re.search(r"SM-A[357]3", m): return 13
        return 12
    
    if any(x in brand for x in ["xiaomi", "redmi", "poco"]):
        if re.search(r"^(24|25)", m): return 15
        if re.search(r"^23", m): return 14
        if re.search(r"^22", m): return 13
        if re.search(r"^21", m): return 12
        if re.search(r"^(marble|mondrian|fuxi|nuwa|thor|pissarro|ruby|fleur|topaz)", d): return 13
        return 11

    if "google" in brand:
        if re.search(r"^(shiba|husky|akita|tokay|caiman|komodo)", d): return 15
        if re.search(r"^(frankel|blazer|mustang|rango)", d): return 16
        return 14

    if "oneplus" in brand:
        if re.search(r"CPH2[56][0-9]{2}", m): return 15
        if re.search(r"CPH24[0-9]{2}", m): return 14
        return 13

    if re.search(r"^2[45][0-9]{3}", m): return 15
    if re.search(r"^23[0-9]{3}", m): return 14
    return 12

def is_mobile_phone(name, model, device):
    if not name or not all(ord(c) < 128 for c in name): return False
    name, mod, dev = name.lower(), model.lower(), device.lower()
    
    hard_excludes = [
        'chromebook', 'cheets', 'bravia', 'mitv', 'mi tv', 'android tv', 'google tv', 
        'laptop', 'tablet', 'watch', 'buds', 'earphone', 'monitor', 'display', 
        'panel', 'signage', 'stick', 'box', 'player', 'car', 'automotive',
        'projector', 'meeting', 'tv', 'uhd', 'led', 'lcd', 'oled', 'smart', 
        'commercial', 'signage', 'dtab', 'viera', 'aquos tv', 'stb', 'ott', 'dvb',
        'router', 'cpe', 'hotspot', 'modem', 'gateway', 'sketsa', 'tab', 'pad',
        'terminal', 'pos ', 'hub ', 'cast', 'bridge', 'vx_neo', 'vx lite', 'vane'
    ]
    if any(x in name or x in mod or x in dev for x in hard_excludes): return False
    if mod.startswith('zxv') or mod.startswith('b86') or mod.startswith('zx'): return False
    if ',' in name or ',' in mod: return False
    if mod.startswith('d-') or mod.startswith('so-'): return False
    if len(name) < 3 or name.isdigit(): return False
    if re.search(r'^sm-[txpw][0-9]', mod): return False
    if re.search(r'\btab\b|\bpad\b', name): return False
    emu_keywords = ['emulator', 'generic', 'sdk built for', 'x86', 'vbox', 'vsoc', 'gphone', 'arm64', 'qemu']
    if any(x in name or x in mod or x in dev for x in emu_keywords): return False
    return True

def download_csv():
    print(f"[*] Downloading CSV from {CSV_URL}...")
    try:
        urllib.request.urlretrieve(CSV_URL, CSV_PATH)
        print("[+] Download complete.")
    except Exception as e:
        print(f"[!] Download failed: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KuySpoof Database Generator")
    parser.add_argument("--update", action="store_true", help="Download latest CSV from Google")
    args = parser.parse_args()

    if args.update or not os.path.exists(CSV_PATH): download_csv()
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

    print("[*] Processing CSV...")
    results = {b["file"]: [] for b in TARGET_BRANDS}
    seen = set()

    try:
        with open(CSV_PATH, "r", encoding="utf-16") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get("Retail Branding", "").strip()
                model = row.get("Model", "").strip()
                device = row.get("Device", "").strip()
                mname = row.get("Marketing Name", "").strip()

                if not model or not device or not brand: continue
                if model in seen: continue
                
                target = None
                bl = brand.lower()
                ml = model.upper()
                
                # Priority 0: Forced Model Prefixes (Fix nyasar)
                if ml.startswith("GT-") or ml.startswith("SM-") or ml.startswith("SGH-") or ml.startswith("SCH-"):
                    target = "samsung"
                elif ml.startswith("XT") or ml.startswith("MOTO"):
                    target = "motorola"
                elif "PIXEL" in ml:
                    target = "google"

                # Priority 1: Strict Retail Branding Match
                if not target:
                    for b_cfg in TARGET_BRANDS:
                        if b_cfg["file"] == "google":
                            if bl == "google": target = "google"; break
                        elif b_cfg["match"] in bl:
                            target = b_cfg["file"]; break
                
                # Priority 2: Keyword match in Marketing/Model
                if not target:
                    search_str = f"{mname} {model}".lower()
                    for b_cfg in TARGET_BRANDS:
                        if b_cfg["file"] == "google": continue 
                        if re.search(b_cfg["match"], search_str):
                            target = b_cfg["file"]; break
                
                if not target: continue
                if not is_mobile_phone(mname, model, device): continue

                # Technical filtering
                if target == "samsung" and not model.upper().startswith("SM-"): continue
                if target == "sony" and not re.search(r"^(XQ-|SO-|SOG)", model, re.IGNORECASE): continue
                
                # Cleanup Marketing Name (Remove anything in brackets/parentheses and technical codes)
                clean_mname = re.sub(r'[\(\[\{].*?[\)\]\}]', '', mname) # Remove (...) [...] {...}
                clean_mname = re.sub(r'(?i)\bmodel\b.*$', '', clean_mname) # Remove "Model ..."
                clean_mname = re.sub(r'(?i)\bSM-[A-Z0-9-]+\b', '', clean_mname) # Remove SM-XXXX codes
                clean_mname = clean_mname.split('/')[0].strip()
                
                if not clean_mname or len(clean_mname) < 2: 
                    clean_mname = model

                seen_key = f"{target}_{model}_{device}"
                if seen_key in seen: continue
                seen.add(seen_key)

                results[target].append({
                    "m": clean_mname, # Marketing Name
                    "k": model,       # Model (technical code)
                    "d": device       # Device (codename)
                })
    except Exception as e:
        print(f"[!] Error reading CSV: {e}"); return

    # Save to JSON
    for brand_file, items in results.items():
        if not items: continue
        items.sort(key=lambda x: x["m"])
        out_path = os.path.join(DB_PATH, f"{brand_file}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
        print(f"[+] Generated {out_path} ({len(items)} devices)")

    print("[*] All done!")

if __name__ == "__main__":
    main()
