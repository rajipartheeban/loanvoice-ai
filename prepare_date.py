import os
import shutil
from datetime import date

import pandas as pd

# 1. Keep an untouched backup of the raw data (only the first time)
backup = f"data/raw_reviews_{date.today()}.csv"
if not os.path.exists(backup):
    shutil.copy("data/reviews.csv", backup)
    print("Backup saved:", backup)

# 2. Replace app IDs with readable names
df = pd.read_csv("data/reviews.csv")
names = {
    "com.kreditbee.android": "KreditBee",
    "com.whizdm.moneyview.loans": "Moneyview",
    "com.earlysalary.android": "Fibe",
    "co.tslc.cashe.android": "CASHe",
}
df["app_name"] = df["app_name"].map(names).fillna(df["app_name"])
df.to_csv("data/reviews.csv", index=False)

# 3. Quick checks
df["review_date"] = pd.to_datetime(df["review_date"])
print("Total reviews:", len(df))
print(df.groupby("app_name").agg(
    reviews=("rating", "size"),
    first_date=("review_date", "min"),
    last_date=("review_date", "max"),
    avg_rating=("rating", "mean"),
).round(2))
print("Rating counts:", df["rating"].value_counts().sort_index().to_dict())
print("Very short reviews (under 10 characters):", (df["review_text"].str.len() < 10).sum())