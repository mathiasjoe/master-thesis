# DDoS2Vec Trainer
import pandas as pd
from gensim.models import Word2Vec
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
import os
import joblib

# Load corpus and train Word2Vec
def train_embeddings(corpus_file, embedding_size=100):
    with open(corpus_file, "r") as f:
        sentences = [line.strip().split() for line in f.readlines()]

    model = Word2Vec(sentences, vector_size=embedding_size, window=5, min_count=1)
    model.save("ddos2vec_embedding.model")
    #print("Word2Vec model saved.")
    return model

# Convert flow tokens to vectors
def sentence_to_vec(sentence, w2v_model):
    words = sentence.split()
    vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if not vecs:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vecs, axis=0)

# Train LSTM classifier 
def train_lstm_classifier(csv_folder, embedding_model_path="ddos2vec_embedding.model"):
    model = Word2Vec.load(embedding_model_path)
    X, y = [], []

    label_map = {}
    label_counter = 0

    for file in os.listdir(csv_folder):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(csv_folder, file))
            df["sentence"] = df["proto"].astype(str) + "_" + df["sport"].astype(str) + "_" + df["dport"].astype(str)
            for _, row in df.iterrows():
                label = row["label"]
                if label not in label_map:
                    label_map[label] = label_counter
                    label_counter += 1
                vec = sentence_to_vec(row["sentence"], model)
                X.append(vec)
                y.append(label_map[label])

    X = np.array(X)
    y = np.array(y)

    # LSTM expects 3D input
    X = X.reshape((X.shape[0], 1, X.shape[1]))

    classifier = Sequential()
    classifier.add(LSTM(64, input_shape=(1, model.vector_size)))
    classifier.add(Dense(len(label_map), activation="softmax"))

    classifier.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    classifier.fit(X, y, epochs=5, batch_size=64, verbose=1)

    classifier.save("ddos2vec_lstm.h5")
    joblib.dump(label_map, "ddos2vec_label_map.pkl")
    print("LSTM model and label map saved.")

#  Run all
if __name__ == "__main__":
    generate_corpus("training_data")  # folder with labeled flow CSVs
    train_embeddings("ddos2vec_corpus.txt")
    train_lstm_classifier("training_data")
