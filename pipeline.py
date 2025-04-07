import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from ddos2vec_predict import predict_ddos2vec
import os

# Setup output folder
os.makedirs("results", exist_ok=True)
metrics_summary = []

# Load test dataset 
df = pd.read_csv("test_set.csv")
ip_encoder = joblib.load("ip_encoder.pkl")
label_encoder = joblib.load("label_encoder.pkl")

df["sip_enc"] = ip_encoder.transform(df["sip"])
df["dip_enc"] = ip_encoder.transform(df["dip"])
df["proto_enc"] = pd.factorize(df["proto"])[0]

X = df[["sip_enc", "dip_enc", "sport", "dport", "proto_enc", "packets", "bytes"]]
y_true = label_encoder.transform(df["label"])

# Load and evaluate traditional models
models = {
    "Random Forest": joblib.load("rf_model.pkl"),
    "Naive Bayes": joblib.load("nb_model.pkl"),
}

for name, model in models.items():
    print(f"\n🧪 Evaluating: {name}")
    y_pred = model.predict(X)
    class_report = classification_report(y_true, y_pred, target_names=label_encoder.classes_, output_dict=True)

    # Save predictions 
    df_out = df.copy()
    df_out["predicted_label"] = label_encoder.inverse_transform(y_pred)
    pred_file = f"results/{name.lower().replace(' ', '_')}_predictions.csv"
    df_out.to_csv(pred_file, index=False)
    print(f"✅ Predictions saved to: {pred_file}")

    # Save metrics summary 
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, average='weighted')
    metrics_summary.append({
        "model": name,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "support": support
    })


    print("✅ Classification Report:")
    print(classification_report(y_true, y_pred, target_names=label_encoder.classes_))
    print("📊 Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

# Evaluate DDoS2Vec 
predict_ddos2vec("test_set.csv")
df_ddos = pd.read_csv("ddos2vec_predictions.csv")
df_ddos.to_csv("results/ddos2vec_predictions.csv", index=False)
print("\n🧪 Evaluating: DDoS2Vec")

# Generate metrics
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

print("✅ Classification Report:")
print(classification_report(df_ddos["label"], df_ddos["predicted_label"]))
print("📊 Confusion Matrix:")
print(confusion_matrix(df_ddos["label"], df_ddos["predicted_label"]))

# Save metrics summary CSV 
metrics_df = pd.DataFrame(metrics_summary)
metrics_df.to_csv("results/model_metrics_summary.csv", index=False)
print("\n📁 Summary saved to: results/model_metrics_summary.csv")
