import numpy as np
import os
import datetime
from silk import *
from Sliding_Window import Sliding_Window 

def extract_silk_features(list_of_silk_files, output_dir="data/Classifiers", sliding_window_times=[1200, 6000, 12000]):
    """
    Extracts network flow features from SiLK files and saves them in .npy format.

    Parameters:
        list_of_silk_files (list): List of SiLK file paths.
        output_dir (str): Directory to save extracted features.
        sliding_window_times (list): Time windows for entropy-based calculations.
    
    Returns:
        None (Saves features in .npy files)
    """

    # Initialize sliding windows for entropy-based features
    sliding_window = Sliding_Window(sliding_window_times[0], sliding_window_times[1], sliding_window_times[2], False)

    # Storage for feature sets
    fields_features = []  # For Fields-based classifiers (Random Forest)
    entropy_features = []  # For Entropy-based classifiers
    combined_features = []  # For classifiers using both fields and entropy

    for file in list_of_silk_files:
        print(f"Processing SiLK file: {file}")

        # Open the SiLK flow file
        infile = silkfile_open(file, READ)

        for rec in infile:
            sliding_window_values = sliding_window.addNewRec(rec)  # Update sliding window

            # Extract Fields-Based Features (Basic NetFlow fields)
            field_data = [
                int(rec.sip), int(rec.dip), rec.sport, rec.dport, rec.protocol, rec.packets, rec.bytes, int(rec.nhip),
                int(rec.tcpflags.fin), int(rec.tcpflags.syn), int(rec.tcpflags.rst), int(rec.tcpflags.psh), int(rec.tcpflags.ack),
                int(rec.tcpflags.urg), int(rec.tcpflags.ece), int(rec.tcpflags.cwr),
                rec.duration / datetime.timedelta(milliseconds=1),  # Normalize duration
                rec.sensor_id  # Attack label (assumed)
            ]

            # Extract Entropy-Based Features (Requires sliding window)
            entropy_data, combined_data = extract_entropy_features(sliding_window_values)

            # Store extracted features
            fields_features.append(field_data)
            if entropy_data:
                entropy_features.append(entropy_data)
            if combined_data:
                combined_features.append(combined_data)

        infile.close()

    # Convert lists to numpy arrays
    fields_features = np.array(fields_features, dtype=np.float32)
    entropy_features = np.array(entropy_features, dtype=object)
    combined_features = np.array(combined_features, dtype=np.float32)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save extracted features
    np.save(os.path.join(output_dir, "fields.npy"), fields_features)
    np.save(os.path.join(output_dir, "entropy.npy"), entropy_features)
    np.save(os.path.join(output_dir, "combined.npy"), combined_features)

    print(f"Feature extraction complete. Data saved in {output_dir}/")

def extract_entropy_features(sliding_window_values):
    """
    Processes entropy-based features from a sliding window.

    Parameters:
        sliding_window_values (list): Values from the sliding window.

    Returns:
        tuple: (entropy-based features, combined features)
    """
    entropy_data = []
    combined_data = []

    if len(sliding_window_values) > 0:
        for x in range(0, len(sliding_window_values)):
            if sliding_window_values[x] == "window":
                if x + 1 >= len(sliding_window_values):
                    continue
                elif sliding_window_values[x + 1] == "window" or len(sliding_window_values[x + 1]) == 0:
                    continue
                else:
                    entropy_data.append(sliding_window_values[x + 1][0][18:])  # Extract entropy values

        for temp in sliding_window_values:
            if len(temp) != 0 and temp != "window":
                for r in temp:
                    combined_data.append(r)  # Append combined feature set

    return entropy_data, combined_data