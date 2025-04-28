# rw_to_csv_converter.py

import os
import subprocess

# === CONFIG ===
INPUT_FOLDER = "final_dataset_01"        # Folder where your .rw files are
OUTPUT_FOLDER = "attack_data"    # Where CSVs will be saved
FIELDS = "sip,dip,sport,dport,proto,packets,bytes,stime,etime"  # Fields to extract

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def convert_rw_to_csv(rw_file, csv_file):
    try:
        with open(csv_file, "w") as f:
            subprocess.run([
                "rwcut",
                "--fields", FIELDS,
                "--delimited",
                "--no-title",
                rw_file
            ], stdout=f, check=True)
        print(f" Converted: {rw_file} -> {csv_file}")
    except subprocess.CalledProcessError:
        print(f" Error converting: {rw_file}")

def batch_convert(input_folder, output_folder):
    files = [f for f in os.listdir(input_folder) if f.endswith(".rw")]

    for rw_file in files:
        input_path = os.path.join(input_folder, rw_file)
        output_path = os.path.join(output_folder, rw_file.replace(".rw", ".csv"))
        convert_rw_to_csv(input_path, output_path)

if __name__ == "__main__":
    print(" Converting all .rw files to CSV...")
    batch_convert(INPUT_FOLDER, OUTPUT_FOLDER)
    print("\n All conversions complete!")
