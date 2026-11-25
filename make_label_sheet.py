import pandas as pd

df = pd.read_csv("data/reviews.csv")
df["words"] = df["review_text"].fillna("").str.split().str.len()
useful = df[df["words"] >= 3]          # 1-2 word reviews ("good", "nice app") get a simple rule later
print("Reviews with 3+ words:", len(useful), "of", len(df))

# Test set: 500 random reviews, the honest exam paper for the AI
test = useful.sample(n=500, random_state=42)
rest = useful.drop(test.index)

# Training set: 1,500 reviews, with extra low-rated ones so every complaint type has examples
low = rest[rest["rating"] <= 3].sample(n=900, random_state=42)
high = rest[rest["rating"] >= 4].sample(n=600, random_state=42)
train = pd.concat([low, high])

sheet = pd.concat([test.assign(split="test"), train.assign(split="train")])
sheet = sheet.sample(frac=1, random_state=7)   # mix them up
sheet["issue"] = ""
sheet[["review_id", "app_name", "rating", "review_text", "issue", "split"]].to_csv(
    "data/to_label.csv", index=False, encoding="utf-8-sig")
print("Wrote data/to_label.csv with", len(sheet), "reviews:", sheet["split"].value_counts().to_dict())