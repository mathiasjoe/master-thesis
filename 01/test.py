import subprocess
import glob
import os

# Define paths
rwfilter_path = "/usr/local/bin/rwfilter"  # Correct path to rwfilter
rwcut_path = "/usr/local/bin/rwcut"  # Ensure rwcut is also in the correct location
silk_conf_path = "SILK_testing/silk.conf"  # Path to silk.conf
input_dir = "SILK_testing/01/"  # Path to SiLK data files
filtered_output = "filtered_in.rw"
csv_output = "netflow_data.csv"

# Ensure silk.conf exists
if not os.path.exists(silk_conf_path):
    print(f"Error: silk.conf not found at {silk_conf_path}")
    exit()

# Get all SiLK files in the directory
input_files = glob.glob(os.path.join(input_dir, "*"))
if not input_files:
    print("Error: No SiLK files found in the directory!")
    exit()

# Convert list of files to space-separated string
input_files_str = " ".join(input_files)

# Run rwfilter to extract incoming traffic with the correct path
print("Running rwfilter...")
filter_command = f"{rwfilter_path} --site-config={silk_conf_path} --type=in --pass={filtered_output} {input_files_str}"
subprocess.run(filter_command, shell=True, check=True)

# Convert filtered data to CSV with the correct rwcut path
print("Converting to CSV...")
convert_command = f"{rwcut_path} --fields=sip,dip,sport,dport,proto,bytes,packets {filtered_output} > {csv_output}"
subprocess.run(convert_command, shell=True, check=True)

print(f"Extraction complete! Data saved to {csv_output}")
