import subprocess
import pandas as pd
import os
from glob import glob

# === CONFIG ===
input_folder = "final_dataset_01"  # Folder with .rw files
output_csv_file = "training_dataset.csv"
temp_folder = "temp_csv_parts"

# Ports mapped to attack labels
attack_port_map = {
    6001: "slow_read",
    6002: "rudy",
    6003: "ping_flood",
    6004: "blacknurse",
    6005: "xmas_scan",
    6006: "udp_flood",
    6007: "syn_flood",
    6008: "slowloris"
}

# Fields to extract from rw file
fields = "sip,dip,sport,dport,stime,etime,proto,packets,bytes"


def extract_folder_to_csv(folder, temp_output_dir):
    os.makedirs(temp_output_dir, exist_ok=True)
    rw_files = glob(os.path.join(folder, "*"))

    temp_csvs = []
    for i, rw_file in enumerate(rw_files):
        temp_csv = os.path.join(temp_output_dir, f"part_{i}.csv")
        cmd = [
            "rwcut",
            "--fields", fields,
            "--delimited",
            "--no-title",
            "--input-path", rw_file
        ]
        print(f"Extracting: {rw_file}")
        with open(temp_csv, "w") as f:
            subprocess.run(cmd, stdout=f)
        temp_csvs.append(temp_csv)

    return temp_csvs


def label_and_merge_csvs(csv_files, final_csv):
    print("Merging and labeling data...")
    columns = ["sip", "dip", "sport", "dport", "stime", "etime", "proto", "packets", "bytes"]
    dfs = [pd.read_csv(f, names=columns) for f in csv_files]
    full_df = pd.concat(dfs, ignore_index=True)

    full_df["label"] = full_df["dport"].map(attack_port_map)
    full_df["label"] = full_df["label"].fillna("normal")

    full_df.to_csv(final_csv, index=False)
    print(f"Labeled training dataset saved: {final_csv}")


# === Main ===
if __name__ == "__main__":
    temp_csvs = extract_folder_to_csv(input_folder, temp_folder)
    label_and_merge_csvs(temp_csvs, output_csv_file)

    # cleanup temp files
    for f in temp_csvs:
        os.remove(f)
    os.rmdir(temp_folder)
