import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AYANT Trading AI")
st.caption("XAUUSD Strategy Backtesting — V1")

st.divider()

st.subheader("📂 Historical XAUUSD Data")

uploaded_file = st.file_uploader(
    "1-minute XAUUSD CSV upload करो",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        st.success("CSV successfully loaded!")

        st.write("### Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        st.write("### Dataset Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Rows", f"{len(df):,}")

        with col2:
            st.metric("Columns", len(df.columns))

        with col3:
            st.metric("Missing Values", int(df.isna().sum().sum()))

        st.write("### Columns")
        st.write(list(df.columns))

    except Exception as e:
        st.error(f"CSV read error: {e}")

else:
    st.info("पहले अपना XAUUSD historical CSV upload करो।")

st.divider()

st.subheader("⚙️ Strategy V1")

st.write("""
**Execution Windows**
- 8:30 AM New York
- 9:30 AM New York

**AOX Entry Levels**
- -0.21
- -0.255
- -0.29

**Trade Management**
- Trade 1: SL 5.000 / TP 15.000
- Trade 2: SL 5.000 / TP 20.000

**Maximum**
- 1 entry per setup
- Maximum 2 entries per day
- 2 positions per entry
""")

st.warning(
    "⚠️ अभी backtest calculation engine नहीं लगाया गया है। "
    "यह version केवल CSV upload और data validation करता है।"
)
