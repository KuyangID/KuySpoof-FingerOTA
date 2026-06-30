import os

# DAFTAR IZIN (Include Keywords - Brand Major)
INCLUDE = [
    "Google", "Samsung", "Xiaomi", "POCO", "Redmi", 
    "Oppo", "Vivo", "Realme", "OnePlus", "Asus", 
    "Sony", "Motorola", "Lenovo", "Meizu", 
    "Infinix", "Tecno", "Lava", "Itel", "Nokia"
]

def clean_db():
    # Path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = current_dir
    
    # File input (di folder yang sama dengan script)
    input_file = os.path.join(current_dir, "custom_fpraw.txt")
    # File output (di folder files)
    output_file = os.path.join(base_dir, "files", "custom_fp.txt")
    
    if not os.path.exists(input_file):
        print(f"[!] File sumber tidak ditemukan: {input_file}")
        return

    print(f"[*] Memproses {input_file}...")
    
    raw_data = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # Cek apakah mengandung brand yang diizinkan
            is_allowed = False
            for brand in INCLUDE:
                if brand.lower() in line.lower():
                    is_allowed = True
                    break
            
            # Tambahan: Harus mengandung 'release-keys' dan bukan 'test-keys'
            if "release-keys" not in line or "test-keys" in line:
                is_allowed = False
                
            if is_allowed:
                raw_data.append(line)

    # DEDUPLIKASI: Ambil yang terbaru per Model & OS Version
    # Logic: Grouping by 'BRAND/PRODUCT/DEVICE:VERSION'
    # Lalu ambil incremental paling tinggi (biasanya line terakhir setelah sort)
    
    # Sort dulu secara keseluruhan agar versi & inc berurutan
    raw_data.sort()
    
    dedup_dict = {}
    removed_dupes = 0
    
    for line in raw_data:
        try:
            # Format: BRAND/PRODUCT/DEVICE:VERSION/ID/INC:TYPE/TAGS
            parts = line.split(":")
            model_part = parts[0] # BRAND/PRODUCT/DEVICE
            ver_part = parts[1].split("/")[0] # VERSION
            
            # Key unik: Model + Version
            key = f"{model_part}:{ver_part}"
            
            # Simpan line. Karena raw_data sudah di-sort, 
            # line yang masuk belakangan adalah inc/id yang lebih baru (string-wise)
            if key in dedup_dict:
                removed_dupes += 1
            
            dedup_dict[key] = line
        except:
            # Jika format aneh, simpan aja as-is
            dedup_dict[line] = line

    final_data = sorted(list(dedup_dict.values()))
    
    # Pastikan folder output ada
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Tulis hasil ke files/custom_fp.txt
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# List Custom Fingerprint KuySpoof (Strict Cleaned & Premium)\n")
        f.write("# Format: BRAND/PRODUCT/DEVICE:VERSION/ID/INC:TYPE/TAGS\n\n")
        for fp in final_data:
            f.write(fp + "\n")

    print("-" * 35)
    print(f"[*] PEMBERSIHAN SELESAI!")
    print(f"[*] Duplikat dipangkas : {removed_dupes} baris")
    print(f"[*] Berhasil Disimpan  : {len(final_data)} baris")
    print(f"[*] Output: {output_file}")

if __name__ == "__main__":
    clean_db()
