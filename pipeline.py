import pandas as pd
import os
import glob
import joblib
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from gensim.models import Word2Vec
import numpy as np

# === CONFIG ===
ATTACK_DATA_FOLDER = "training_data" 
OUTPUT_FOLDER = "results_attack_eval"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

metrics_summary = []
detailed_metrics = []

#  Load models 
rf_model = joblib.load("rf_model.pkl")
rf_label_encoder = joblib.load("rf_label_encoder.pkl")

nb_model = joblib.load("nb_model.pkl")
nb_label_encoder = joblib.load("nb_label_encoder.pkl")

def prepare_attack_data(file_path):
    # Read the CSV file normally, since it already contains headers
    df = pd.read_csv(file_path, low_memory=False)

    # Encode protocol field
    df["proto_enc"] = pd.factorize(df["proto"])[0]

    # Select the correct features
    feature_cols = ["sport", "dport", "proto_enc", "packets", "bytes"]
    X = df[feature_cols]

    return df, X


# Evaluate models
models = {
    "Random Forest": (rf_model, rf_label_encoder),
    "Naive Bayes": (nb_model, nb_label_encoder)
}

for name, (model, label_encoder) in models.items():
    print(f"\n Evaluating model: {name}")

    all_true = []
    all_pred = []

    # Process each attack file
    for file_path in glob.glob(os.path.join(ATTACK_DATA_FOLDER, "*.csv")):
        df, X = prepare_attack_data(file_path)

        if "label" not in df.columns:
            print(f" 'label' column missing in {file_path}")
            continue

        y_true = label_encoder.transform(df["label"])
        y_pred = model.predict(X)

        all_true.extend(y_true)
        all_pred.extend(y_pred)

    # Overall evaluation
    if all_true and all_pred:
        print(" Classification Report:")
        print(classification_report(all_true, all_pred, target_names=label_encoder.classes_))

        # Save high-level model metrics
        precision, recall, f1, support = precision_recall_fscore_support(all_true, all_pred, average='weighted')
        metrics_summary.append({
            "model": name,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "support": support
        })

        # Save full classification report
        class_report = classification_report(all_true, all_pred, target_names=label_encoder.classes_, output_dict=True)
        for label_name, scores in class_report.items():
            if label_name in ['accuracy', 'macro avg', 'weighted avg']:
                continue  # skip global averages for this file
            detailed_metrics.append({
                "model": name,
                "class": label_name,
                "precision": round(scores["precision"], 4),
                "recall": round(scores["recall"], 4),
                "f1_score": round(scores["f1-score"], 4),
                "support": int(scores["support"])
            })

    else:
        print(f" No valid data evaluated for model {name}.")

# Save final summary 
if metrics_summary:
    summary_df = pd.DataFrame(metrics_summary)
    summary_df.to_csv(os.path.join(OUTPUT_FOLDER, "model_metrics_summary.csv"), index=False)
    print("\n Global model summary saved to:", os.path.join(OUTPUT_FOLDER, "model_metrics_summary.csv"))

#Save full detailed classification report 
if detailed_metrics:
    detailed_df = pd.DataFrame(detailed_metrics)
    detailed_df.to_csv(os.path.join(OUTPUT_FOLDER, "model_classification_reports.csv"), index=False)
    print(" Detailed per-class classification reports saved to:", os.path.join(OUTPUT_FOLDER, "model_classification_reports.csv"))
else:
    print("\n No detailed report generated. Check your labels/data.")

 # === Evaluate DDoS2Vec separately ===
print("\n Evaluating model: DDoS2Vec")

# Load the models
w2v_model = Word2Vec.load("ddos2vec_embedding.model")
classifier = joblib.load("ddos2vec_classifier.pkl")
label_map = joblib.load("ddos2vec_label_map.pkl")
inv_label_map = {v: k for k, v in label_map.items()}

def sentence_to_vec(sentence, w2v_model):
    words = sentence.split()
    vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if not vecs:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vecs, axis=0)

# Prepare DDoS2Vec dataset
all_true, all_pred = [], []

for file_path in glob.glob(os.path.join(ATTACK_DATA_FOLDER, "*.csv")):
    df = pd.read_csv(file_path, usecols=["proto", "sport", "dport", "label"])
    df = df.dropna(subset=["label"])  # remove rows without labels

    df["sentence"] = df["proto"].astype(str) + "_" + df["sport"].astype(str) + "_" + df["dport"].astype(str)
    df["label_encoded"] = df["label"].map(label_map)

    X = np.array([sentence_to_vec(s, w2v_model) for s in df["sentence"]])
    y_true = df["label_encoded"].tolist()
    y_pred = classifier.predict(X)

    all_true.extend(y_true)
    all_pred.extend(y_pred)

# Evaluate
if all_true and all_pred:
    from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

    print(" Classification Report:")
    print(classification_report(all_true, all_pred, target_names=[inv_label_map[i] for i in sorted(inv_label_map)]))

    precision, recall, f1, support = precision_recall_fscore_support(all_true, all_pred, average='weighted')
    metrics_summary.append({
        "model": "DDoS2Vec",
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "support": support
    })

    # Detailed metrics
    detailed = classification_report(all_true, all_pred, target_names=[inv_label_map[i] for i in sorted(inv_label_map)], output_dict=True)
    for label, scores in detailed.items():
        if label in ['accuracy', 'macro avg', 'weighted avg']:
            continue
        detailed_metrics.append({
            "model": "DDoS2Vec",
            "class": label,
            "precision": round(scores["precision"], 4),
            "recall": round(scores["recall"], 4),
            "f1_score": round(scores["f1-score"], 4),
            "support": int(scores["support"])
        })

else:
    print(" No valid DDoS2Vec evaluation data found.")

