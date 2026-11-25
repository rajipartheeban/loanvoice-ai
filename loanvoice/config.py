"""Project settings shared by the pipeline and the Streamlit app."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
SQL_DIR = ROOT / "sql"

# PostgreSQL connection. Change it with an environment variable.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/loanvoice"
)

# Issue categories used for labelling. Keys are stored in the database.
# Based on the real reviews: "document_upload" was merged into "kyc_verification" (only 2 reviews),
# and "repayment_credit_score" was added (many complaints about paying back and CIBIL updates).
ISSUES = {
    "kyc_verification": "KYC & documents",
    "rejection_no_reason": "Rejected / no new loan without reason",
    "hidden_charges": "Hidden charges / high interest",
    "disbursal_delay": "Disbursal delay",
    "customer_support": "Poor customer support",
    "app_bugs": "App bugs / crashes",
    "recovery_calls": "Aggressive recovery calls",
    "repayment_credit_score": "Repayment & credit score problems",
    "positive": "Positive experience",
    "other": "Other / general",
}
PROBLEM_ISSUES = [k for k in ISSUES if k not in ("positive", "other")]

# Business-analyst assumptions for the roadmap (1 = small fix, 5 = big project).
EFFORT_POINTS = {
    "kyc_verification": 4,
    "rejection_no_reason": 2,
    "hidden_charges": 2,
    "disbursal_delay": 5,
    "customer_support": 3,
    "app_bugs": 2,
    "recovery_calls": 3,
    "repayment_credit_score": 3,
}

# Proposed fix for each issue (used in the roadmap table).
PROPOSED_FIX = {
    "kyc_verification": "Clear KYC error messages, retry for selfie/OTP checks, DigiLocker as a fallback, faster document review",
    "rejection_no_reason": "Show the main reason and the reapply date; a clear path back for customers who repaid on time",
    "hidden_charges": "Show total cost (fees, insurance, interest, APR) on one screen before e-sign",
    "disbursal_delay": "Live disbursal tracker with expected time, auto-escalate after 24 hours",
    "customer_support": "In-app ticket tracking, callback booking, first reply within 4 hours",
    "app_bugs": "Crash monitoring, staged rollouts, hotfix within 48 hours of a bad release",
    "recovery_calls": "Strict recovery-call policy, no contact-list access, complaint button in app",
    "repayment_credit_score": "Manual pay before the due date, retry auto-debit before any penalty, update payment and CIBIL within 48 hours, auto-send NOC",
}

# Share of affected users assumed to be satisfied once an issue is fixed.
DEFAULT_FIX_RATE = 0.6