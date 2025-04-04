import subprocess
import random
import os
from glob import glob

# === Configuration ===
NORMAL_DATASET_DIR = "01"
ATTACK_DATASET_FILES = [
    "02/in/2025/04/01/in-S0_20250401.14",
    "02/in/2025/04/01/in-S0_20250401.15"
]
OUTPUT_FOLDER = "final_dataset_chunks"
TEMP_DIR = "temp"
NUM_COPIES = 1
BYTE_SPLIT_LIMIT = 512000  # in bytes

# === Attack Labels – Unique destination ports for each attack type ===
ATTACK_PORTS = {
    "slow_read": 6001,
    "rudy": 6002,
    "ping_flood": 6003,
    "blacknurse": 6004,
    "xmas_scan": 6005,
    "udp_flood": 6006,
    "syn_flood": 6007,
    "slowloris": 6008
}


def get_all_silk_files(directory):
    return [f for f in glob(os.path.join(directory, "*")) if os.path.isfile(f)]


def extract_common_ips(dataset):
    cmd = f"rwstats --fields=sip,dip --count=50 {dataset}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    ip_list = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            ip_list.append(parts[0])
            ip_list.append(parts[1])
    return list(set(ip_list))


def modify_attack_ips(input_file, output_file, common_ips):
    ip_mapping = {f"192.168.100.{i}": random.choice(common_ips) for i in range(10, 110)}
    rwcut_cmd = f"rwcut --fields=sip,dip,sport,dport,stime,etime,bytes,packets --no-title --delimited --input-path={input_file}"

    result = subprocess.run(rwcut_cmd, shell=True, capture_output=True, text=True)
    modified_lines = []

    for line in result.stdout.splitlines():
        parts = line.strip().split('|')
        if len(parts) >= 2:
            parts[0] = ip_mapping.get(parts[0], parts[0])
            parts[1] = ip_mapping.get(parts[1], parts[1])
        modified_lines.append('|'.join(parts))

    # Write modified text to temp, convert back to .rw using rwrec/rwipfix
    text_file = output_file.replace(".rw", ".txt")
    with open(text_file, "w") as f:
        f.write("\n".join(modified_lines))

    # Optional: keep text format, or convert back using rwrec if needed
    # Here we skip reconversion to .rw and just note file is ready

    return text_file  # text-format for now


def duplicate_attack_records(input_file, output_file, num_copies):
    cmd = f"rwcat {' '.join([input_file] * num_copies)} > {output_file}"
    subprocess.run(cmd, shell=True)


def split_attacks_by_port(attack_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    port_files = []

    for attack_name, port in ATTACK_PORTS.items():
        output_file = os.path.join(output_dir, f"{attack_name}.rw")
        cmd = f"rwfilter {attack_file} --dport={port} --pass-dest={output_file}"
        subprocess.run(cmd, shell=True)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            port_files.append(output_file)

    return port_files


def merge_and_sort_multiple(normal_files, attack_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    print(f"📦 Splitting merged attack data into {len(normal_files)} chunks...")
    split_prefix = os.path.join(TEMP_DIR, "attack_chunk_")
    subprocess.run(f"rwsplit --basename={split_prefix} --byte-limit={BYTE_SPLIT_LIMIT} {attack_file}", shell=True)

    attack_chunks = sorted(glob(f"{split_prefix}*.rw"))

    for i, normal_file in enumerate(normal_files):
        chunk_file = attack_chunks[i % len(attack_chunks)] if attack_chunks else None
        output_file = os.path.join(output_dir, f"merged_{i}.rw")

        if chunk_file and os.path.exists(chunk_file):
            temp_merge = os.path.join(TEMP_DIR, f"temp_merge_{i}.rw")
            subprocess.run(f"rwcat {normal_file} {chunk_file} > {temp_merge}", shell=True)
            subprocess.run(f"rwsort --fields=stime {temp_merge} > {output_file}", shell=True)
            os.remove(temp_merge)
        else:
            subprocess.run(f"rwsort --fields=stime {normal_file} > {output_file}", shell=True)


# === MAIN EXECUTION ===
if __name__ == "__main__":
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("🔍 Loading normal dataset files...")
    normal_files = get_all_silk_files(NORMAL_DATASET_DIR)

    if not normal_files:
        print("❌ No normal dataset files found. Check your folder path.")
        exit(1)

    print("📊 Extracting common IPs from normal dataset...")
    common_ips = []
    for f in normal_files:
        common_ips += extract_common_ips(f)
    common_ips = list(set(common_ips))

    processed_attack_files = []

    for file_idx, attack_file in enumerate(ATTACK_DATASET_FILES):
        print(f"\n🔨 Splitting attack file: {attack_file}")
        attack_type_files = split_attacks_by_port(attack_file, os.path.join(TEMP_DIR, f"split_{file_idx}"))

        for port_file in attack_type_files:
            base = os.path.splitext(os.path.basename(port_file))[0]
            ip_mod_file = os.path.join(TEMP_DIR, f"ip_mod_{base}.rw")
            duplicated_file = os.path.join(TEMP_DIR, f"dup_{base}.rw")

            ip_text_file = modify_attack_ips(port_file, ip_mod_file, common_ips)

            # NOTE: We are working with text-format files from rwcut; skip if binary needed
            # To keep it consistent, we just skip binary-only tools like rwcat for now
            processed_attack_files.append(ip_text_file)

    print("\n📥 Merging all processed attack text files into one...")
    merged_attack_file = "merged_attacks.txt"
    with open(merged_attack_file, "w") as outfile:
        for f in processed_attack_files:
            with open(f) as infile:
                outfile.write(infile.read() + "\n")

    print(f"\n✅ Done! Merged attack flows saved as: {merged_attack_file}")
    print("Note: Final output is in text format. You can convert to .rw if needed using rwrec.")
