import pandas as pd
import glob
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Load all CSVs 
csv_files = glob.glob("training_data/*.csv")
print(f" Found {len(csv_files)} CSV files")

df_list = [pd.read_csv(f) for f in csv_files]
df = pd.concat(df_list, ignore_index=True)

print(f" Combined dataset shape: {df.shape}")

# Preprocess 
df.dropna(inplace=True)

# Label encode only necessary fields
le_proto = LabelEncoder()
df["proto_enc"] = le_proto.fit_transform(df["proto"])

# Define feature columns (skip sip/dip)
feature_cols = ["sport", "dport", "proto_enc", "packets", "bytes"]
X = df[feature_cols]
y = df["label"]

# Encode labels
le_label = LabelEncoder()
y_encoded = le_label.fit_transform(y)

# Train/test split 
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.25, random_state=42)

# Train Random Forest optimized
print(" Training Random Forest...")
clf = RandomForestClassifier(
    n_estimators=50,
    max_depth=15,
    n_jobs=-1,
    random_state=42
)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)

print(" Classification Report:")
print(classification_report(y_test, y_pred, target_names=le_label.classes_))

print(" Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save model
joblib.dump(clf, "rf_model.pkl")
joblib.dump(le_label, "rf_label_encoder.pkl")
print("\n Model and encoders saved!")
