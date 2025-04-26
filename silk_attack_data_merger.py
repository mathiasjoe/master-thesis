import subprocess
import random
import os
from glob import glob

# === Configuration ===
NORMAL_DATASET_DIR = "01"
ATTACK_DATASET_FILES = [
    "03/in-S0_20250401.15",
    "03/in-S0_20250401.16"
]
OUTPUT_FOLDER = "final_dataset_chunks"
TEMP_DIR = "temp"
BYTE_SPLIT_LIMIT = 512000  # 500 KB per split chunk

# === Attack Labels – Destination ports per attack ===
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
    return sorted([f for f in glob(os.path.join(directory, "*")) if os.path.isfile(f)])


def extract_common_ips(dataset_files):
    print(" Extracting common IPs from normal dataset...")
    all_ips = set()

    for f in dataset_files:
        cmd = f"rwcut {f} --fields=sip,dip --no-title --delimited"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        for line in result.stdout.splitlines():
            parts = line.strip().split('|')
            if len(parts) == 2:
                all_ips.add(parts[0].strip())
                all_ips.add(parts[1].strip())

    return list(all_ips)


def modify_attack_ips(input_file, output_text_file, common_ips):
    print(f" Rewriting IPs in: {input_file}")
    ip_map = {}

    rwcut_cmd = f"rwcut --fields=sip,dip,sport,dport,stime,etime,bytes,packets --no-title --delimited --input-path={input_file}"
    result = subprocess.run(rwcut_cmd, shell=True, capture_output=True, text=True)

    modified_lines = []
    for line in result.stdout.splitlines():
        parts = line.strip().split('|')
        if len(parts) < 8:
            continue
        # Replace source and destination IPs
        for i in [0, 1]:  # sip and dip
            ip = parts[i]
            if ip not in ip_map:
                ip_map[ip] = random.choice(common_ips)
            parts[i] = ip_map[ip]
        modified_lines.append('|'.join(parts))

    with open(output_text_file, "w") as f:
        f.write("\n".join(modified_lines))

    return output_text_file


def split_attacks_by_port(attack_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    port_files = []

    for attack_name, port in ATTACK_PORTS.items():
        output_file = os.path.join(output_dir, f"{attack_name}.rw")
        cmd = f"rwfilter --input-path={attack_file} --dport={port} --pass-destination={output_file}"
        subprocess.run(cmd, shell=True)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            port_files.append(output_file)

    return port_files


def merge_and_sort_multiple(normal_files, attack_rw_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    print(f" Splitting attack data using rwsplit...")
    split_prefix = os.path.join(TEMP_DIR, "attack_chunk_")
    subprocess.run(f"rwsplit --basename={split_prefix} --byte-limit={BYTE_SPLIT_LIMIT} {attack_rw_file}", shell=True)

    attack_chunks = sorted(glob(f"{split_prefix}*.rw"))

    for i, normal_file in enumerate(normal_files):
        chunk_file = attack_chunks[i % len(attack_chunks)] if attack_chunks else None
        output_file = os.path.join(output_dir, f"merged_{i:02d}.rw")

        if chunk_file:
            temp_merge = os.path.join(TEMP_DIR, f"temp_merge_{i}.rw")
            subprocess.run(f"rwcat {normal_file} {chunk_file} > {temp_merge}", shell=True)
            subprocess.run(f"rwsort --fields=stime {temp_merge} > {output_file}", shell=True)
            os.remove(temp_merge)
        else:
            subprocess.run(f"rwsort --fields=stime {normal_file} > {output_file}", shell=True)


# MAIN SCRIPT 
if __name__ == "__main__":
    os.makedirs(TEMP_DIR, exist_ok=True)

    print(" Gathering normal dataset files...")
    normal_files = get_all_silk_files(NORMAL_DATASET_DIR)
    if not normal_files:
        print(" No normal dataset files found in folder '01/'. Exiting.")
        exit(1)

    common_ips = extract_common_ips(normal_files)
    if not common_ips:
        print(" Failed to extract IPs from normal data. Exiting.")
        exit(1)

    processed_text_files = []

    for attack_file in ATTACK_DATASET_FILES:
        print(f"\n Processing attack file: {attack_file}")
        port_files = split_attacks_by_port(attack_file, os.path.join(TEMP_DIR, "split_attacks"))

        for port_file in port_files:
            attack_name = os.path.splitext(os.path.basename(port_file))[0]
            text_output = os.path.join(TEMP_DIR, f"{attack_name}.txt")
            processed_file = modify_attack_ips(port_file, text_output, common_ips)
            processed_text_files.append(processed_file)

    if not processed_text_files:
        print(" No usable attack files after IP modification. Exiting.")
        exit(1)

    print("\n Merging all modified attack flows into one text file...")
    merged_txt = os.path.join(TEMP_DIR, "all_attacks.txt")
    with open(merged_txt, "w") as outfile:
        for txt_file in processed_text_files:
            with open(txt_file) as infile:
                outfile.write(infile.read() + "\n")

    print(" Converting merged text attack flows to binary .rw format...")
    merged_rw = os.path.join(TEMP_DIR, "merged_attacks.rw")
    subprocess.run(
        f"rwload --fields=sip,dip,sport,dport,stime,etime,bytes,packets "
        f"--input-path={merged_txt} --output-path={merged_rw}",
        shell=True
    )

    print("\n Merging attack flows with normal dataset...")
    merge_and_sort_multiple(normal_files, merged_rw, OUTPUT_FOLDER)

    print(f"\n✅ DONE! Merged dataset saved in: {OUTPUT_FOLDER}/")
