"""
app.py
------
Flask backend for the Spam Email Classifier.

Serves the frontend (frontend/index.html, style.css, script.js) and exposes:

    GET  /api/metrics   -> model evaluation metrics (accuracy, precision, etc.)
    POST /api/predict    -> { text } -> { label, confidence, trigger_words }

Run:
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import os
import json
import re
import joblib
import numpy as np
from flask import Flask, request, jsonify, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL_PATH = os.path.join(ROOT, "model", "spam_classifier.joblib")
METRICS_PATH = os.path.join(ROOT, "model", "metrics.json")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

app = Flask(__name__, static_folder=None)

# --- Load model artifacts at startup ---------------------------------------
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        "Model file not found. Run `python model/train_model.py` first "
        "(after `python data/generate_dataset.py`)."
    )

artifact = joblib.load(MODEL_PATH)
vectorizer = artifact["vectorizer"]
model = artifact["model"]
model_name = artifact["model_name"]

with open(METRICS_PATH) as f:
    METRICS = json.load(f)

FEATURE_NAMES = np.array(vectorizer.get_feature_names_out())


def get_trigger_words(text, predicted_label, top_k=8):
    """
    Return the words/phrases in `text` that most pushed the prediction
    towards the predicted class, for interpretability in the UI.
    """
    vec = vectorizer.transform([text])
    present_idx = vec.nonzero()[1]
    if len(present_idx) == 0:
        return []

    classes = list(model.classes_)
    class_idx = classes.index(predicted_label)

    if hasattr(model, "feature_log_prob_"):
        # Naive Bayes: how much more likely each feature is under the
        # predicted class vs the other class.
        other_idx = 1 - class_idx
        scores = model.feature_log_prob_[class_idx] - model.feature_log_prob_[other_idx]
    elif hasattr(model, "coef_"):
        # Logistic Regression: raw coefficient, sign flipped for the "ham" class.
        coef = model.coef_[0]
        scores = coef if class_idx == list(model.classes_).index("spam") else -coef
    else:
        return []

    weighted = [(FEATURE_NAMES[i], scores[i]) for i in present_idx]
    weighted = [w for w in weighted if w[1] > 0]
    weighted.sort(key=lambda x: x[1], reverse=True)
    return [w for w, _ in weighted[:top_k]]


@app.route("/api/metrics", methods=["GET"])
def metrics():
    return jsonify(METRICS)


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Please provide some email text to analyze."}), 400

    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]
    proba = model.predict_proba(vec)[0]
    classes = list(model.classes_)
    confidence = float(proba[classes.index(pred)])

    triggers = get_trigger_words(text, pred)

    return jsonify({
        "label": pred,
        "confidence": round(confidence * 100, 1),
        "probabilities": {c: round(float(p) * 100, 1) for c, p in zip(classes, proba)},
        "trigger_words": triggers,
        "model_used": model_name,
    })


# --- Serve frontend ----------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
