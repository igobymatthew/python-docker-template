import argparse
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
import joblib

LABELS = [
    "identity_attack",
    "insult",
    "obscene",
    "severe_toxicity",
    "sexual_explicit",
    "threat",
    "toxicity",
]

def load_data(path: str):
    df = pd.read_csv(path)
    X = df["text"].astype(str)
    y = df[LABELS]
    return train_test_split(X, y, test_size=0.2, random_state=42)

def train(data_path: str, model_dir: str = "models"):
    X_train, X_test, y_train, y_test = load_data(data_path)
    vect = TfidfVectorizer(max_features=5000)
    X_train_vec = vect.fit_transform(X_train)
    X_test_vec = vect.transform(X_test)
    clf = OneVsRestClassifier(LogisticRegression(max_iter=1000))
    clf.fit(X_train_vec, y_train)
    preds = clf.predict(X_test_vec)
    print(classification_report(y_test, preds, target_names=LABELS))
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "vectorizer": vect}, Path(model_dir) / "model.joblib")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train text classification model")
    parser.add_argument("data_path")
    parser.add_argument("--model_dir", default="models")
    args = parser.parse_args()
    train(args.data_path, args.model_dir)
