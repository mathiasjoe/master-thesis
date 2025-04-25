# ddos2vec_corpus_gen.py
import pandas as pd
import os

def generate_corpus(input_csv_folder, output_corpus_path="ddos2vec_corpus.txt"):
    all_rows = []
    for file in os.listdir(input_csv_folder):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(input_csv_folder, file))
            df["sentence"] = df["proto"].astype(str) + "_" + df["sport"].astype(str) + "_" + df["dport"].astype(str)
            all_rows.extend(df["sentence"].tolist())

    with open(output_corpus_path, "w") as f:
        for row in all_rows:
            f.write(row + "\n")
    print(f" DDoS2Vec corpus saved to: {output_corpus_path}")
