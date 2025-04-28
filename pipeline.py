import pandas as pd
import os
import glob
import joblib
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

# === CONFIG ===
ATTACK_DATA_FOLDER = "attack_data" 
OUTPUT_FOLDER = "results_attack_eval"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

metrics_summary = []
detailed_metrics = []

#  Load models 
rf_model = joblib.load("rf_model.pkl")
rf_label_encoder = joblib.load("rf_label_encoder.pkl")

nb_model = joblib.load("nb_model.pkl")
nb_label_encoder = joblib.load("nb_label_encoder.pkl")

# Helper to prepare attack data
def prepare_attack_data(file_path):
    # Correct column names
    columns = ["sip", "dip", "sport", "dport", "proto", "packets", "bytes", "stime", "etime", "label"]
    df = pd.read_csv(file_path, names=columns)

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
        print("📊 Confusion Matrix:")
        print(confusion_matrix(all_true, all_pred))

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

""" # === Evaluate DDoS2Vec separately ===
print("\n Evaluating model: DDoS2Vec")

all_attack_files = glob.glob(os.path.join(ATTACK_DATA_FOLDER, "*.csv"))
merged_attack_file = "merged_attacks.csv"
merged_df = pd.concat([pd.read_csv(f) for f in all_attack_files], ignore_index=True)
merged_df.to_csv(merged_attack_file, index=False)

predict_ddos2vec(merged_attack_file)

df_ddos = pd.read_csv("ddos2vec_predictions.csv")
df_ddos.to_csv(os.path.join(OUTPUT_FOLDER, "ddos2vec_predictions.csv"), index=False)

# Evaluation
ddos_report = classification_report(df_ddos["label"], df_ddos["predicted_label"], output_dict=True)
precision, recall, f1, support = precision_recall_fscore_support(
    df_ddos["label"], df_ddos["predicted_label"], average='weighted')

metrics_summary.append({
    "model": "DDoS2Vec",
    "precision": round(precision, 4),
    "recall": round(recall, 4),
    "f1_score": round(f1, 4),
    "support": support
})

print(" Classification Report:")
print(classification_report(df_ddos["label"], df_ddos["predicted_label"]))
print(" Confusion Matrix:")
print(confusion_matrix(df_ddos["label"], df_ddos["predicted_label"])) """

