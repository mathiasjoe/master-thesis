import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime

# Constants
ARTEFACTS_PATH = "./Artefacts/"
FLOW_DATA_PATH = "./FlowData/"
FLOW_FILE = "flow_data.csv"  # Replace with your actual flow data file
LABEL_FILE = "labels.csv"    # Replace with your actual labels file

# Ensure artefacts directory exists
os.makedirs(ARTEFACTS_PATH, exist_ok=True)

def load_flow_data(flow_file):
    """
    Load flow data from a CSV file.
    """
    df = pd.read_csv(flow_file)
    return df

def preprocess_data(df):
    """
    Preprocess the flow data.
    """
    # Example preprocessing steps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.dropna()
    return df

def generate_corpus(df):
    """
    Generate a text corpus from the flow data.
    """
    corpus = df['flow_features'].astype(str).tolist()
    return corpus

def vectorize_corpus(corpus):
    """
    Vectorize the text corpus using TF-IDF.
    """
    vectorizer = TfidfVectorizer()
    X_tfidf = vectorizer.fit_transform(corpus)
    return X_tfidf, vectorizer

def reduce_dimensions(X, n_components=100):
    """
    Reduce dimensionality using Truncated SVD.
    """
    svd = TruncatedSVD(n_components=n_components)
    X_reduced = svd.fit_transform(X)
    return X_reduced, svd

def scale_features(X):
    """
    Scale features to zero mean and unit variance.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler

def save_artefacts(artefacts, artefact_names):
    """
    Save artefacts (e.g., models, scalers) to disk.
    """
    for artefact, name in zip(artefacts, artefact_names):
        with open(os.path.join(ARTEFACTS_PATH, name), 'wb') as f:
            pickle.dump(artefact, f)

def main():
    # Load and preprocess flow data
    flow_data_path = os.path.join(FLOW_DATA_PATH, FLOW_FILE)
    df = load_flow_data(flow_data_path)
    df = preprocess_data(df)

    # Generate corpus
    corpus = generate_corpus(df)

    # Vectorize corpus
    X_tfidf, vectorizer = vectorize_corpus(corpus)

    # Reduce dimensions
    X_reduced, svd = reduce_dimensions(X_tfidf)

    # Scale features
    X_scaled, scaler = scale_features(X_reduced)

    # Save artefacts
    artefacts = [vectorizer, svd, scaler]
    artefact_names = ['tfidf_vectorizer.pkl', 'svd_model.pkl', 'scaler.pkl']
    save_artefacts(artefacts, artefact_names)

    # Save processed data
    processed_data_path = os.path.join(ARTEFACTS_PATH, 'processed_flow_data.npy')
    np.save(processed_data_path, X_scaled)
    print(f"Processed data saved to {processed_data_path}")

if __name__ == "__main__":
    main()
