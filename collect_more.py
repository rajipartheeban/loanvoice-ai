import os
import time

import pandas as pd
from google_play_scraper import Sort, reviews

APPS = {
    "com.kreditbee.android": "KreditBee",
    "com.whizdm.moneyview.loans": "Moneyview",
    "com.earlysalary.android": "Fibe",
    "co.tslc.cashe.android": "CASHe",
}
PER_APP = 40000                      # maximum reviews per app
SINCE = pd.Timestamp("2026-05-01")   # stop when reviews are older than this

os.makedirs("data/raw", exist_ok=True)

for app_id, name in APPS.items():
    out = f"data/raw/{name}.csv"
    if os.path.exists(out):
        print(f"{name}: already downloaded, skipping")
        continue
    rows, token = [], None
    while len(rows) < PER_APP:
        batch = None
        for attempt in range(5):
            try:
                batch, token = reviews(app_id, lang="en", country="in", sort=Sort.NEWEST,
                                       count=200, continuation_token=token)
                break
            except Exception as e:
                print(f"  network problem ({type(e).__name__}), retrying in 10 seconds...")
                time.sleep(10)
        if not batch:
            break
        rows.extend(batch)
        oldest = batch[-1]["at"]
        print(f"{name}: {len(rows):,} reviews, back to {oldest.date()}")
        if oldest < SINCE or token is None:
            break
        time.sleep(1)
    if not rows:
        print(f"{name}: nothing downloaded, run the script again later")
        continue
    df = pd.DataFrame([{
        "review_id": r["reviewId"],
        "app_name": name,
        "rating": r["score"],
        "review_text": (r.get("content") or "").strip(),
        "review_date": r["at"].date().isoformat(),
        "app_version": r.get("reviewCreatedVersion") or r.get("appVersion"),
        "thumbs_up": r.get("thumbsUpCount", 0),
    } for r in rows])
    df = df[(df.review_text.str.len() > 0) & (pd.to_datetime(df.review_date) >= SINCE)]
    df = df.drop_duplicates("review_id")
    df.to_csv(out, index=False)
    print(f"{name}: saved {len(df):,} reviews to {out}")

files = [f"data/raw/{n}.csv" for n in APPS.values() if os.path.exists(f"data/raw/{n}.csv")]
all_df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
all_df.to_csv("data/reviews.csv", index=False)

all_df["review_date"] = pd.to_datetime(all_df["review_date"])
print("\nTotal reviews:", len(all_df))
print(all_df.groupby("app_name").agg(
    reviews=("rating", "size"),
    first_date=("review_date", "min"),
    last_date=("review_date", "max"),
    avg_rating=("rating", "mean"),
).round({"avg_rating": 2}))