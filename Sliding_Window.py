import datetime
import numpy as np
import copy

class Sliding_Window:
    def __init__(self, sliding_window_interval, aggregate_window_duration, comparison_window_interval):
        """
        Initializes a sliding window for processing network flow data.
        
        :param sliding_window_interval: How often the window updates (e.g., 1200 seconds).
        :param aggregate_window_duration: Duration of the aggregate window (e.g., 6000 seconds).
        :param comparison_window_interval: Time span for historical comparison (e.g., 12000 seconds).
        """
        self.sliding_window_interval = sliding_window_interval
        self.aggregate_window_duration = aggregate_window_duration
        self.comparison_window_interval = comparison_window_interval
        
        # Stores past window data for anomaly detection
        self.comparison_window = {"values": [], 
                                  "interval": datetime.timedelta(seconds=comparison_window_interval)}
        
        # Active aggregation window
        self.aggregate_window = {"currentTime": 0, "earliestTime": 0, "flows": []}

        # Features to be extracted
        self.feature_values = {
            "entropySip": 0, "entropyDip": 0, "entropyPacketsize": 0,
            "totalPackets": 0, "totalBytes": 0, "SYN_Flood": 0,
            "ICMP_Unreachable": 0, "uniqueIPs": 0
        }

    def addNewFlow(self, flow):
        """
        Adds a new network flow to the sliding window.

        :param flow: A dictionary representing a network flow.
        """
        if self.aggregate_window["earliestTime"] == 0:
            self.aggregate_window["earliestTime"] = flow["timestamp"]

        self.aggregate_window["currentTime"] = flow["timestamp"]

        # Check if window has exceeded its interval and needs to shift
        if self.checkIfPastSlidingWindow():
            self.shiftWindow()

        # Add flow to the current window
        self.aggregate_window["flows"].append(flow)

    def checkIfPastSlidingWindow(self):
        """
        Determines whether the sliding window has exceeded its interval.

        :return: True if the window needs to shift, False otherwise.
        """
        elapsed_time = self.aggregate_window["currentTime"] - self.aggregate_window["earliestTime"]
        return elapsed_time >= datetime.timedelta(seconds=self.sliding_window_interval)

    def shiftWindow(self):
        """
        Moves the sliding window forward, calculates entropy & other features.
        """
        # Compute statistical and entropy-based features
        self.computeFeatures()

        # Move window forward by discarding the oldest flows
        self.aggregate_window["earliestTime"] = self.aggregate_window["currentTime"]
        self.aggregate_window["flows"] = []

    def computeFeatures(self):
        """
        Computes statistical and entropy-based features for the current sliding window.
        """
        flows = self.aggregate_window["flows"]

        # Track unique IPs, packet sizes, bytes, and SYN floods
        source_ips = {}
        destination_ips = {}
        packet_sizes = {}
        syn_packets = 0
        icmp_unreachable = 0
        total_bytes = 0
        total_packets = 0

        for flow in flows:
            sip = flow["source_ip"]
            dip = flow["destination_ip"]
            size = flow["packet_size"]
            packets = flow["packet_count"]
            total_packets += packets
            total_bytes += flow["byte_count"]

            # Track unique source IPs
            if sip in source_ips:
                source_ips[sip] += packets
            else:
                source_ips[sip] = packets

            # Track unique destination IPs
            if dip in destination_ips:
                destination_ips[dip] += packets
            else:
                destination_ips[dip] = packets

            # Track packet sizes
            if size in packet_sizes:
                packet_sizes[size] += packets
            else:
                packet_sizes[size] = packets

            # Count SYN packets (DDoS detection)
            if flow["tcp_flags_syn"]:
                syn_packets += packets

            # Count ICMP unreachable messages (Scan detection)
            if flow["icmp_type"] == 3:
                icmp_unreachable += packets

        # Compute entropy values
        entropy_sip = self.calculateEntropy(source_ips, total_packets)
        entropy_dip = self.calculateEntropy(destination_ips, total_packets)
        entropy_packet_size = self.calculateEntropy(packet_sizes, total_packets)

        # Store computed features
        self.feature_values.update({
            "entropySip": entropy_sip,
            "entropyDip": entropy_dip,
            "entropyPacketsize": entropy_packet_size,
            "totalPackets": total_packets,
            "totalBytes": total_bytes,
            "SYN_Flood": syn_packets,
            "ICMP_Unreachable": icmp_unreachable,
            "uniqueIPs": len(source_ips)
        })

        # Store values for historical comparison
        self.comparison_window["values"].append(copy.deepcopy(self.feature_values))

    def calculateEntropy(self, distribution, total):
        """
        Computes entropy for a given feature distribution.

        :param distribution: Dictionary of feature counts.
        :param total: Total number of packets or flows.
        :return: Entropy value.
        """
        if total == 0:
            return 0
        probabilities = [count / total for count in distribution.values()]
        return -sum(p * np.log2(p) for p in probabilities if p > 0)

    def detectAnomalies(self):
        """
        Compares current feature values against past values to detect anomalies.
        """
        if len(self.comparison_window["values"]) < 2:
            return "No sufficient data for anomaly detection."

        latest = self.comparison_window["values"][-1]
        previous_avg = {key: np.mean([entry[key] for entry in self.comparison_window["values"][:-1]]) 
                        for key in latest.keys()}

        anomalies = []
        for key in latest.keys():
            deviation = abs(latest[key] - previous_avg[key])
            if deviation > (previous_avg[key] * 0.3):  # 30% deviation threshold
                anomalies.append(f"Anomaly detected in {key} (Change: {deviation:.2f})")

        return anomalies if anomalies else "No anomalies detected."

    def getCurrentFeatureValues(self):
        """
        Returns the latest computed feature values.
        """
        return self.feature_values