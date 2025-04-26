import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib

#  Load and Combine CSVs 
csv_files = glob.glob("training_data/*.csv")
print(f" Found {len(csv_files)} CSV files")

df_list = [pd.read_csv(f) for f in csv_files]
df = pd.concat(df_list, ignore_index=True)
df.dropna(inplace=True)

# Optional: Sample down to 1M rows if dataset too large
# df = df.sample(n=1_000_000, random_state=42)

#  Encode protocol field only
proto_encoder = LabelEncoder()
df["proto_enc"] = proto_encoder.fit_transform(df["proto"])

# Select features (SKIP sip/dip for optimization) 
feature_cols = ["sport", "dport", "proto_enc", "packets", "bytes"]
X = df[feature_cols]

#  Label encode target 
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(df["label"])

#  Split train/test 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

#  Train Naive Bayes 
print(" Training Gaussian Naive Bayes...")
model = GaussianNB()
model.fit(X_train, y_train)

#  Evaluate 
y_pred = model.predict(X_test)

print(" Classification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

print(" Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# === Save model and encoders ===
joblib.dump(model, "nb_model.pkl")
joblib.dump(label_encoder, "nb_label_encoder.pkl")
joblib.dump(proto_encoder, "nb_proto_encoder.pkl")

print("\n Naive Bayes model and encoders saved!")
