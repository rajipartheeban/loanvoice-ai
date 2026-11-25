"""Database helpers: create tables, load data, read results (PostgreSQL or SQLite)."""
import pandas as pd
from sqlalchemy import create_engine, text

from .config import DATABASE_URL, SQL_DIR

# Final label for each review: the hand label if a person labelled it, else the model's label.
VIEW_SQL = """
CREATE VIEW v_review_issues AS
SELECT r.review_id, r.app_name, r.rating, r.review_text, r.review_date, r.app_version, r.thumbs_up,
       COALESCE(h.issue, p.predicted_issue) AS issue,
       CASE WHEN h.issue IS NOT NULL THEN 'hand' ELSE 'model' END AS label_source,
       p.confidence
FROM reviews r
LEFT JOIN hand_labels h ON h.review_id = r.review_id
LEFT JOIN predictions p ON p.review_id = r.review_id
"""


def get_engine(url=DATABASE_URL):
    return create_engine(url)


def is_postgres(engine):
    return engine.dialect.name == "postgresql"


def reset_and_load(engine, reviews, hand_labels):
    """Create fresh tables and load reviews + hand labels."""
    if is_postgres(engine):
        with engine.begin() as con:
            con.exec_driver_sql((SQL_DIR / "schema.sql").read_text())
        mode = "append"
    else:
        with engine.begin() as con:
            for t in ["v_review_issues"]:
                con.exec_driver_sql(f"DROP VIEW IF EXISTS {t}")
        mode = "replace"
    reviews = reviews.copy()
    reviews["review_date"] = pd.to_datetime(reviews["review_date"]).dt.date
    reviews.to_sql("reviews", engine, if_exists=mode, index=False, chunksize=1000, method="multi")
    hand_labels[["review_id", "issue", "split"]].to_sql("hand_labels", engine, if_exists=mode, index=False)


def save_table(engine, df, name):
    """Replace the contents of a results table (keeps the PostgreSQL types and keys)."""
    if is_postgres(engine):
        with engine.begin() as con:
            con.execute(text(f"DELETE FROM {name}"))
        df.to_sql(name, engine, if_exists="append", index=False, chunksize=1000, method="multi")
    else:
        df.to_sql(name, engine, if_exists="replace", index=False)


def create_view(engine):
    with engine.begin() as con:
        con.exec_driver_sql("DROP VIEW IF EXISTS v_review_issues")
        con.exec_driver_sql(VIEW_SQL)


def read_sql(engine, sql, **params):
    with engine.connect() as con:
        return pd.read_sql(text(sql), con, params=params)
