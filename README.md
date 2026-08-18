# Inbox Radar — Spam Email Classifier

A complete spam email classifier: a trained machine-learning model (TF-IDF +
Naive Bayes / Logistic Regression, whichever scores higher) served by a
Flask API, with a polished web UI to paste an email and see the verdict,
confidence score, and exactly which words drove the decision.

```
spam-email-classifier/
├── data/
│   ├── generate_dataset.py   # builds dataset.csv (synthetic, offline)
│   └── dataset.csv           # generated dataset (2,760 labeled emails)
├── model/
│   ├── train_model.py        # trains + evaluates the classifier
│   ├── spam_classifier.joblib
│   └── metrics.json
├── backend/
│   └── app.py                # Flask API + serves the frontend
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

## 1. Setup (in VS Code's terminal)

```bash
cd spam-email-classifier
python3 -m venv venv  ##Create the virtual environment

source venv/bin/activate  ##Activate it

python3 -m pip install --upgrade pip  
python3 -m pip install -r requirements.txt  ##Install requirements
```

## 2. Generate the dataset and train the model

The model and dataset are already included, but you can regenerate them
anytime (fully offline, no downloads needed):

```bash
python3 data/generate_dataset.py  ##Generate the dataset
python3 model/train_model.py  ##Train the model
```

This prints a classification report for both candidate models and saves
whichever performs better to `model/spam_classifier.joblib`.

## 3. Run the app

```bash
cd backend  ##Run the Flask app
python3 app.py
```

Open **http://127.0.0.1:5000** in your browser. Paste an email (or click one
of the sample chips), hit **Analyze message**, and you'll see:

- A **spam / legitimate** verdict with a confidence score
- A probability breakdown for both classes
- The specific **trigger words** that pushed the decision
- Your email text with those words **highlighted inline**

## How it works

- **Dataset**: `data/generate_dataset.py` synthetically builds a labeled
  dataset of ~2,760 emails across realistic categories (lottery scams,
  phishing, fake invoices, crypto scams, work emails, receipts, personal
  notes, newsletters, etc.), including deliberately "hard" examples with
  overlapping vocabulary so the model can't rely on obvious keyword
  shortcuts alone. This keeps the whole project runnable with no internet
  access or external downloads.
- **Model**: text is vectorized with TF-IDF (unigrams + bigrams), then two
  classifiers (Multinomial Naive Bayes and Logistic Regression) are trained
  and compared on a held-out test split; the better one is saved.
- **Interpretability**: for each prediction, the API surfaces the words
  present in the message that most strongly pushed it toward the predicted
  class (using the model's own learned weights), which the UI highlights.

## Using your own / real-world data

The bundled dataset is synthetic so the project works fully offline. For a
stronger, more realistic model, drop in a real labeled dataset — e.g. the
[SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
or [Enron-Spam](https://www2.aueb.gr/users/ion/data/enron-spam/) — as long
as it has `label` (`spam`/`ham`) and `text` columns matching
`data/dataset.csv`, then just re-run `python model/train_model.py`.

## Notes

- This is a demo/learning project, not a production spam filter — don't
  point it at real inboxes without proper safeguards (rate limiting, auth,
  a production WSGI server instead of Flask's dev server, etc.).
- Everything runs locally; no data leaves your machine.
