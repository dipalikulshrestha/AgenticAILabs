
import os
from io import BytesIO

import boto3
import pandas as pd
import plotly.express as px
import streamlit as st

from strands import Agent
from strands.models import BedrockModel

from tools.finance_tools import (
    analyze_spending,
    find_recurring_merchants,
    check_budget,
)


# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SpendWise AI",
    page_icon="💰",
    layout="wide",
)

MODEL_ID = (
    "arn:aws:bedrock:us-east-1:167771397877:"
    "inference-profile/us.amazon.nova-2-lite-v1:0"
)

S3_BUCKET = os.environ.get("SPENDWISE_S3_BUCKET")
S3_KEY = os.environ.get(
    "SPENDWISE_S3_KEY",
    "transactions/spendwise_demo_transactions.csv",
)
S3_REGION = os.environ.get("AWS_REGION", "ap-south-1")

REQUIRED_COLUMNS = {
    "transaction_date",
    "description",
    "category",
    "amount",
    "type",
}

SYSTEM_PROMPT = """
You are SpendWise, an AI personal finance assistant.

You analyze only transaction data available through
your registered tools.

Rules:
- Use analyze_spending for spending questions.
- Use find_recurring_merchants for repeated merchants.
- Use check_budget for budget questions.
- When a month is specified, pass it as YYYY-MM.
- Use tools for numerical calculations. Never invent totals.
- Explain the evidence behind recommendations.
- Repeated charges do not prove subscriptions or
  automatic payments.
- Do not claim a purchase is affordable with certainty.
- Do not provide investment, tax, lending, or legal advice.
- Do not request bank passwords or authentication secrets.
- Be concise, transparent, and practical.
"""

# S3 client uses the configured bucket region.
s3 = boto3.client("s3", region_name=S3_REGION)


# =========================================================
# 2. CREATE A STRANDS AGENT FOR THIS STREAMLIT SESSION
# =========================================================

def create_agent():
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name="us-east-1",
    )

    return Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[
            analyze_spending,
            find_recurring_merchants,
            check_budget,
        ],
    )


if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# 3. HELPERS
# =========================================================

def validate_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the uploaded transaction CSV."""

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df = df.copy()

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="raise",
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="raise",
    )

    if df["transaction_date"].isna().any():
        raise ValueError("Transaction dates cannot be empty.")

    if df["amount"].isna().any():
        raise ValueError("Transaction amounts cannot be empty.")

    if (df["amount"] < 0).any():
        raise ValueError("Amounts must be non-negative.")

    df["type"] = (
        df["type"].astype(str).str.strip().str.lower()
    )

    if not df["type"].isin(["income", "expense"]).all():
        raise ValueError(
            "The type column must contain income or expense."
        )

    for column in ["description", "category"]:
        if df[column].isna().any():
            raise ValueError(
                f"{column} cannot contain empty values."
            )

        df[column] = df[column].astype(str).str.strip()

        if (df[column] == "").any():
            raise ValueError(
                f"{column} cannot contain empty values."
            )

    return df


def load_transactions_from_s3() -> pd.DataFrame:
    """Always read the current CSV object from S3."""

    if not S3_BUCKET:
        raise ValueError(
            "Set the SPENDWISE_S3_BUCKET environment variable."
        )

    response = s3.get_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
    )

    csv_bytes = response["Body"].read()

    df = pd.read_csv(BytesIO(csv_bytes))

    return validate_transactions(df)


def extract_agent_text(result) -> str:
    """Extract readable text from a Strands agent result."""

    message = getattr(result, "message", None)

    if isinstance(message, dict):
        content = message.get("content", [])

        text_blocks = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("text")
        ]

        if text_blocks:
            return "\n".join(text_blocks)

    return str(result)


# =========================================================
# 4. APPLICATION HEADER
# =========================================================

st.title("💰 SpendWise — AI Personal Finance Agent")

st.caption(
    "Understand your spending. Find patterns. Plan smarter."
)

st.info(
    "Demo only: use synthetic transactions. "
    "Insights are estimates, not financial advice."
)


# =========================================================
# 5. SIDEBAR: UPLOAD CSV TO S3 / REFRESH FROM S3
# =========================================================

with st.sidebar:
    st.header("Transaction data")

    st.caption("S3 is the source of truth for this application.")

    st.text(f"Bucket: {S3_BUCKET or 'Not configured'}")
    st.text(f"Object: {S3_KEY}")

    uploaded = st.file_uploader(
        "Select transaction CSV",
        type=["csv"],
        key="transaction_uploader",
    )

    if st.button(
        "Upload CSV to S3",
        disabled=(uploaded is None or not S3_BUCKET),
        use_container_width=True,
    ):
        try:
            candidate = pd.read_csv(uploaded)
            candidate = validate_transactions(candidate)

            csv_bytes = candidate.to_csv(
                index=False
            ).encode("utf-8")

            s3.put_object(
                Bucket=S3_BUCKET,
                Key=S3_KEY,
                Body=csv_bytes,
                ContentType="text/csv",
            )

            # Remove old conversation context after changing datasets.
            st.session_state.messages = []
            st.session_state.pop("agent", None)

            st.success(
                f"Uploaded {len(candidate)} transactions to S3."
            )

            st.rerun()

        except Exception as exc:
            st.error(f"Upload failed: {exc}")

    if st.button(
        "Refresh data from S3",
        use_container_width=True,
    ):
        # Force the dashboard to rerun and read S3 again.
        st.rerun()

    if st.button(
        "Clear chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.pop("agent", None)
        st.rerun()


# =========================================================
# 6. LOAD CURRENT TRANSACTIONS FROM S3
# =========================================================

try:
    df = load_transactions_from_s3()

except Exception as exc:
    st.error(
        "Could not load transactions from S3. "
        "Check your bucket, object key, AWS credentials, "
        "and S3 permissions."
    )

    with st.expander("Technical details"):
        st.code(str(exc))

    st.stop()


if df.empty:
    st.warning("The S3 CSV contains no transactions.")
    st.stop()


st.caption(
    f"Data source: Amazon S3 | "
    f"Loaded {len(df)} transactions | "
    f"Object: {S3_KEY}"
)


# =========================================================
# 7. DASHBOARD FILTER
# =========================================================

months = sorted(
    df["transaction_date"].dt.strftime("%Y-%m").unique(),
    reverse=True,
)

selected_month = st.selectbox(
    "Select month",
    options=months,
)

view = df[
    df["transaction_date"].dt.strftime("%Y-%m")
    == selected_month
].copy()


# =========================================================
# 8. SUMMARY METRICS
# =========================================================

income = view.loc[
    view["type"] == "income", "amount"
].sum()

expenses = view.loc[
    view["type"] == "expense", "amount"
].sum()

net_cash_flow = income - expenses

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Income",
    f"₹{income:,.0f}",
)

col2.metric(
    "Expenses",
    f"₹{expenses:,.0f}",
)

col3.metric(
    "Net cash flow",
    f"₹{net_cash_flow:,.0f}",
)

col4.metric(
    "Transactions",
    f"{len(view):,}",
)


# =========================================================
# 9. SPENDING CHART
# =========================================================

st.subheader(f"Spending breakdown — {selected_month}")

expenses_df = view[view["type"] == "expense"]

if expenses_df.empty:
    st.info("No expenses found for this month.")

else:
    category_totals = (
        expenses_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_bar = px.bar(
            category_totals,
            x="category",
            y="amount",
            title="Expenses by category",
            labels={
                "category": "Category",
                "amount": "Amount (₹)",
            },
        )

        st.plotly_chart(
            fig_bar,
            use_container_width=True,
        )

    with chart_col2:
        fig_pie = px.pie(
            category_totals,
            names="category",
            values="amount",
            title="Share of expenses",
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True,
        )


# =========================================================
# 10. TRANSACTION TABLE
# =========================================================

with st.expander("View transactions for selected month"):
    st.dataframe(
        view.sort_values(
            "transaction_date",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 11. STRAND AGENT CHAT
# =========================================================

st.divider()

st.subheader("💬 Ask SpendWise")

st.caption(
    "Try: Which categories exceeded my budget in October 2026?"
)

# Display previous conversation messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept a new user question.
if prompt := st.chat_input(
    "Ask about your transactions, spending, or budget..."
):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(
            "Analyzing your transactions..."
        ):
            try:
                # The agent's tools independently read the latest
                # S3 object when they are invoked.
                result = st.session_state.agent(prompt)
                answer = extract_agent_text(result)

            except Exception:
                answer = (
                    "I couldn't complete that analysis. "
                    "Please check the Bedrock configuration, "
                    "S3 permissions, and application logs."
                )

            st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )
