"""
"Ask the reviews" assistant.

Step 1 (always): find the reviews most related to the question (TF-IDF search).
Step 2 (optional): send those reviews to an LLM to write the answer.
    - Free and local: install Ollama, run `ollama pull llama3.2`, then set
          OLLAMA_MODEL=llama3.2
    - Any OpenAI-compatible API (OpenAI, Gemini, Groq and others offer one):
          LLM_BASE_URL=https://.../v1   LLM_API_KEY=...   LLM_MODEL=...
Without an LLM, the assistant writes a data summary of the matching reviews itself.
"""
import os
import re

import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .config import ISSUES


PRAISE_WORDS = {"praise", "like", "love", "happy", "positive", "best", "recommend", "good"}
COMPLAINT_WORDS = {"angry", "complain", "complaint", "complaints", "problem", "problems", "issue", "issues",
                   "why", "not", "fail", "failing", "failed", "bad", "worst", "unhappy", "delay", "stuck"}


def wants_complaints(question):
    """Most questions are about problems. Only praise questions should return happy reviews."""
    words = set(re.findall(r"[a-z]+", question.lower()))
    return bool(words & COMPLAINT_WORDS) or not (words & PRAISE_WORDS)


class ReviewSearch:
    def __init__(self, df):
        self.df = df.reset_index(drop=True)
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self.matrix = self.vec.fit_transform(self.df.review_text.fillna("").astype(str))

    def search(self, question, k=25, app=None):
        scores = linear_kernel(self.vec.transform([question]), self.matrix).ravel()
        res = self.df.assign(score=scores)
        if app:
            res = res[res.app_name == app]
        if wants_complaints(question):
            # keyword search can't tell "money not credited" from "money credited fast",
            # so for problem questions keep only unhappy reviews (1-3 stars, not labelled positive)
            res = res[(res.rating <= 3) & (res.issue != "positive")]
        return res[res.score > 0].sort_values("score", ascending=False).head(k)


def data_summary(question, hits):
    if hits.empty:
        return "No reviews matched that question. Try other words, for example 'money not credited' or 'KYC'."
    top = hits.issue.value_counts()
    main = top.index[0]
    lines = [
        f"Found {len(hits)} closely matching reviews (average rating {hits.rating.mean():.1f} stars).",
        f"Most of them are about **{ISSUES.get(main, main)}** ({top.iloc[0]} of {len(hits)}).",
    ]
    by_app = hits.app_name.value_counts()
    if len(by_app) > 1:
        lines.append(f"They come mostly from {by_app.index[0]} ({by_app.iloc[0]} reviews).")
    latest = pd.to_datetime(hits.review_date).max().date()
    lines.append(f"Most recent matching review: {latest}.")
    return " ".join(lines)


def llm_answer(question, hits):
    """Return an LLM answer, or None if no LLM is configured or it fails."""
    context = "\n".join(f"- ({r.app_name}, {r.rating}★, {r.review_date}) {r.review_text}"
                        for r in hits.head(25).itertuples())
    prompt = (
        "You are a product analyst. Answer the question using ONLY these app reviews. "
        "Give the main reasons, which app is most affected, and one suggested fix. "
        "Keep it under 120 words.\n\n"
        f"Question: {question}\n\nReviews:\n{context}"
    )
    try:
        if os.getenv("OLLAMA_MODEL"):
            r = requests.post(os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate",
                              json={"model": os.environ["OLLAMA_MODEL"], "prompt": prompt, "stream": False},
                              timeout=120)
            r.raise_for_status()
            return r.json()["response"].strip()
        if os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY"):
            r = requests.post(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                              headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
                              json={"model": os.environ["LLM_MODEL"],
                                    "messages": [{"role": "user", "content": prompt}]},
                              timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # show the data summary instead
        return f"(LLM unavailable: {exc})"
    return None


def monthly_brief(df, stats_results, impact_results):
    """A short plain-English summary of what changed, for the top of the app."""
    parts = []
    rising = [r for r in stats_results.get("rising_issues", []) if r["change_pts"] > 1]
    if rising:
        r = rising[0]
        month = pd.Period(stats_results["latest_month"]).strftime("%B %Y")
        parts.append(f"In {month}, **{r['label']}** complaints at {r['app']} rose to "
                     f"{r['last_month']:.0%} of reviews (from {r['prev_3_months']:.0%} in the 3 months before).")
    drops = [r for r in stats_results.get("release_tests", []) if r["significant"] and r["change"] < 0]
    if drops:
        d = drops[0]
        parts.append(f"{d['app']} version {d['version']} ({d['release_date']}) is linked to a significant rating "
                     f"drop: {d['avg_before']} → {d['avg_after']} stars (p {d['p_text']}).")
    top = impact_results["roadmap"][0]
    parts.append(f"Top priority fix: **{top['label']}**, expected +{top['gain']:.2f} stars for effort {top['effort']}/5.")
    return " ".join(parts)