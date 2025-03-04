import subprocess
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO if you want less verbose output
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_silk_records(file_path):
    """
    Runs rwcut on the given Silk file and parses the output.
    Skips header lines that start with '#' or that contain non-numeric values
    in the bytes/packets fields.
    """
    logging.info(f"Starting to parse file: {file_path}")
    command = f"rwcut --fields=sip,dip,sport,dport,pro,bytes,packets,stime,etime,dur {file_path}"
    logging.debug(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error(f"Error reading Silk file: {result.stderr}")
        raise Exception(f"Error reading Silk file: {result.stderr}")
    
    records = []
    for line in result.stdout.splitlines():
        logging.debug(f"Processing line: {line}")
        # Skip lines starting with '#' (comment or meta information)
        if line.startswith("#"):
            logging.debug("Skipping comment/header line.")
            continue
        
        # Split the line into fields using '|' as the delimiter and strip whitespace.
        fields = [field.strip() for field in line.split('|')]
        
        # Check if this is a header line by testing if the expected numeric fields contain non-numeric values.
        if len(fields) < 8:
            logging.warning("Line does not have enough fields; skipping line.")
            continue
        if fields[5].lower() == "bytes" or fields[6].lower() == "packets":
            logging.debug("Skipping header line with column names.")
            continue
        
        try:
            record = {
                'sip': fields[0],
                'dip': fields[1],
                'sport': fields[2],
                'dport': fields[3],
                'pro': fields[4],
                'bytes': int(fields[5]),
                'packets': int(fields[6]),
                'stime': fields[7]  # Using stime for aggregation
            }
            records.append(record)
        except Exception as e:
            logging.error(f"Error processing line: {line}\nException: {e}")
    
    logging.info(f"Finished parsing file: {file_path} with {len(records)} records.")
    return records

def process_records(records, window='hour'):
    """
    Aggregates records into time windows.
    The default aggregation is by hour (using the first 13 characters of stime).
    """
    logging.info("Starting aggregation of records...")
    aggregated_data = {}
    for record in records:
        if 'stime' not in record:
            logging.warning("Record without stime encountered; skipping record.")
            continue

        if window == 'hour':
            time_window = record['stime'][:13]  # e.g., "20110101.00"
        elif window == 'minute':
            time_window = record['stime'][:16]
        else:
            time_window = record['stime']

        if time_window not in aggregated_data:
            aggregated_data[time_window] = {
                'total_packets': 0,
                'total_bytes': 0,
                'flow_count': 0
            }
        aggregated_data[time_window]['total_packets'] += record['packets']
        aggregated_data[time_window]['total_bytes'] += record['bytes']
        aggregated_data[time_window]['flow_count'] += 1

    logging.info("Finished aggregating records.")
    return aggregated_data

def label_data(aggregated_data, threshold=1000):
    """
    Labels each aggregated time window based on a threshold.
    If the flow_count exceeds the threshold, the label is set to 1 (indicating potential DDoS),
    otherwise it is 0.
    for time_window, data in aggregated_data.items():
        label = 1 if data['flow_count'] > threshold else 0
    """
    logging.info("Starting labeling of aggregated data...")
    training_data = []
    for time_window, data in aggregated_data.items():
        # Label is 0 because we assume all data is benign.
        label = 0
        record = {
            'time_window': time_window,
            'total_packets': data['total_packets'],
            'total_bytes': data['total_bytes'],
            'flow_count': data['flow_count'],
            'label': label
        }
        training_data.append(record)
    logging.info("Finished labeling data.")
    return training_data

def process_folder(folder_path):
    """
    Processes all files in the specified folder and returns all parsed records.
    """
    logging.info(f"Processing folder: {folder_path}")
    all_records = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        logging.info(f"Processing file: {file_path}")
        try:
            records = parse_silk_records(file_path)
            logging.info(f"Parsed {len(records)} records from {file_path}")
            all_records.extend(records)
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
    logging.info(f"Total records parsed from folder: {len(all_records)}")
    return all_records

def main():
    folder_path = '01'
    if not os.path.exists(folder_path):
        logging.error(f"Folder not found: {folder_path}")
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    logging.info("Starting to process folder...")
    records = process_folder(folder_path)
    logging.info(f"Total records parsed: {len(records)}")
    
    logging.info("Aggregating records...")
    aggregated_data = process_records(records, window='hour')
    
    logging.info("Labeling aggregated data...")
    training_data = label_data(aggregated_data, threshold=1000)
    
    # Now training_data contains aggregated features and a label per time window.
    for record in training_data:
        logging.info(f"Training Data Record: {record}")

if __name__ == "__main__":
    main()
