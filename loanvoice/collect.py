"""
Collect REAL Google Play reviews (run this on your own laptop).

    python pipeline.py collect --apps com.example.loanapp1 com.example.loanapp2 --per-app 10000

Find an app's ID in its Play Store link: play.google.com/store/apps/details?id=<APP_ID>

Privacy: reviewer names and profile images are dropped and never stored.
Only collect public reviews, keep the request rate low, and use the data for
analysis and learning, not to identify individual people.
"""
import time

import pandas as pd

from .config import DATA_DIR


def collect_reviews(app_ids, per_app=5000, country="in", lang="en", pause=1.0):
    from google_play_scraper import Sort, reviews  # pip install google-play-scraper

    all_rows = []
    for app_id in app_ids:
        token, rows = None, []
        while len(rows) < per_app:
            batch, token = reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                                   count=min(200, per_app - len(rows)), continuation_token=token)
            if not batch:
                break
            rows.extend(batch)
            print(f"{app_id}: {len(rows):,} reviews")
            time.sleep(pause)
            if token is None:
                break
        for r in rows:
            all_rows.append({
                "review_id": r["reviewId"],
                "app_name": app_id,
                "rating": r["score"],
                "review_text": (r.get("content") or "").strip(),
                "review_date": r["at"].date().isoformat(),
                "app_version": r.get("reviewCreatedVersion") or r.get("appVersion"),
                "thumbs_up": r.get("thumbsUpCount", 0),
            })
    df = pd.DataFrame(all_rows)
    df = df[df.review_text.str.len() > 0].drop_duplicates("review_id")
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(DATA_DIR / "reviews.csv", index=False)
    print(f"Saved {len(df):,} reviews to data/reviews.csv")
    print("Next: label about 2,000 random reviews by hand in data/hand_labels.csv "
          "(columns: review_id, issue, split) - use `python pipeline.py sample-for-labelling`.")
    return df


def sample_for_labelling(n=2000, n_test=500, seed=42):
    """Create a sheet of random reviews for you to label by hand."""
    df = pd.read_csv(DATA_DIR / "reviews.csv")
    s = df.sample(n=min(n, len(df)), random_state=seed)[["review_id", "app_name", "rating", "review_text"]]
    s["issue"] = ""
    s["split"] = "train"
    s.loc[s.sample(n=min(n_test, len(s)), random_state=seed + 1).index, "split"] = "test"
    out = DATA_DIR / "to_label.csv"
    s.to_csv(out, index=False)
    print(f"Wrote {len(s):,} reviews to {out}. Fill the 'issue' column using the keys in "
          "loanvoice/config.py ISSUES, then save it as data/hand_labels.csv")
