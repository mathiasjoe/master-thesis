# ddos2vec_predict.py
import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from keras.models import load_model
import joblib

def sentence_to_vec(sentence, w2v_model):
    words = sentence.split()
    vecs = [w2v_model.wv[w] for w in words if w in w2v_model.wv]
    if not vecs:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vecs, axis=0)

def predict_ddos2vec(input_csv):
    df = pd.read_csv(input_csv)
    df["sentence"] = df["proto"].astype(str) + "_" + df["sport"].astype(str) + "_" + df["dport"].astype(str)

    w2v = Word2Vec.load("ddos2vec_embedding.model")
    model = load_model("ddos2vec_lstm.h5")
    label_map = joblib.load("ddos2vec_label_map.pkl")
    rev_label_map = {v: k for k, v in label_map.items()}

    X = np.array([sentence_to_vec(s, w2v) for s in df["sentence"]])
    X = X.reshape((X.shape[0], 1, X.shape[1]))

    predictions = model.predict(X)
    predicted_indices = np.argmax(predictions, axis=1)
    predicted_labels = [rev_label_map[i] for i in predicted_indices]

    df["predicted_label"] = predicted_labels
    df.to_csv("ddos2vec_predictions.csv", index=False)
    print("Predictions saved to ddos2vec_predictions.csv")
