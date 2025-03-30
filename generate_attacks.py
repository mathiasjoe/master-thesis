import os
import random
from pathlib import Path

# Victim IP
VICTIM_IP = "192.168.50.10"

# Attack ports
ATTACK_PORTS = {
    "slow_read": 6001,
    "rudy": 6002,
    "ping_flood": 6003,
    "blacknurse": 6004,
    "xmas_scan": 6005,
    "udp_flood": 6006,
    "syn_flood": 6007,
    "slowloris": 6008,
}

# Protocols for each attack
ATTACK_PROTOCOLS = {
    "slow_read": 6,
    "rudy": 6,
    "ping_flood": 1,
    "blacknurse": 1,
    "xmas_scan": 6,
    "udp_flood": 17,
    "syn_flood": 6,
    "slowloris": 6,
}

# Create a new unique output folder
def create_output_folder(base_name="attacks_run"):
    i = 1
    while Path(f"{base_name}_{i}").exists():
        i += 1
    folder_path = Path(f"{base_name}_{i}")
    folder_path.mkdir()
    return folder_path

# Generate a synthetic attack flow
def generate_attack_flow(attack_name, port, proto, run_id, output_dir):
    output_file = output_dir / f"{attack_name}_run{run_id}.rw"
    flows = random.randint(1000, 5000)
    bytes_per_flow = random.randint(40, 150)
    duration = random.randint(30, 90)

    cmd = (
        f"rwgenerate "
        f"--sip-range=192.168.40.1-192.168.40.200 "
        f"--dip={VICTIM_IP} "
        f"--sport=1024-65535 "
        f"--dport={port} "
        f"--proto={proto} "
        f"--flows={flows} "
        f"--bytes={bytes_per_flow} "
        f"--packets=1 "
        f"--duration={duration} "
        f"--output-path={output_file}"
    )

    print(f"[+] Generating: {attack_name} (Run {run_id}) -> {output_file}")
    os.system(cmd)

# Main logic
def main():
    output_dir = create_output_folder()
    print(f"\n📁 Output folder created: {output_dir}\n")

    for attack, port in ATTACK_PORTS.items():
        proto = ATTACK_PROTOCOLS[attack]
        for run in range(1, 3):  # 2 runs per attack
            generate_attack_flow(attack, port, proto, run, output_dir)

    print(f"\n✅ All .rw files saved in: {output_dir}")

if __name__ == "__main__":
    main()
