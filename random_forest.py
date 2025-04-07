import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib  # for saving model

# Load all CSVs 
csv_files = glob.glob("training_data/*.csv")
print(f"📂 Found {len(csv_files)} CSV files")

df_list = [pd.read_csv(f) for f in csv_files]
df = pd.concat(df_list, ignore_index=True)

#  Preprocess 

# Drop any rows with missing values
df.dropna(inplace=True)

# Label encode IP addresses and protocol
le_ip = LabelEncoder()
df["sip_enc"] = le_ip.fit_transform(df["sip"])
df["dip_enc"] = le_ip.fit_transform(df["dip"])
df["proto_enc"] = LabelEncoder().fit_transform(df["proto"])


feature_cols = ["sip_enc", "dip_enc", "sport", "dport", "proto_enc", "packets", "bytes"]
X = df[feature_cols]
y = df["label"]

# Encode labels
le_label = LabelEncoder()
y_encoded = le_label.fit_transform(y)

# Train/test split 
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.25, random_state=42)

# Train Random Forest
print("🌲 Training Random Forest...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)

print("✅ Classification Report:")
print(classification_report(y_test, y_pred, target_names=le_label.classes_))

print("📊 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save model and encoders
joblib.dump(clf, "rf_model.pkl")
joblib.dump(le_label, "rf_label_encoder.pkl")
joblib.dump(le_ip, "rf_ip_encoder.pkl")

print("\n Model and encoders saved!")
