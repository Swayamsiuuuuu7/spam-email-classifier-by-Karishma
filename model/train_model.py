"""
train_model.py
---------------
Loads data/dataset.csv, trains and evaluates two candidate models
(Multinomial Naive Bayes and Logistic Regression) on TF-IDF features,
picks the better performer on held-out test data, and saves:

    model/spam_classifier.joblib   (vectorizer + trained classifier)
    model/metrics.json             (accuracy / precision / recall / F1 + confusion matrix)

Run:
    python train_model.py
"""

import os
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, classification_report)

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "dataset.csv")
MODEL_PATH = os.path.join(HERE, "spam_classifier.joblib")
METRICS_PATH = os.path.join(HERE, "metrics.json")


def main():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "label"])

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=8000,
        min_df=2,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    candidates = {
        "naive_bayes": MultinomialNB(alpha=0.3),
        "logistic_regression": LogisticRegression(max_iter=1000, C=5.0),
    }

    results = {}
    best_name, best_model, best_f1 = None, None, -1

    for name, model in candidates.items():
        model.fit(X_train_vec, y_train)
        preds = model.predict(X_test_vec)

        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, pos_label="spam")
        rec = recall_score(y_test, preds, pos_label="spam")
        f1 = f1_score(y_test, preds, pos_label="spam")
        cm = confusion_matrix(y_test, preds, labels=["ham", "spam"]).tolist()

        results[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion_matrix": cm,  # rows/cols ordered [ham, spam]
        }

        print(f"\n=== {name} ===")
        print(classification_report(y_test, preds))

        if f1 > best_f1:
            best_name, best_model, best_f1 = name, model, f1

    print(f"\nBest model: {best_name} (F1={best_f1:.4f})")

    # Save the winning vectorizer + model together
    joblib.dump({"vectorizer": vectorizer, "model": best_model, "model_name": best_name},
                MODEL_PATH)

    metrics = {
        "best_model": best_name,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "results": results,
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
