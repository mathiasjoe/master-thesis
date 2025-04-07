import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix

# Load test dataset
df = pd.read_csv("test_set.csv")  # create this from your flow dataset

# Encode IPs and protocol
ip_encoder = joblib.load("ip_encoder.pkl")
label_encoder = joblib.load("label_encoder.pkl")

df["sip_enc"] = ip_encoder.transform(df["sip"])
df["dip_enc"] = ip_encoder.transform(df["dip"])
df["proto_enc"] = pd.factorize(df["proto"])[0]  # quick re-encoding

X = df[["sip_enc", "dip_enc", "sport", "dport", "proto_enc", "packets", "bytes"]]
y_true = label_encoder.transform(df["label"])

# Load and test each model
models = {
    "Random Forest": joblib.load("rf_model.pkl"),
    "Naive Bayes": joblib.load("nb_model.pkl"),
}

for name, model in models.items():
    print(f"\n🧪 Evaluating: {name}")
    y_pred = model.predict(X)
    print("✅ Classification Report:")
    print(classification_report(y_true, y_pred, target_names=label_encoder.classes_))
    print("📊 Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))
