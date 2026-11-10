
import streamlit as st
import joblib
import json
import numpy as np
import re
import html
from pathlib import Path

st.set_page_config(
    page_title="Inbox Radar",
    page_icon="📡",
    layout="wide"
)

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "model" / "spam_classifier.joblib"
METRICS_PATH = ROOT / "model" / "metrics.json"

@st.cache_resource
def load_model():
    artifact = joblib.load(MODEL_PATH)
    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    return artifact, metrics

artifact, metrics = load_model()
vectorizer = artifact["vectorizer"]
model = artifact["model"]
model_name = artifact["model_name"]

def get_trigger_words(text, label, top_k=8):
    vec = vectorizer.transform([text])
    present = vec.nonzero()[1]

    if len(present) == 0:
        return []

    classes = list(model.classes_)
    idx = classes.index(label)

    if hasattr(model, "feature_log_prob_"):
        scores = (
            model.feature_log_prob_[idx]
            - model.feature_log_prob_[1 - idx]
        )
    elif hasattr(model, "coef_"):
        coef = model.coef_[0]
        spam_idx = classes.index("spam")
        scores = coef if idx == spam_idx else -coef
    else:
        return []

    names = vectorizer.get_feature_names_out()
    weighted = [(names[i], scores[i]) for i in present]
    weighted = [x for x in weighted if x[1] > 0]
    weighted.sort(key=lambda x: x[1], reverse=True)

    return [word for word, score in weighted[:top_k]]

SAMPLES = {
    "Lottery Scam": (
        "CONGRATULATIONS! You've WON $850,000!!!",
        "Dear Winner, your email address has won $850,000 "
        "in the International Online Lottery. Click here "
        "to claim your prize within 24 hours. Provide your "
        "bank details immediately."
    ),
    "Account Phishing": (
        "Your account has been LIMITED",
        "We detected unusual activity on your account. "
        "Click here to verify your identity immediately "
        "or your account will be permanently closed."
    ),
    "Retail Promotion": (
        "Flash sale: 30% off ends tonight",
        "Hi there, our biggest sale of the season ends "
        "at midnight. Shop your favorites before they "
        "are gone. Unsubscribe anytime."
    ),
    "Work Update": (
        "Meeting notes from today's sync",
        "Hi team, thanks for joining the call today. "
        "I've attached the notes from our discussion "
        "about the project timeline. Let me know if "
        "I missed anything."
    ),
    "Personal Note": (
        "Dinner this weekend?",
        "Hey, are you free for dinner this Saturday? "
        "Thinking of trying that new place downtown. "
        "Let me know what time works for you!"
    )
}

st.markdown("""
<style>
.stApp {
    background: #12151B;
    color: #ECEAE3;
}
h1, h2, h3 {
    color: #ECEAE3 !important;
}
.stTextArea textarea, .stTextInput input {
    background: #212834;
    color: white;
}
div.stButton > button {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📡 Inbox Radar")
st.caption("AI-powered Spam Email Classifier")
st.divider()

best = metrics["results"][metrics["best_model"]]

c1, c2, c3 = st.columns(3)
c1.metric("Model Accuracy", f'{best["accuracy"] * 100:.1f}%')
c2.metric("Training Samples", metrics["n_train"])
c3.metric("Testing Samples", metrics["n_test"])

st.caption(f"Active model: {model_name.replace('_', ' ').title()}")

st.divider()
st.subheader("01 — Analyze your email")

st.write("Choose a sample or enter your own email.")

cols = st.columns(5)

for i, name in enumerate(SAMPLES):
    if cols[i].button(name, use_container_width=True):
        st.session_state.subject = SAMPLES[name][0]
        st.session_state.body = SAMPLES[name][1]

subject = st.text_input(
    "Email Subject",
    key="subject",
    placeholder="Enter email subject..."
)

body = st.text_area(
    "Email Body",
    key="body",
    height=200,
    placeholder="Paste your email here..."
)

if st.button("🔍 Analyze Message", type="primary", use_container_width=True):

    text = (subject + ". " + body).strip(" .")

    if not text:
        st.warning("Please enter an email first.")
    else:
        vec = vectorizer.transform([text])
        prediction = model.predict(vec)[0]
        probabilities = model.predict_proba(vec)[0]

        classes = list(model.classes_)
        confidence = probabilities[classes.index(prediction)] * 100

        triggers = get_trigger_words(text, prediction)

        st.divider()
        st.subheader("02 — Analysis Results")

        r1, r2 = st.columns(2)

        if prediction == "spam":
            r1.error("⚠️ LIKELY SPAM")
        else:
            r1.success("✓ LOOKS LEGITIMATE")

        r2.metric("Confidence", f"{confidence:.1f}%")

        st.write("### Probability Breakdown")

        for cls, prob in zip(classes, probabilities):
            st.write(f"**{cls.upper()} — {prob * 100:.1f}%**")
            st.progress(float(prob))

        st.write("### 🚩 Flagged Signals")

        if triggers:
            st.write("Words that influenced the prediction:")
            st.write("  ".join([f"`{word}`" for word in triggers]))
        else:
            st.info("No strongly weighted words found.")

        st.write("### Email with Highlighted Signals")

        safe_text = html.escape(text)

        for word in sorted(triggers, key=len, reverse=True):
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            safe_text = pattern.sub(
                lambda m: (
                    '<mark style="background:#F2A93B;color:#12151B;'
                    'padding:2px;border-radius:3px;">'
                    + m.group(0) + '</mark>'
                ),
                safe_text
            )

        st.markdown(
            f'<div style="background:#212834;padding:20px;'
            f'border-radius:10px;line-height:2;color:#ECEAE3;">'
            f'{safe_text}</div>',
            unsafe_allow_html=True
        )

st.divider()
st.caption(
    "Inbox Radar | TF-IDF + Machine Learning | "
    "Educational demonstration"
)
