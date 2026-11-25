"""
Business impact: how much could the average rating rise if an issue is fixed?

For each issue i:
    share_i    = reviews about issue i / all reviews
    gap_i      = avg rating of reviews WITHOUT issue i - avg rating of reviews WITH issue i
    gain_i     = share_i x fix_rate x gap_i

fix_rate is the share of affected users who would be satisfied after the fix
(default 60%). It is an assumption: state it, and show what happens at 40% and 80%.

Roadmap priority = expected rating gain / effort points (effort from config.py).
"""
import json

import pandas as pd

from .config import DEFAULT_FIX_RATE, EFFORT_POINTS, ISSUES, OUTPUT_DIR, PROBLEM_ISSUES, PROPOSED_FIX


def rating_gain_table(df, fix_rate=DEFAULT_FIX_RATE):
    n_all, rows = len(df), []
    for issue in PROBLEM_ISSUES:
        with_i, without_i = df[df.issue == issue].rating, df[df.issue != issue].rating
        if len(with_i) == 0:
            continue
        share = len(with_i) / n_all
        gap = without_i.mean() - with_i.mean()
        rows.append({"issue": issue, "label": ISSUES[issue], "n_reviews": len(with_i),
                     "share_of_reviews": share, "avg_rating_with": with_i.mean(),
                     "avg_rating_without": without_i.mean(), "expected_rating_gain": share * fix_rate * gap})
    t = pd.DataFrame(rows)
    t["effort_points"] = t.issue.map(EFFORT_POINTS)
    t["priority_score"] = t.expected_rating_gain / t.effort_points
    t = t.sort_values("priority_score", ascending=False).reset_index(drop=True)
    t["priority_rank"] = range(1, len(t) + 1)
    return t


def run_impact(df, fix_rate=DEFAULT_FIX_RATE):
    overall = rating_gain_table(df, fix_rate)
    current = df.rating.mean()
    top3 = overall.head(3)
    by_app = {}
    for app, g in df.groupby("app_name"):
        t = rating_gain_table(g, fix_rate)
        best = t.sort_values("expected_rating_gain", ascending=False).head(3)
        by_app[app] = {"current_avg": round(g.rating.mean(), 2), "n_reviews": len(g),
                       "top_issues": [{"issue": r.issue, "label": r.label, "share": round(r.share_of_reviews, 3),
                                       "gain": round(r.expected_rating_gain, 3)} for r in best.itertuples()],
                       "rating_if_top3_fixed": round(g.rating.mean() + best.expected_rating_gain.sum(), 2)}
    sensitivity = {f"{int(fr * 100)}%": round(current + rating_gain_table(df, fr).head(3).expected_rating_gain.sum(), 2)
                   for fr in (0.4, 0.6, 0.8)}
    result = {
        "fix_rate": fix_rate,
        "current_avg_rating": round(current, 2),
        "rating_if_top3_fixed": round(current + top3.expected_rating_gain.sum(), 2),
        "top3_sensitivity": sensitivity,
        "rating_if_all_fixed": round(current + overall.expected_rating_gain.sum(), 2),
        "roadmap": [{"rank": int(r.priority_rank), "issue": r.issue, "label": r.label,
                     "share": round(r.share_of_reviews, 3), "avg_with": round(r.avg_rating_with, 2),
                     "avg_without": round(r.avg_rating_without, 2), "gain": round(r.expected_rating_gain, 3),
                     "effort": int(r.effort_points), "priority": round(r.priority_score, 4),
                     "fix": PROPOSED_FIX[r.issue]} for r in overall.itertuples()],
        "by_app": by_app,
    }
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "impact.json").write_text(json.dumps(result, indent=2))
    table = overall[["issue", "n_reviews", "share_of_reviews", "avg_rating_with", "avg_rating_without",
                     "expected_rating_gain", "effort_points", "priority_score", "priority_rank"]].round(4)
    return result, table
