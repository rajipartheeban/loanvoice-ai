"""
Statistics: which issues drive 1-star ratings, and did any app release hurt ratings?

1. Chi-square test of independence: issue type vs rating group (1-2, 3, 4-5 stars).
2. Share of 1-star reviews per issue, with a 95% Wilson confidence interval.
3. Release check: for every NEW app version, Welch's t-test on ratings in the
   30 days before vs the 30 days after release. Bonferroni correction is used
   because many releases are tested at once.
4. Rising issues: for each app, last month's share vs the average of the 3 months before.
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from .config import ISSUES, OUTPUT_DIR, PROBLEM_ISSUES


def version_key(v):
    """'9.1.10' -> (9, 1, 10), so versions compare as numbers, not text."""
    parts = []
    for piece in str(v).split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def p_text(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def run_statistics(df):
    df = df.copy()
    df["review_date"] = pd.to_datetime(df["review_date"])
    df["rating_group"] = pd.cut(df.rating, [0, 2, 3, 5], labels=["1-2 stars", "3 stars", "4-5 stars"])

    # 1. Chi-square: issue vs rating group
    table = pd.crosstab(df.issue, df.rating_group)
    chi2, p_chi, dof, _ = stats.chi2_contingency(table)
    cramers_v = np.sqrt(chi2 / (table.values.sum() * (min(table.shape) - 1)))

    # 2. 1-star share per issue with confidence interval
    one_star = []
    for issue, g in df.groupby("issue"):
        k, n = int((g.rating == 1).sum()), len(g)
        lo, hi = wilson_ci(k, n)
        one_star.append({"issue": issue, "label": ISSUES.get(issue, issue), "n": n,
                         "one_star_share": round(k / n, 3), "ci_low": round(lo, 3), "ci_high": round(hi, 3)})
    one_star.sort(key=lambda r: -r["one_star_share"])

    # 3. Release impact (30 days before vs after each NEW version)
    # A version's first review is not always its release date: people on old versions keep
    # reviewing for months. So a version only counts as a release if it is newer than every
    # version seen before it, has 30+ reviews, and comes 30+ days after the data starts.
    data_start = df.review_date.min()
    releases = []
    for app, g in df.groupby("app_name"):
        first_seen = g.groupby("app_version").review_date.min().sort_values()
        counts = g.app_version.value_counts()
        newest = None
        for version, rel_date in first_seen.items():
            key = version_key(version)
            is_newer = newest is None or key > newest
            if is_newer:
                newest = key
            if not is_newer or counts[version] < 30 or rel_date < g.review_date.min() + pd.Timedelta(days=30):
                continue
            before = g[(g.review_date < rel_date) & (g.review_date >= rel_date - pd.Timedelta(days=30))].rating
            after = g[(g.review_date >= rel_date) & (g.review_date < rel_date + pd.Timedelta(days=30))].rating
            if len(before) < 30 or len(after) < 30:
                continue
            t, p = stats.ttest_ind(after, before, equal_var=False)
            pooled = np.sqrt((before.var(ddof=1) + after.var(ddof=1)) / 2)
            releases.append({"app": app, "version": version, "release_date": rel_date.date().isoformat(),
                             "avg_before": round(before.mean(), 2), "avg_after": round(after.mean(), 2),
                             "change": round(after.mean() - before.mean(), 2),
                             "cohens_d": round((after.mean() - before.mean()) / pooled, 2) if pooled else 0.0,
                             "p_value": float(f"{p:.2g}"), "p_text": p_text(p), "n_before": len(before), "n_after": len(after)})
    alpha = 0.05 / max(1, len(releases))
    for r in releases:
        r["significant"] = bool(r["p_value"] < alpha)
    releases.sort(key=lambda r: r["change"])

    # 4. Rising issues per app (problem issues only)
    df["month"] = df.review_date.dt.to_period("M")
    months = sorted(df.month.unique())
    rising = []
    if len(months) >= 4:
        last_m, prev_m = months[-1], months[-4:-1]
        for app, g in df.groupby("app_name"):
            share = pd.crosstab(g.month, g.issue, normalize="index")
            if last_m not in share.index or (g.month == last_m).sum() < 100:
                continue
            for issue in PROBLEM_ISSUES:
                if issue not in share:
                    continue
                last, prev = float(share.loc[last_m, issue]), float(share.loc[share.index.isin(prev_m), issue].mean())
                rising.append({"app": app, "issue": issue, "label": ISSUES[issue], "last_month": round(last, 3),
                               "prev_3_months": round(prev, 3), "change_pts": round((last - prev) * 100, 1)})
        rising.sort(key=lambda r: -r["change_pts"])
    monthly = months

    results = {
        "chi_square": {"chi2": round(float(chi2), 1), "dof": int(dof), "p_value": float(f"{p_chi:.2g}"), "p_text": p_text(p_chi),
                       "cramers_v": round(float(cramers_v), 3)},
        "one_star_by_issue": one_star,
        "release_tests": releases,
        "bonferroni_alpha": round(alpha, 5),
        "rising_issues": rising[:10],
        "latest_month": str(monthly[-1]) if len(monthly) else None,
    }
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "statistics.json").write_text(json.dumps(results, indent=2))
    return results