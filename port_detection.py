import os
import glob
import pandas as pd
import numpy as np
from collections import defaultdict
from gensim.models import Word2Vec
import joblib
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CONFIG ===
ATTACK_DATA_FOLDER = "attack_data"  # Folder with test data (no labels)
OUTPUT_FOLDER = "results_attack_eval"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
NUM_THREADS = 20

# === Load Models ===
print(" Loading models...")

rf_model = joblib.load("rf_model.pkl")
rf_label_encoder = joblib.load("rf_label_encoder.pkl")

nb_model = joblib.load("nb_model.pkl")
nb_label_encoder = joblib.load("nb_label_encoder.pkl")

ddos2vec_model = joblib.load("ddos2vec_classifier.pkl")
ddos2vec_w2v = Word2Vec.load("ddos2vec_embedding.model")
ddos2vec_label_map = joblib.load("ddos2vec_label_map.pkl")
ddos2vec_inv_label_map = {v: k for k, v in ddos2vec_label_map.items()}

# === Helpers ===

def sentence_to_vec(sentence, w2v_model):
    words = sentence.split()
    vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if not vecs:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vecs, axis=0)

def analyze_port_detections(model_name, predictions_df):
    attack_counts_by_port = defaultdict(int)
    for _, row in predictions_df.iterrows():
        if row["predicted_label"].lower() != "normal":
            attack_counts_by_port[row["dport"]] += 1
    return pd.DataFrame(
        [{"model": model_name, "port": port, "attack_count": count} for port, count in attack_counts_by_port.items()]
    )

def run_ddos2vec(df):
    df = df.dropna(subset=["proto", "sport", "dport"])
    df["sentence"] = df["proto"].astype(str) + "_" + df["sport"].astype(str) + "_" + df["dport"].astype(str)
    X = np.array([sentence_to_vec(s, ddos2vec_w2v) for s in df["sentence"]])
    if X.size == 0:
        raise ValueError("No valid vector inputs for DDoS2Vec.")
    y_pred = ddos2vec_model.predict(X)
    df["predicted_label"] = [ddos2vec_inv_label_map[i] for i in y_pred]
    return df


def run_ml_model(df, model, label_encoder):
    df["proto_enc"] = pd.factorize(df["proto"])[0]
    feature_cols = ["sport", "dport", "proto_enc", "packets", "bytes"]

    # Remove rows with missing or invalid values in any feature column
    df = df.dropna(subset=feature_cols)
    df = df[feature_cols].apply(pd.to_numeric, errors="coerce")  # force all to numeric
    df = df.dropna()

    if df.empty:
        raise ValueError("No valid rows after cleaning for model input.")

    X = df[feature_cols]
    y_pred = model.predict(X)
    df["predicted_label"] = label_encoder.inverse_transform(y_pred)
    return df


# === Parallel Processing Function ===
def process_file_parallel(file_path):
    result_list = []

    try:
        columns = ["sip", "dip", "sport", "dport", "proto", "packets", "bytes", "stime", "etime"]
        df = pd.read_csv(file_path, names=columns, header=None, low_memory=False)
    except Exception as e:
        print(f" Failed to read {file_path}: {e}")
        return []

    try:
        df_rf = run_ml_model(df.copy(), rf_model, rf_label_encoder)
        rf_res = analyze_port_detections("Random Forest", df_rf)
        result_list.append(rf_res)
    except Exception as e:
        print(f" RF error in {file_path}: {e}")

    try:
        df_nb = run_ml_model(df.copy(), nb_model, nb_label_encoder)
        nb_res = analyze_port_detections("Naive Bayes", df_nb)
        result_list.append(nb_res)
    except Exception as e:
        print(f" NB error in {file_path}: {e}")

    try:
        df_vec = run_ddos2vec(df.copy())
        ddos_res = analyze_port_detections("DDoS2Vec", df_vec)
        result_list.append(ddos_res)
    except Exception as e:
        print(f" DDoS2Vec error in {file_path}: {e}")

    return result_list

# === Run with ThreadPool ===
file_paths = glob.glob(os.path.join(ATTACK_DATA_FOLDER, "*.csv"))
all_results = []

print(f"\n Starting threaded processing with {NUM_THREADS} threads...")

with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = {executor.submit(process_file_parallel, path): path for path in file_paths}
    for future in as_completed(futures):
        try:
            result = future.result()
            if result:
                all_results.extend(result)
        except Exception as e:
            print(f" Thread error for {futures[future]}: {e}")

# === Save Output ===
if all_results:
    final_df = pd.concat(all_results, ignore_index=True)
    final_df = final_df.sort_values(by=["model", "attack_count"], ascending=[True, False])
    output_file = os.path.join(OUTPUT_FOLDER, "port_attack_summary.csv")
    final_df.to_csv(output_file, index=False)
    print(f"\n Saved threaded port-based attack summary to: {output_file}")
else:
    print(" No predictions made. Check for errors.")
