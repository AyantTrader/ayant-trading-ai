import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AYANT Trading AI")
st.caption("XAUUSD Strategy Backtesting — V1")

st.divider()

# ==============================
# STRATEGY SETTINGS
# ==============================

st.subheader("⚙️ Locked V1 Rules")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Setup 1", "08:30 NY")

with col2:
    st.metric("Setup 2", "09:30 NY")

with col3:
    st.metric("Max Entries / Day", "2")

st.write("### AOX Entry Levels")
st.write("-0.21  |  -0.255  |  -0.29")

st.write("### Trade Management")
st.write("- Position 1 → SL 5.000 / TP 15.000")
st.write("- Position 2 → SL 5.000 / TP 20.000")

st.write("### Execution Rules")
st.write("""
- Maximum 1 entry at 08:30 setup
- Maximum 1 entry at 09:30 setup
- First valid AOX level touch only
- No re-entry after SL
- Maximum 2 entries per day
- Each entry contains 2 positions
""")

st.divider()

# ==============================
# DATA UPLOAD
# ==============================

st.subheader("📂 Historical XAUUSD Data")

uploaded_file = st.file_uploader(
    "1-minute XAUUSD CSV upload करें",
    type=["csv"]
)

if uploaded_file is None:

    st.info(
        "अभी कोई historical CSV upload नहीं है। "
        "Backtest engine तैयार है; data मिलने पर test चलाया जाएगा।"
    )

else:

    try:

        df = pd.read_csv(uploaded_file)

        st.success("✅ CSV successfully loaded")

        st.write("### Data Preview")
        st.dataframe(
            df.head(20),
            use_container_width=True
        )

        st.write("### Dataset")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Rows", f"{len(df):,}")

        with c2:
            st.metric("Columns", len(df.columns))

        with c3:
            st.metric(
                "Missing Values",
                int(df.isna().sum().sum())
            )

        st.write("### Available Columns")
        st.write(list(df.columns))

        # ==============================
        # COLUMN DETECTION
        # ==============================

        column_map = {}

        lower_columns = {
            str(c).lower().strip(): c
            for c in df.columns
        }

        possible_open = ["open", "o"]
        possible_high = ["high", "h"]
        possible_low = ["low", "l"]
        possible_close = ["close", "c"]

        for name in possible_open:
            if name in lower_columns:
                column_map["open"] = lower_columns[name]
                break

        for name in possible_high:
            if name in lower_columns:
                column_map["high"] = lower_columns[name]
                break

        for name in possible_low:
            if name in lower_columns:
                column_map["low"] = lower_columns[name]
                break

        for name in possible_close:
            if name in lower_columns:
                column_map["close"] = lower_columns[name]
                break

        st.write("### 🔎 OHLC Detection")

        if len(column_map) == 4:

            st.success(
                "✅ Open / High / Low / Close columns detected."
            )

            st.json(column_map)

            o = column_map["open"]
            h = column_map["high"]
            l = column_map["low"]
            c = column_map["close"]

            numeric_columns = [o, h, l, c]

            for col in numeric_columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

            df = df.dropna(
                subset=numeric_columns
            )

            st.metric(
                "Valid OHLC Rows",
                f"{len(df):,}"
            )

            # ==============================
            # BACKTEST BUTTON
            # ==============================

            st.divider()

            st.subheader("🧪 Backtest")

            if st.button(
                "▶️ Run V1 Backtest",
                type="primary"
            ):

                st.warning(
                    "Historical data successfully validated. "
                    "The full 08:30 / 09:30 AOX trade-detection "
                    "module will be connected next."
                )

                st.write("### Current Engine Status")

                st.write("✅ CSV loaded")
                st.write("✅ OHLC detected")
                st.write("✅ Numeric validation complete")
                st.write("⏳ AOX manipulation detection — next module")
                st.write("⏳ Entry detection — next module")
                st.write("⏳ SL / TP simulation — next module")
                st.write("⏳ Performance report — next module")

        else:

            st.error(
                "❌ Open / High / Low / Close columns "
                "automatically detect नहीं हो पाए।"
            )

            st.write(
                "CSV के column names ऊपर दिख रहे हैं। "
                "उन्हें देखकर अगला mapping step किया जाएगा।"
            )

    except Exception as e:

        st.error(
            f"CSV processing error: {e}"
        )

st.divider()

st.caption(
    "AYANT Trading AI • Strategy V1 • "
    "New York timezone framework"
)
