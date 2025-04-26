import os
import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# CONFIG 
TRAINING_DATA_FOLDER = "training_data"
EMBEDDING_MODEL_FILE = "ddos2vec_embedding.model"
CLASSIFIER_FILE = "ddos2vec_classifier.pkl"
LABEL_MAP_FILE = "ddos2vec_label_map.pkl"
EMBEDDING_SIZE = 100
CHUNK_SIZE = 1000000  # Read 1mill rows at a time
WORKERS = os.cpu_count()  # Use all CPU cores


# Create label map (fast vectorized) 
def create_label_map(input_folder):
    all_labels = []
    for file in os.listdir(input_folder):
        if file.endswith(".csv"):
            for chunk in pd.read_csv(os.path.join(input_folder, file), usecols=["label"], chunksize=CHUNK_SIZE):
                all_labels.extend(chunk["label"].tolist())

    all_labels = list(set(all_labels))  # unique labels
    label_map = {label: idx for idx, label in enumerate(sorted(all_labels))}
    print(f" Label map created: {label_map}")
    return label_map


#  Sentence Generator 
class FlowSentenceGenerator:
    def __init__(self, csv_folder):
        self.files = [os.path.join(csv_folder, f) for f in os.listdir(csv_folder) if f.endswith(".csv")]

    def __iter__(self):
        for file in self.files:
            for chunk in pd.read_csv(file, usecols=["proto", "sport", "dport"], chunksize=CHUNK_SIZE):
                chunk["sentence"] = chunk["proto"].astype(str) + "_" + chunk["sport"].astype(str) + "_" + chunk["dport"].astype(str)
                for sentence in chunk["sentence"]:
                    yield sentence.split()


# Train Word2Vec Model 
def train_word2vec(csv_folder, embedding_model_path, embedding_size=100):
    sentences = FlowSentenceGenerator(csv_folder)
    w2v_model = Word2Vec(
        sentences,
        vector_size=embedding_size,
        window=5,
        min_count=1,
        workers=WORKERS
    )
    w2v_model.save(embedding_model_path)
    print(f" Word2Vec model saved to: {embedding_model_path}")
    return w2v_model


#  Convert sentence to vector 
def sentence_to_vec(sentence, w2v_model):
    words = sentence.split()
    vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if not vecs:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vecs, axis=0)


# Prepare Dataset (vectorized) 
def prepare_dataset(input_folder, w2v_model, label_map):
    X = []
    y = []

    for file in os.listdir(input_folder):
        if file.endswith(".csv"):
            for chunk in pd.read_csv(os.path.join(input_folder, file), usecols=["proto", "sport", "dport", "label"], chunksize=CHUNK_SIZE):
                chunk["sentence"] = chunk["proto"].astype(str) + "_" + chunk["sport"].astype(str) + "_" + chunk["dport"].astype(str)
                chunk["label_encoded"] = chunk["label"].map(label_map)

                X.extend([sentence_to_vec(s, w2v_model) for s in chunk["sentence"]])
                y.extend(chunk["label_encoded"].tolist())

    X = np.array(X)
    y = np.array(y)
    print(f" Prepared dataset: {X.shape[0]} samples")
    return X, y


# Train Classifier 
def train_classifier(X, y):
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(" Classification Report:")
    print(classification_report(y_test, y_pred))

    return clf


# MAIN
if __name__ == "__main__":
    print(" Creating label map...")
    label_map = create_label_map(TRAINING_DATA_FOLDER)

    print(" Training Word2Vec model...")
    w2v_model = train_word2vec(TRAINING_DATA_FOLDER, EMBEDDING_MODEL_FILE, embedding_size=EMBEDDING_SIZE)

    print(" Preparing dataset...")
    X, y = prepare_dataset(TRAINING_DATA_FOLDER, w2v_model, label_map)

    print(" Training classifier...")
    classifier = train_classifier(X, y)

    # Save everything
    joblib.dump(classifier, CLASSIFIER_FILE)
    joblib.dump(label_map, LABEL_MAP_FILE)

    print("\n DDoS2Vec training complete! Models and label map saved.")
