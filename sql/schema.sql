-- LoanVoice AI - PostgreSQL schema
-- Running this file resets the tables (the pipeline runs it for you).

DROP VIEW IF EXISTS v_review_issues;
DROP TABLE IF EXISTS issue_impact, model_runs, predictions, hand_labels, reviews CASCADE;

-- One row per public app review (no reviewer names are stored)
CREATE TABLE reviews (
    review_id     VARCHAR(64) PRIMARY KEY,
    app_name      VARCHAR(100) NOT NULL,
    rating        SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text   TEXT NOT NULL,
    review_date   DATE NOT NULL,
    app_version   VARCHAR(30),
    thumbs_up     INTEGER DEFAULT 0
);
CREATE INDEX idx_reviews_app_date ON reviews (app_name, review_date);

-- Reviews a person read and labelled (ground truth for training and testing)
CREATE TABLE hand_labels (
    review_id  VARCHAR(64) PRIMARY KEY REFERENCES reviews (review_id),
    issue      VARCHAR(40) NOT NULL,
    split      VARCHAR(5)  NOT NULL CHECK (split IN ('train', 'test'))
);

-- The AI model's label for every review
CREATE TABLE predictions (
    review_id        VARCHAR(64) PRIMARY KEY REFERENCES reviews (review_id),
    predicted_issue  VARCHAR(40) NOT NULL,
    confidence       NUMERIC(5, 4) NOT NULL,
    model_version    VARCHAR(40) NOT NULL
);

-- One row per model training run, with its test scores
CREATE TABLE model_runs (
    model_version  VARCHAR(40) PRIMARY KEY,
    trained_at     TIMESTAMP NOT NULL,
    n_train        INTEGER NOT NULL,
    n_test         INTEGER NOT NULL,
    accuracy       NUMERIC(5, 4) NOT NULL,
    macro_f1       NUMERIC(5, 4) NOT NULL
);

-- Rating-gain estimate and roadmap priority per issue
CREATE TABLE issue_impact (
    issue                 VARCHAR(40) PRIMARY KEY,
    n_reviews             INTEGER NOT NULL,
    share_of_reviews      NUMERIC(6, 4) NOT NULL,
    avg_rating_with       NUMERIC(4, 2) NOT NULL,
    avg_rating_without    NUMERIC(4, 2) NOT NULL,
    expected_rating_gain  NUMERIC(5, 3) NOT NULL,
    effort_points         SMALLINT NOT NULL,
    priority_score        NUMERIC(7, 4) NOT NULL,
    priority_rank         SMALLINT NOT NULL
);
