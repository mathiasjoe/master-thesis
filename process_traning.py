import subprocess
import pandas as pd
import os
from glob import glob

# === CONFIG ===
input_folder = "final_dataset_01"      # Folder with .rw files
output_folder = "training_data"   # Where labeled CSVs will go
os.makedirs(output_folder, exist_ok=True)

# Port to label mapping
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

# Fields to extract
fields = "sip,dip,sport,dport,stime,etime,proto,packets,bytes"

# Max rows per output CSV 
max_rows_per_csv = 100_000


def convert_and_label(input_rw, output_prefix, part_num):
    temp_csv = f"{output_prefix}_raw.csv"
    out_base = f"{output_prefix}_part"

    # 1. Convert .rw to CSV using rwcut
    with open(temp_csv, "w") as f:
        subprocess.run([
            "rwcut",
            "--fields", fields,
            "--no-title",
            "--delimited=,",
            input_rw
        ], stdout=f)

    # 2. Read and label
    cols = ["sip", "dip", "sport", "dport", "stime", "etime", "proto", "packets", "bytes"]
    df = pd.read_csv(temp_csv, names=cols)
    df["label"] = df["dport"].map(attack_port_map).fillna("normal")

    # 3. Split if necessary
    if len(df) <= max_rows_per_csv:
        out_file = f"{out_base}_{part_num}.csv"
        df.to_csv(out_file, index=False)
    else:
        for i, start in enumerate(range(0, len(df), max_rows_per_csv)):
            part_df = df.iloc[start:start + max_rows_per_csv]
            part_df.to_csv(f"{out_base}_{part_num}_{i}.csv", index=False)

    os.remove(temp_csv)


# === Main ===
if __name__ == "__main__":
    rw_files = sorted(glob(os.path.join(input_folder, "*")))
    for idx, rw_file in enumerate(rw_files):
        file_name = os.path.basename(rw_file).replace(".", "_")
        output_prefix = os.path.join(output_folder, file_name)
        print(f"📄 Processing {rw_file} -> {output_prefix}")
        convert_and_label(rw_file, output_prefix, idx)

    print(f"\n All done! Labeled CSVs saved in '{output_folder}/'")
