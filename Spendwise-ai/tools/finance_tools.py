import json
import os
from io import BytesIO
from pathlib import Path

import boto3
import pandas as pd
from strands import tool


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
BUDGET_FILE = BASE_DIR / "data" / "budgets.json"

REQUIRED_COLUMNS = {
    "transaction_date",
    "description",
    "category",
    "amount",
    "type",
}


# ---------------------------------------------------------
# Load transactions from Amazon S3
# ---------------------------------------------------------

def load_transactions() -> pd.DataFrame:
    """
    Download the transaction CSV from S3 and validate its
    structure before returning a pandas DataFrame.
    """

    bucket = os.environ.get("SPENDWISE_S3_BUCKET")
    key = os.environ.get(
        "SPENDWISE_S3_KEY",
        "transactions/spendwise_demo_transactions.csv",
    )
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not bucket:
        raise ValueError(
            "SPENDWISE_S3_BUCKET environment variable is not set."
        )

    s3 = boto3.client("s3", region_name=region)

    response = s3.get_object(Bucket=bucket, Key=key)
    csv_content = response["Body"].read()

    df = pd.read_csv(BytesIO(csv_content))

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {sorted(missing)}"
        )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="raise",
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="raise",
    )

    if df["amount"].isna().any():
        raise ValueError("Transaction amounts cannot be empty.")

    if df["transaction_date"].isna().any():
        raise ValueError("Transaction dates cannot be empty.")

    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df["category"] = df["category"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()

    return df


# ---------------------------------------------------------
# Helper: Filter transactions by month
# ---------------------------------------------------------

def filter_by_month(
    df: pd.DataFrame,
    month: str = "",
) -> pd.DataFrame:
    """
    Filter by YYYY-MM, for example 2026-10.
    If month is empty, return all transactions.
    """

    if not month:
        return df.copy()

    try:
        pd.Period(month, freq="M")
    except ValueError as exc:
        raise ValueError(
            "Month must use YYYY-MM format, for example 2026-10."
        ) from exc

    return df[
        df["transaction_date"].dt.strftime("%Y-%m") == month
    ].copy()


# ---------------------------------------------------------
# Tool 1: Analyze spending
# ---------------------------------------------------------

@tool
def analyze_spending(month: str = "") -> dict:
    """
    Calculate income, expenses, net cash flow, and spending
    by category from S3 transactions.

    Args:
        month: Optional month in YYYY-MM format, e.g. 2026-10.
               Leave empty to analyze all available transactions.
    """

    df = filter_by_month(load_transactions(), month)

    if df.empty:
        return {
            "month": month or "all available data",
            "transaction_count": 0,
            "message": "No transactions found for this period.",
        }

    income = df.loc[df["type"] == "income", "amount"].sum()
    expenses = df.loc[df["type"] == "expense", "amount"].sum()

    expense_df = df[df["type"] == "expense"]

    category_totals = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    return {
        "month": month or "all available data",
        "transaction_count": int(len(df)),
        "income": round(float(income), 2),
        "expenses": round(float(expenses), 2),
        "net_cash_flow": round(float(income - expenses), 2),
        "spending_by_category": {
            category: round(float(amount), 2)
            for category, amount in category_totals.items()
        },
    }


# ---------------------------------------------------------
# Tool 2: Find recurring merchants
# ---------------------------------------------------------

@tool
def find_recurring_merchants(month: str = "") -> dict:
    """
    Find merchants/descriptions with multiple expense
    transactions in the selected month.

    Repeated transactions are not necessarily subscriptions
    or automatic payments.

    Args:
        month: Optional month in YYYY-MM format, e.g. 2026-10.
    """

    df = filter_by_month(load_transactions(), month)

    expenses = df[df["type"] == "expense"].copy()

    if expenses.empty:
        return {
            "month": month or "all available data",
            "recurring_merchants": [],
            "message": "No expense transactions found.",
        }

    grouped = (
        expenses.groupby("description")
        .agg(
            transaction_count=("amount", "count"),
            total_amount=("amount", "sum"),
        )
        .reset_index()
    )

    recurring = grouped[grouped["transaction_count"] >= 2]
    recurring = recurring.sort_values(
        "total_amount",
        ascending=False,
    )

    results = [
        {
            "merchant": str(row["description"]),
            "transaction_count": int(row["transaction_count"]),
            "total_amount": round(float(row["total_amount"]), 2),
        }
        for _, row in recurring.iterrows()
    ]

    return {
        "month": month or "all available data",
        "recurring_merchants": results,
        "note": (
            "Repeated transactions do not prove a subscription "
            "or automatic payment."
        ),
    }


# ---------------------------------------------------------
# Tool 3: Check budget
# ---------------------------------------------------------

@tool
def check_budget(month: str = "") -> dict:
    """
    Compare spending in each category with data/budgets.json.

    Args:
        month: Optional month in YYYY-MM format, e.g. 2026-10.
    """

    if not BUDGET_FILE.exists():
        return {
            "error": f"Budget file not found: {BUDGET_FILE}"
        }

    with open(BUDGET_FILE, "r", encoding="utf-8") as file:
        budgets = json.load(file)

    df = filter_by_month(load_transactions(), month)
    expenses = df[df["type"] == "expense"]

    if expenses.empty:
        return {
            "month": month or "all available data",
            "budget_results": [],
            "message": "No expense transactions found.",
        }

    spending = expenses.groupby("category")["amount"].sum()

    results = []

    for category, budget in budgets.items():
        actual = float(spending.get(category, 0.0))
        budget = float(budget)
        difference = actual - budget

        if difference > 0:
            status = "OVER_BUDGET"
        elif difference < 0:
            status = "UNDER_BUDGET"
        else:
            status = "ON_BUDGET"

        results.append({
            "category": category,
            "budget": round(budget, 2),
            "actual_spending": round(actual, 2),
            "difference": round(difference, 2),
            "status": status,
        })

    # Include categories that have spending but no configured budget.
    for category, actual in spending.items():
        if category not in budgets:
            results.append({
                "category": category,
                "budget": None,
                "actual_spending": round(float(actual), 2),
                "difference": None,
                "status": "BUDGET_NOT_CONFIGURED",
            })

    results.sort(
        key=lambda item: (
            item["status"] != "OVER_BUDGET",
            -(item["difference"] or 0),
        )
    )

    return {
        "month": month or "all available data",
        "budget_results": results,
    }
