import subprocess
import random
import datetime

# Configuration
ATTACK_DATASET = "attacks.rw"  # The attack dataset
NORMAL_DATASET = "normal_traffic.rw"  # The normal dataset
OUTPUT_DATASET = "final_dataset.rw"  # The final merged dataset
NUM_COPIES = 1  # Number of times to replicate attack traffic
TIME_SHIFT_RANGE = (60, 600)  # Time shift in seconds 

# Extract common IPs from the normal dataset
def extract_common_ips(dataset):
    """Extracts frequently occurring source and destination IPs from a SiLK dataset."""
    cmd = f"rwstats --fields=sip,dip --count=50 {dataset}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    ip_list = []
    for line in result.stdout.splitlines()[1:]:  
        parts = line.split()
        if len(parts) >= 2:
            ip_list.append(parts[0])  # Add source IP
            ip_list.append(parts[1])  # Add destination IP

    return list(set(ip_list))  # Remove duplicates

# Modify timestamps in attack records
def modify_attack_timestamps(input_file, output_file, time_shift):
    """Shifts the timestamp of attack flows by a given offset."""
    cmd = f"rwset --time-after=now-{time_shift}s {input_file} | rwcut > {output_file}"
    subprocess.run(cmd, shell=True)

# Modify attack IPs to match common traffic patterns
def modify_attack_ips(input_file, output_file, common_ips):
    """Replaces attack source and destination IPs with IPs found in normal traffic."""
    ip_mapping = {f"192.168.100.{i}": random.choice(common_ips) for i in range(10, 110)}  # Fake to real mapping
    
    # Process each record and replace IPs
    cmd = f"rwcut --fields=sip,dip,sport,dport,stime,etime,bytes,packets {input_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    modified_lines = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            parts[0] = ip_mapping.get(parts[0], parts[0])  # Source IP
            parts[1] = ip_mapping.get(parts[1], parts[1])  # Destination IP
        modified_lines.append("\t".join(parts))

    
    with open(output_file, "w") as f:
        f.write("\n".join(modified_lines))

# Duplicate attack records
def duplicate_attack_records(input_file, output_file, num_copies):
    cmd = f"rwcat {input_file} " + " ".join([input_file] * num_copies) + f" > {output_file}"
    subprocess.run(cmd, shell=True)

# Merge and Sort Dataset
def merge_and_sort_datasets(normal_file, attack_file, output_file):
    """Merges normal and attack datasets, then sorts them by timestamp."""
    merged_file = "merged_unsorted.rw"
    
    # Merge both datasets
    cmd_merge = f"rwcat {normal_file} {attack_file} > {merged_file}"
    subprocess.run(cmd_merge, shell=True)

    # Sort dataset by timestamp
    cmd_sort = f"rwsort --fields=stime {merged_file} > {output_file}"
    subprocess.run(cmd_sort, shell=True)

# **Main Execution**
if __name__ == "__main__":
    print("Extracting common IPs from normal dataset")
    common_ips = extract_common_ips(NORMAL_DATASET)

    print("Modifying timestamps of attack dataset")
    modified_attacks = "modified_attacks.rw"
    time_shift = random.randint(*TIME_SHIFT_RANGE)
    modify_attack_timestamps(ATTACK_DATASET, modified_attacks, time_shift)

    print("Modifying attack IP addresses")
    ip_modified_attacks = "ip_modified_attacks.rw"
    modify_attack_ips(modified_attacks, ip_modified_attacks, common_ips)

    print("Duplicating attack records")
    duplicated_attacks = "duplicated_attacks.rw"
    duplicate_attack_records(ip_modified_attacks, duplicated_attacks, NUM_COPIES)

    print("Merging attack dataset with normal dataset")
    merge_and_sort_datasets(NORMAL_DATASET, duplicated_attacks, OUTPUT_DATASET)

    print(f" Attack injection completed! Final dataset saved as {OUTPUT_DATASET}")
