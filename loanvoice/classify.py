"""
AI labelling: train a text classifier on hand-labelled reviews, measure it on
reviews it has never seen, then label every review.

Model: TF-IDF features (words + character pieces, so typos and Hinglish still
match) + the star rating -> Logistic Regression. Simple, fast, explainable, and a strong baseline.
Why the star rating: error analysis showed the text-only model calling happy 5-star reviews that
mention "loan" a "no new loan" complaint. The rating is known for every review, so it is a fair input.
Upgrade idea: compare it with sentence embeddings or an LLM, using the SAME test set.
"""
import json
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import ISSUES, OUTPUT_DIR

FEATURES = ["review_text", "rating"]


def build_model():
    text = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True)),
    ])
    features = ColumnTransformer([
        ("text", text, "review_text"),
        ("stars", OneHotEncoder(handle_unknown="ignore"), ["rating"]),
    ])
    return Pipeline([
        ("features", features),
        ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
    ])


def train_and_evaluate(reviews, hand_labels):
    data = hand_labels.merge(reviews[["review_id", "review_text", "rating"]], on="review_id")
    train, test = data[data.split == "train"], data[data.split == "test"]

    model = build_model().fit(train[FEATURES], train.issue)
    pred = model.predict(test[FEATURES])

    labels = [k for k in ISSUES if k in set(data.issue)]
    acc = accuracy_score(test.issue, pred)
    macro_f1 = f1_score(test.issue, pred, average="macro")
    report = classification_report(test.issue, pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(test.issue, pred, labels=labels)
    version = "tfidf-stars-logreg-" + datetime.now().strftime("%Y%m%d-%H%M")

    # Show a few mistakes so you can explain where the model struggles
    mistakes = test.assign(predicted=pred)
    mistakes = mistakes[mistakes.issue != mistakes.predicted].head(12)

    metrics = {
        "model_version": version,
        "n_train": int(len(train)), "n_test": int(len(test)),
        "accuracy": round(float(acc), 4), "macro_f1": round(float(macro_f1), 4),
        "labels": labels,
        "per_class": {k: {m: round(float(report[k][m]), 3) for m in ("precision", "recall", "f1-score", "support")}
                      for k in labels},
        "confusion_matrix": cm.tolist(),
        "example_mistakes": mistakes[["review_text", "issue", "predicted"]].to_dict("records"),
    }

    # Final model: retrain on ALL hand labels, then label every review
    final = build_model().fit(data[FEATURES], data.issue)
    proba = final.predict_proba(reviews[FEATURES])
    classes = final.classes_
    predictions = pd.DataFrame({
        "review_id": reviews.review_id,
        "predicted_issue": classes[proba.argmax(axis=1)],
        "confidence": np.round(proba.max(axis=1), 4),
        "model_version": version,
    })

    OUTPUT_DIR.mkdir(exist_ok=True)
    joblib.dump(final, OUTPUT_DIR / "issue_model.joblib")
    (OUTPUT_DIR / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    run = pd.DataFrame([{"model_version": version, "trained_at": datetime.now(), "n_train": len(train),
                         "n_test": len(test), "accuracy": round(acc, 4), "macro_f1": round(macro_f1, 4)}])
    return predictions, metrics, run