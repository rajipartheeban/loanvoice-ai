"""
Sample review data for the demo.

Creates realistic-looking Google Play reviews for four DEMO loan apps (App A-D),
January-October 2026, plus a hand-labelled subset. Use this to learn and test
the pipeline. For the real project, collect real reviews with collect.py.

Patterns built into the data (your analysis should find them):
  * App A has the most disbursal-delay complaints.
  * App B released version 6.2.0 on 8 July 2026; crash complaints jumped and
    ratings fell until the 6.2.2 hotfix on 20 August.
  * App C has the most hidden-charges complaints.
  * App D has the most KYC and document-upload complaints.
  * App A's disbursal-delay complaints jump in October (festive season).
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .config import DATA_DIR

RATING_PROBS = {  # probability of 1..5 stars for each issue
    "positive":            [0.00, 0.00, 0.05, 0.30, 0.65],
    "other":               [0.35, 0.15, 0.20, 0.15, 0.15],
    "kyc_verification":    [0.55, 0.20, 0.15, 0.07, 0.03],
    "document_upload":     [0.50, 0.22, 0.16, 0.08, 0.04],
    "rejection_no_reason": [0.70, 0.15, 0.08, 0.04, 0.03],
    "hidden_charges":      [0.78, 0.12, 0.06, 0.02, 0.02],
    "disbursal_delay":     [0.62, 0.18, 0.10, 0.06, 0.04],
    "customer_support":    [0.60, 0.20, 0.12, 0.05, 0.03],
    "app_bugs":            [0.45, 0.25, 0.18, 0.08, 0.04],
    "recovery_calls":      [0.85, 0.08, 0.04, 0.02, 0.01],
}

# Share of reviews per issue for each app (normal months)
APP_MIX = {
    "App A": {"positive": .40, "other": .08, "kyc_verification": .05, "document_upload": .05, "rejection_no_reason": .07,
              "hidden_charges": .06, "disbursal_delay": .15, "customer_support": .06, "app_bugs": .05, "recovery_calls": .03},
    "App B": {"positive": .44, "other": .08, "kyc_verification": .06, "document_upload": .06, "rejection_no_reason": .07,
              "hidden_charges": .05, "disbursal_delay": .06, "customer_support": .07, "app_bugs": .07, "recovery_calls": .04},
    "App C": {"positive": .38, "other": .08, "kyc_verification": .05, "document_upload": .04, "rejection_no_reason": .07,
              "hidden_charges": .16, "disbursal_delay": .06, "customer_support": .08, "app_bugs": .04, "recovery_calls": .04},
    "App D": {"positive": .40, "other": .08, "kyc_verification": .12, "document_upload": .12, "rejection_no_reason": .07,
              "hidden_charges": .04, "disbursal_delay": .05, "customer_support": .06, "app_bugs": .04, "recovery_calls": .02},
}

CORE = {
    "kyc_verification": [
        "KYC failed {n} times, Aadhaar OTP is not coming",
        "video KYC keeps disconnecting in the middle",
        "PAN verification failed even though my details are correct",
        "stuck on the KYC screen for {d} days",
        "Aadhaar OTP never arrives so I cannot complete KYC",
        "selfie verification keeps failing, says face not matching",
        "e-KYC page shows server error every time",
        "my KYC is pending for {d} days with no update",
    ],
    "document_upload": [
        "bank statement PDF is not accepted, it says password protected",
        "salary slip upload fails every time",
        "document upload is stuck at 99 percent",
        "it says file size too large, my photo is only {n} MB",
        "uploaded my documents {n} times but it keeps asking again",
        "cannot upload ITR, the app gives an error",
        "the app rejects my statement saying invalid file format",
        "document upload page keeps loading and never finishes",
    ],
    "rejection_no_reason": [
        "loan rejected without giving any reason",
        "my CIBIL is {score} and still rejected, no explanation",
        "application rejected after taking all my details",
        "they rejected me but did not tell why",
        "rejected in seconds, they don't even check properly",
        "eligible amount was shown but then rejected without reason",
    ],
    "hidden_charges": [
        "processing fee of Rs {fee} deducted without telling clearly",
        "interest rate is much higher than shown in the ad",
        "insurance was added to my loan without asking me",
        "I got Rs {amt} less than the approved amount because of hidden charges",
        "so many hidden charges, total cost is not shown upfront",
        "they charged GST and fees that were never mentioned",
        "the actual interest is almost double what they showed",
    ],
    "disbursal_delay": [
        "loan approved but money not credited for {d} days",
        "disbursal pending since {d} days, no update",
        "amount not received in my account even after e-sign",
        "they said 10 minutes disbursal but it took {d} days",
        "approved {d} days ago, still waiting for the money",
        "money is not credited and the status still shows processing",
    ],
    "customer_support": [
        "customer care never picks up the call",
        "no response to my emails for {d} days",
        "the chat bot is useless and there is no option to talk to a human",
        "raised a ticket {d} days ago, nobody replied",
        "support team gives the same copy paste reply every time",
        "customer care number is always busy",
    ],
    "app_bugs": [
        "the app crashes as soon as I open it",
        "after the latest update the app keeps crashing",
        "stuck on the loading screen after login",
        "OTP screen freezes after the new update",
        "app shows a blank white screen",
        "login error every time since the update",
        "the app hangs when I click on apply",
    ],
    "recovery_calls": [
        "recovery agents are calling my family and friends",
        "they call me {n} times a day for payment, it is harassment",
        "recovery team is very rude and threatening",
        "they called my office about the EMI, very embarrassing",
        "getting abusive calls from recovery agents",
    ],
    "positive": [
        "got my loan in {m} minutes, very smooth process",
        "quick disbursal and easy KYC",
        "very good app, money credited the same day",
        "simple process and low interest rate",
        "customer support helped me quickly",
        "best loan app, transparent charges",
        "easy to use and fast approval",
        "the whole process was paperless and fast",
    ],
    "other": [
        "worst app", "bad app", "not good", "waste of time", "useless app",
        "ok ok app", "average experience", "not satisfied", "could be better",
        "fake app", "don't download", "nothing works properly",
    ],
}
SHORT_POSITIVE = ["good app", "nice app", "super", "very nice", "good service", "excellent"]
NEG_OPENERS = ["Worst experience.", "Very disappointed.", "Totally useless.", "Not happy.", "Very bad experience.", "Please fix this."]
NEG_CLOSERS = ["Don't install this app.", "Fix it asap.", "Uninstalling now.", "Giving 1 star.", "Very poor service.", "Hope you fix it soon."]
POS_OPENERS = ["Excellent app!", "Very good experience.", "Superb.", "Happy with the service."]
POS_CLOSERS = ["Highly recommended.", "Thank you team.", "Will use again.", "Keep it up."]
HINGLISH = {
    "disbursal_delay": ["paisa abhi tak nahi aaya", "paise nahi aaye abhi tak"],
    "customer_support": ["koi call nahi uthata", "customer care bekar hai"],
    "app_bugs": ["app baar baar band ho jata hai"],
    "hidden_charges": ["bahut zyada charges kaat liye"],
    "other": ["ekdum bekar app", "kya bakwas app hai"],
    "positive": ["bahut accha app hai", "jaldi paisa mil gaya"],
}

VERSIONS = {  # (release date, version) per app
    "App A": [("2025-12-15", "4.8.0"), ("2026-02-10", "4.9.0"), ("2026-04-20", "5.0.0"), ("2026-07-01", "5.1.0"), ("2026-09-15", "5.2.0")],
    "App B": [("2025-12-01", "6.0.0"), ("2026-03-05", "6.1.0"), ("2026-07-08", "6.2.0"), ("2026-08-20", "6.2.2"), ("2026-10-05", "6.3.0")],
    "App C": [("2025-11-20", "3.4.0"), ("2026-02-25", "3.5.0"), ("2026-05-30", "3.6.0"), ("2026-08-30", "3.7.0")],
    "App D": [("2025-12-10", "2.1.0"), ("2026-03-15", "2.2.0"), ("2026-06-10", "2.3.0"), ("2026-09-01", "2.4.0")],
}


def _version_on(app, day):
    current = VERSIONS[app][0][1]
    for d, v in VERSIONS[app]:
        if date.fromisoformat(d) <= day:
            current = v
    return current


def _typo(rng, text):
    words = text.split()
    if len(words) < 3:
        return text
    i = rng.integers(0, len(words))
    w = words[i]
    if len(w) > 3:
        j = rng.integers(1, len(w) - 1)
        words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def _sentence(rng, issue):
    s = rng.choice(CORE[issue])
    return s.format(n=rng.integers(2, 9), d=rng.integers(2, 15), score=rng.integers(720, 820),
                    fee=rng.choice([999, 1499, 2499, 3500]), amt=rng.choice([1800, 2500, 4000, 6500]),
                    m=rng.choice([5, 10, 15]))


def _review_text(rng, issue):
    negative = issue not in ("positive",)
    if issue == "positive" and rng.random() < 0.15:
        return rng.choice(SHORT_POSITIVE)
    parts = []
    if issue != "other" and rng.random() < 0.3:
        parts.append(rng.choice(NEG_OPENERS if negative else POS_OPENERS))
    if issue in HINGLISH and rng.random() < 0.12:
        parts.append(rng.choice(HINGLISH[issue]))
    else:
        main = _sentence(rng, issue)
        parts.append(main[0].upper() + main[1:] + ".")
    if issue not in ("positive", "other") and rng.random() < 0.25:  # a second, smaller complaint
        other_issue = rng.choice([k for k in CORE if k not in ("positive", "other", issue)])
        parts.append("Also " + _sentence(rng, other_issue) + ".")
    if issue == "other" and rng.random() < 0.25:
        parts.append(rng.choice(NEG_CLOSERS))
    elif issue != "other" and rng.random() < 0.3:
        parts.append(rng.choice(NEG_CLOSERS if negative else POS_CLOSERS))
    text = " ".join(parts)
    if rng.random() < 0.3:
        text = text.lower()
    if rng.random() < 0.15:
        text = text.replace(".", "").replace(",", "")
    if rng.random() < 0.10:
        text = _typo(rng, text)
    return text


def make_demo_reviews(n_per_app=5000, n_hand_labelled=2000, seed=7):
    rng = np.random.default_rng(seed)
    start, end = date(2026, 1, 1), date(2026, 10, 31)
    days = (end - start).days + 1
    weights = np.linspace(0.8, 1.2, days)
    weights /= weights.sum()
    rows = []
    for app, mix in APP_MIX.items():
        for _ in range(n_per_app):
            day = start + timedelta(days=int(rng.choice(days, p=weights)))
            m = dict(mix)
            m["positive"] *= 1.5  # many happy users leave short 5-star reviews
            # App B's bad release: crash complaints jump until the hotfix
            if app == "App B" and date(2026, 7, 8) <= day < date(2026, 8, 20):
                m["app_bugs"] += 0.25
                m["positive"] -= 0.18
            # App A: disbursal delays jump in the October festive season
            if app == "App A" and day >= date(2026, 10, 1):
                m["disbursal_delay"] += 0.12
                m["positive"] -= 0.10
            keys = list(m)
            p = np.array([m[k] for k in keys]); p /= p.sum()
            issue = keys[rng.choice(len(keys), p=p)]
            rating = int(rng.choice([1, 2, 3, 4, 5], p=RATING_PROBS[issue]))
            thumbs = int(rng.lognormal(1.2 if rating <= 2 else 0.3, 1.0)) if rng.random() < 0.6 else 0
            rows.append({"app_name": app, "rating": rating, "review_text": _review_text(rng, issue),
                         "review_date": day.isoformat(), "app_version": _version_on(app, day),
                         "thumbs_up": thumbs, "_true_issue": issue})
    df = pd.DataFrame(rows).sort_values(["review_date", "app_name"]).reset_index(drop=True)
    df.insert(0, "review_id", [f"R{100000 + i}" for i in range(len(df))])

    # Hand-labelled subset: a random sample a person would read and label.
    hand = df.sample(n=n_hand_labelled, random_state=seed)[["review_id", "_true_issue"]].rename(
        columns={"_true_issue": "issue"})
    # People make mistakes too: about 2% of hand labels disagree with the "true" issue
    noisy = hand.sample(frac=0.02, random_state=seed + 2).index
    hand.loc[noisy, "issue"] = rng.choice(list(CORE), size=len(noisy))
    hand["split"] = "train"
    hand.loc[hand.sample(n=500, random_state=seed + 1).index, "split"] = "test"
    reviews = df.drop(columns="_true_issue")
    return reviews, hand.reset_index(drop=True)


def save_demo_data():
    DATA_DIR.mkdir(exist_ok=True)
    reviews, hand = make_demo_reviews()
    reviews.to_csv(DATA_DIR / "reviews.csv", index=False)
    hand.to_csv(DATA_DIR / "hand_labels.csv", index=False)
    print(f"Demo data: {len(reviews):,} reviews, {len(hand):,} hand-labelled "
          f"({(hand.split == 'train').sum()} train / {(hand.split == 'test').sum()} test)")
    return reviews, hand
