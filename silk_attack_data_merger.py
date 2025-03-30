import subprocess
import random
import datetime
import os
from glob import glob

# Configuration
NORMAL_DATASET_DIRS = ["normal_folder1", "normal_folder2"]  # Update with your folder names
ATTACK_DATASET = "attacks.rw"
OUTPUT_FOLDER = "final_dataset_chunks"
NUM_COPIES = 1
TIME_SHIFT_RANGE = (60, 600)

# Get all .rw files from the normal traffic folders
def get_all_normal_files(directories):
    rw_files = []
    for d in directories:
        rw_files.extend(glob(os.path.join(d, "*.rw")))
    return rw_files

# Extract common IPs from a normal .rw file
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

# Modify timestamps in attack records using time shift
def modify_attack_timestamps(input_file, output_file, time_shift):
    cmd = f"rwset --time-after=now-{time_shift}s {input_file} | rwcut > {output_file}"
    subprocess.run(cmd, shell=True)

# Modify timestamps in attack records using timestamps from normal dataset
def match_attack_timestamps_with_normal(input_file, output_file, normal_file):
    cmd_extract_times = f"rwcut --fields=stime {normal_file}"
    result = subprocess.run(cmd_extract_times, shell=True, capture_output=True, text=True)
    normal_timestamps = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    if not normal_timestamps:
        print("No timestamps found in normal dataset. Using random shift instead.")
        return modify_attack_timestamps(input_file, output_file, random.randint(*TIME_SHIFT_RANGE))

    selected_timestamp = random.choice(normal_timestamps)
    cmd_modify_time = f"rwset --time-after={selected_timestamp} {input_file} | rwcut > {output_file}"
    subprocess.run(cmd_modify_time, shell=True)

# Replace attack IPs with common IPs from normal dataset
def modify_attack_ips(input_file, output_file, common_ips):
    ip_mapping = {f"192.168.100.{i}": random.choice(common_ips) for i in range(10, 110)}

    cmd = f"rwcut --fields=sip,dip,sport,dport,stime,etime,bytes,packets {input_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    modified_lines = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            parts[0] = ip_mapping.get(parts[0], parts[0])
            parts[1] = ip_mapping.get(parts[1], parts[1])
        modified_lines.append("\t".join(parts))

    with open(output_file, "w") as f:
        f.write("\n".join(modified_lines))

# Duplicate attack flows
def duplicate_attack_records(input_file, output_file, num_copies):
    cmd = f"rwcat {input_file} " + " ".join([input_file] * num_copies) + f" > {output_file}"
    subprocess.run(cmd, shell=True)

# Merge each normal file with a chunk of attack traffic
def merge_and_sort_multiple(normal_files, attack_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    print(f"Splitting attack dataset into {len(normal_files)} chunks...")
    # Split attack file using rwsplit to create chunks for each normal file
    split_prefix = "attack_chunk_"
    subprocess.run(f"rwsplit --basename={split_prefix} --byte-limit=500K {attack_file}", shell=True)

    # Get all generated attack chunks
    attack_chunks = sorted(glob(f"{split_prefix}*.rw"))

    for i, normal_file in enumerate(normal_files):
        chunk_file = attack_chunks[i % len(attack_chunks)] if attack_chunks else None
        output_file = os.path.join(output_dir, f"merged_{i}.rw")

        if chunk_file and os.path.exists(chunk_file):
            temp_merge = f"temp_merge_{i}.rw"
            subprocess.run(f"rwcat {normal_file} {chunk_file} > {temp_merge}", shell=True)
            subprocess.run(f"rwsort --fields=stime {temp_merge} > {output_file}", shell=True)
            os.remove(temp_merge)
        else:
            # Just sort normal file if no chunk is left
            subprocess.run(f"rwsort --fields=stime {normal_file} > {output_file}", shell=True)

# === Main Execution ===
if __name__ == "__main__":
    print("Gathering normal dataset files...")
    normal_files = get_all_normal_files(NORMAL_DATASET_DIRS)

    if not normal_files:
        print("No normal dataset files found. Check your folder paths.")
        exit(1)

    print("Extracting common IPs from all normal files...")
    common_ips = []
    for f in normal_files:
        common_ips += extract_common_ips(f)
    common_ips = list(set(common_ips))

    print("Modifying timestamps of attack dataset...")
    modified_attacks = "modified_attacks.rw"
    random_normal = random.choice(normal_files)
    match_attack_timestamps_with_normal(ATTACK_DATASET, modified_attacks, random_normal)

    print("Modifying IPs in attack flows...")
    ip_modified_attacks = "ip_modified_attacks.rw"
    modify_attack_ips(modified_attacks, ip_modified_attacks, common_ips)

    print("Duplicating attack records...")
    duplicated_attacks = "duplicated_attacks.rw"
    duplicate_attack_records(ip_modified_attacks, duplicated_attacks, NUM_COPIES)

    print("Merging attack traffic into multiple normal files...")
    merge_and_sort_multiple(normal_files, duplicated_attacks, OUTPUT_FOLDER)

    print(f"\n✅ Attack injection completed! Final dataset is saved in '{OUTPUT_FOLDER}' folder.")
