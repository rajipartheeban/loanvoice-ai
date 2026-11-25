#!/usr/bin/env python3
"""
LoanVoice AI pipeline.

    python pipeline.py collect --apps <id> <id>   # download real Play Store reviews
    python pipeline.py run                        # full pipeline on data/reviews.csv + data/hand_labels.csv
"""
import argparse

import pandas as pd

from loanvoice import classify, db, impact, stats_tests
from loanvoice.config import DATA_DIR, ISSUES, OUTPUT_DIR


def run():
    reviews = pd.read_csv(DATA_DIR / "reviews.csv")
    hand = pd.read_csv(DATA_DIR / "hand_labels.csv")
    hand = hand[hand.issue.notna() & (hand.issue.astype(str).str.strip() != "")][["review_id", "issue", "split"]].copy()
    hand["issue"] = hand.issue.astype(str).str.strip().str.lower()
    hand["split"] = hand.split.astype(str).str.strip().str.lower()
    unknown = sorted(set(hand.issue) - set(ISSUES))
    if unknown:
        raise SystemExit(f"hand_labels.csv has issue names that are not in config.ISSUES: {unknown}. Fix them and run again.")
    missing = set(hand.review_id) - set(reviews.review_id)
    if missing:
        print(f"     note: skipping {len(missing)} hand labels whose review_id is not in reviews.csv")
        hand = hand[hand.review_id.isin(reviews.review_id)]
    engine = db.get_engine()
    print(f"1/5  Loading {len(reviews):,} reviews and {len(hand):,} hand labels into {engine.dialect.name}")
    db.reset_and_load(engine, reviews, hand)

    print("2/5  Training the issue classifier and testing it on hand-labelled reviews")
    predictions, metrics, model_run = classify.train_and_evaluate(reviews, hand)
    # 1-2 word reviews ("good", "nice app") carry no complaint detail: label them with a simple rule
    words = reviews.review_text.fillna("").astype(str).str.split().str.len()
    short = (words < 3).to_numpy()
    rule = (reviews.rating >= 4).map({True: "positive", False: "other"}).to_numpy()
    predictions.loc[short, "predicted_issue"] = rule[short]
    predictions.loc[short, "confidence"] = 1.0
    print(f"     {short.sum():,} short reviews labelled by rule, {(~short).sum():,} by the AI model")
    db.save_table(engine, predictions, "predictions")
    db.save_table(engine, model_run, "model_runs")
    db.create_view(engine)
    print(f"     accuracy {metrics['accuracy']:.1%} | macro F1 {metrics['macro_f1']:.3f} "
          f"on {metrics['n_test']} test reviews")

    labelled = db.read_sql(engine, "SELECT * FROM v_review_issues")
    labelled.to_csv(OUTPUT_DIR / "reviews_labelled.csv", index=False)   # for Power BI / Tableau

    print("3/5  Running statistical tests")
    s = stats_tests.run_statistics(labelled)
    print(f"     chi-square p {s['chi_square']['p_text']} | Cramér's V = {s['chi_square']['cramers_v']}")
    for r in [r for r in s["release_tests"] if r["significant"]][:3]:
        print(f"     {r['app']} {r['version']}: {r['avg_before']} -> {r['avg_after']} stars (p {r['p_text']})")

    print("4/5  Estimating rating gain and building the roadmap")
    result, table = impact.run_impact(labelled)
    db.save_table(engine, table, "issue_impact")
    print(f"     average rating {result['current_avg_rating']} -> {result['rating_if_top3_fixed']} "
          f"if the top 3 issues are fixed (fix rate {result['fix_rate']:.0%})")
    for r in result["roadmap"][:3]:
        print(f"     #{r['rank']} {r['label']}: +{r['gain']:.3f} stars, effort {r['effort']}")

    print("5/5  Done. Results in outputs/ and in the database. Start the app with:")
    print("     streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--apps", nargs="+", required=True, help="Play Store app IDs")
    c.add_argument("--per-app", type=int, default=5000)
    sub.add_parser("run")
    args = p.parse_args()
    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.cmd == "collect":
        from loanvoice.collect import collect_reviews
        collect_reviews(args.apps, args.per_app)
    else:
        run()