-- LoanVoice AI - analysis queries (PostgreSQL)
-- Run after `python pipeline.py demo` (or `run`). All queries use the view v_review_issues.

-- 1. How big is each problem? Share of reviews and average rating per issue
SELECT issue,
       COUNT(*)                                            AS reviews,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_reviews,
       ROUND(AVG(rating), 2)                               AS avg_rating,
       ROUND(100.0 * AVG((rating = 1)::int), 1)            AS pct_one_star
FROM v_review_issues
GROUP BY issue
ORDER BY reviews DESC;

-- 2. Which app suffers most from each issue? (share of that app's reviews)
SELECT app_name, issue,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY app_name), 1) AS pct_of_app_reviews
FROM v_review_issues
GROUP BY app_name, issue
ORDER BY issue, pct_of_app_reviews DESC;

-- 3. Monthly average rating per app, with change vs the previous month
WITH monthly AS (
    SELECT app_name, DATE_TRUNC('month', review_date)::date AS month,
           AVG(rating) AS avg_rating, COUNT(*) AS reviews
    FROM v_review_issues
    GROUP BY app_name, DATE_TRUNC('month', review_date)
)
SELECT app_name, month, reviews, ROUND(avg_rating, 2) AS avg_rating,
       ROUND(avg_rating - LAG(avg_rating) OVER (PARTITION BY app_name ORDER BY month), 2) AS change_vs_prev_month
FROM monthly
ORDER BY app_name, month;

-- 4. Rising issues: last month's share vs the average of the 3 months before
WITH m AS (
    SELECT app_name, issue, DATE_TRUNC('month', review_date)::date AS month, COUNT(*) AS n
    FROM v_review_issues GROUP BY 1, 2, 3
), s AS (
    SELECT app_name, issue, month, n::numeric / SUM(n) OVER (PARTITION BY app_name, month) AS share
    FROM m
), w AS (
    SELECT *, AVG(share) OVER (PARTITION BY app_name, issue ORDER BY month
                               ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS prev_3m
    FROM s
)
SELECT app_name, issue, month, ROUND(100 * share, 1) AS pct_now, ROUND(100 * prev_3m, 1) AS pct_prev_3m,
       ROUND(100 * (share - prev_3m), 1) AS change_pts
FROM w
WHERE month = (SELECT MAX(DATE_TRUNC('month', review_date))::date FROM reviews)
  AND issue NOT IN ('positive', 'other')
ORDER BY change_pts DESC
LIMIT 10;

-- 5. Rating 30 days before vs after each app version release
WITH releases AS (
    SELECT app_name, app_version, MIN(review_date) AS release_date
    FROM reviews GROUP BY app_name, app_version
)
SELECT r.app_name, r.app_version, r.release_date,
       ROUND(AVG(v.rating) FILTER (WHERE v.review_date <  r.release_date), 2) AS avg_before,
       ROUND(AVG(v.rating) FILTER (WHERE v.review_date >= r.release_date), 2) AS avg_after,
       COUNT(*) FILTER (WHERE v.review_date >= r.release_date)               AS reviews_after
FROM releases r
JOIN v_review_issues v
  ON v.app_name = r.app_name
 AND v.review_date BETWEEN r.release_date - 30 AND r.release_date + 29
GROUP BY r.app_name, r.app_version, r.release_date
ORDER BY (AVG(v.rating) FILTER (WHERE v.review_date >= r.release_date)
        - AVG(v.rating) FILTER (WHERE v.review_date <  r.release_date));

-- 6. Most-agreed complaints (thumbs up) for the top issue - quotes for your report
SELECT app_name, rating, thumbs_up, review_text
FROM v_review_issues
WHERE issue = 'hidden_charges'
ORDER BY thumbs_up DESC
LIMIT 10;

-- 7. Model quality check: hand label vs model label on the TEST set
SELECT h.issue AS hand_label,
       COUNT(*) AS test_reviews,
       ROUND(100.0 * AVG((p.predicted_issue = h.issue)::int), 1) AS pct_model_agrees
FROM hand_labels h
JOIN predictions p USING (review_id)
WHERE h.split = 'test'
GROUP BY h.issue
ORDER BY pct_model_agrees;
-- Note: the final model is retrained on all hand labels, so this is optimistic.
-- The honest score is model_runs.accuracy (measured before retraining).

-- 8. Reviews the model is unsure about - label these by hand next
SELECT review_id, app_name, rating, predicted_issue, confidence, review_text
FROM reviews JOIN predictions USING (review_id)
WHERE review_id NOT IN (SELECT review_id FROM hand_labels)
ORDER BY confidence
LIMIT 50;

-- 9. The roadmap: issues ranked by expected rating gain per unit of effort
SELECT priority_rank, issue, n_reviews, ROUND(100 * share_of_reviews, 1) AS pct_reviews,
       avg_rating_with, avg_rating_without, expected_rating_gain, effort_points, priority_score
FROM issue_impact
ORDER BY priority_rank;

-- 10. Model run history
SELECT * FROM model_runs ORDER BY trained_at DESC;
