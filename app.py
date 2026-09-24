import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# VALID PULLBACK DETECTION
# =========================================================

def detect_valid_pullbacks(df):

    signals = []

    for i in range(2, len(df)):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        # -------------------------------------------------
        # BULLISH VALID PULLBACK
        #
        # C2 sweeps C1 Low
        # C2 does NOT close below C1 Low
        # C3 closes above C1 High
        # -------------------------------------------------

        bullish = (
            c2["low"] < c1["low"]
            and c2["close"] >= c1["low"]
            and c3["close"] > c1["high"]
        )

        # -------------------------------------------------
        # BEARISH VALID PULLBACK
        #
        # C2 sweeps C1 High
        # C2 does NOT close above C1 High
        # C3 closes below C1 Low
        # -------------------------------------------------

        bearish = (
            c2["high"] > c1["high"]
            and c2["close"] <= c1["high"]
            and c3["close"] < c1["low"]
        )

        if bullish:

            signals.append({
                "index": i,
                "direction": "bullish",
                "c1_high": c1["high"],
                "c1_low": c1["low"],
                "c2_high": c2["high"],
                "c2_low": c2["low"],
                "confirmation_close": c3["close"]
            })

        elif bearish:

            signals.append({
                "index": i,
                "direction": "bearish",
                "c1_high": c1["high"],
                "c1_low": c1["low"],
                "c2_high": c2["high"],
                "c2_low": c2["low"],
                "confirmation_close": c3["close"]
            })

    return signals


# =========================================================
# AOX LEVEL CALCULATION
# =========================================================

AOX_LEVELS = [
    0,
    1,
    -0.21,
    -0.255,
    -0.29,
    1.47,
    1.55,
    2.56,
    2.60,
    2.64
]

AOX_ENTRY_LEVELS = [
    -0.21,
    -0.255,
    -0.29
]


def calculate_aox_levels(high_price, low_price, direction):

    price_range = abs(high_price - low_price)

    levels = {}

    if direction == "bullish":

        # Bullish orientation: High → Low
        start = high_price
        end = low_price

    else:

        # Bearish orientation: Low → High
        start = low_price
        end = high_price

    for fib in AOX_LEVELS:

        price = start + ((end - start) * fib)

        levels[fib] = price

    return levels


# =========================================================
# AOX FIRST TOUCH DETECTION
# =========================================================

def detect_aox_touch(candle, aox_levels):

    touched = []

    for level in AOX_ENTRY_LEVELS:

        if level not in aox_levels:
            continue

        price = aox_levels[level]

        if candle["low"] <= price <= candle["high"]:

            touched.append(level)

    # No AOX level touched
    if len(touched) == 0:
        return None, "NO_TOUCH"

    # More than one level touched inside same candle
    # Intrabar order cannot be known from OHLC
    if len(touched) > 1:
        return None, "AMBIGUOUS"

    # Exactly one level touched
    return touched[0], "VALID"


# =========================================================
# TRADE LEVELS
# =========================================================

SL_DISTANCE = 5.000
TP1_DISTANCE = 15.000
TP2_DISTANCE = 20.000


def calculate_trade_levels(entry_price, direction):

    if direction == "bullish":

        sl = entry_price - SL_DISTANCE
        tp1 = entry_price + TP1_DISTANCE
        tp2 = entry_price + TP2_DISTANCE

    else:

        sl = entry_price + SL_DISTANCE
        tp1 = entry_price - TP1_DISTANCE
        tp2 = entry_price - TP2_DISTANCE

    return sl, tp1, tp2


# =========================================================
# APP UI
# =========================================================

st.title("📊 AYANT Trading AI")

st.caption(
    "XAUUSD — Strategy Backtesting Engine"
)

st.divider()


# =========================================================
# LOCKED V1 RULES
# =========================================================

st.subheader("🔒 Locked V1 Rules")

rules = {

    "Timezone":
        "America/New_York",

    "Setups":
        "8:30 NY और 9:30 NY",

    "Manipulation":
        "Setup time के बाद वाली LEFT-SIDE manipulation leg",

    "Manipulation Confirmation":
        "Valid Pullback बनने पर manipulation leg confirm",

    "Bullish Valid Pullback":
        "C2 → C1 Low sweep, C2 नीचे close नहीं, C3 → C1 High के ऊपर close",

    "Bearish Valid Pullback":
        "C2 → C1 High sweep, C2 ऊपर close नहीं, C3 → C1 Low के नीचे close",

    "Bullish AOX":
        "High → Low",

    "Bearish AOX":
        "Low → High",

    "AOX Entry":
        "-0.21 / -0.255 / -0.29",

    "AOX Entry Rule":
        "पहला unambiguous touch",

    "Ambiguous Candle":
        "एक candle में multiple entry levels → trade नहीं",

    "Position 1":
        "SL 5.000 / TP 15.000",

    "Position 2":
        "SL 5.000 / TP 20.000"
}


for key, value in rules.items():

    st.write(
        f"**{key}:** {value}"
    )


st.divider()


# =========================================================
# CSV UPLOAD
# =========================================================

st.subheader("📁 Historical XAUUSD Data")

uploaded_file = st.file_uploader(
    "1-minute XAUUSD CSV upload करें",
    type=["csv"]
)


if uploaded_file is not None:

    try:

        df = pd.read_csv(
            uploaded_file
        )

        st.success(
            "✅ CSV loaded"
        )


        # -------------------------------------------------
        # NORMALIZE COLUMN NAMES
        # -------------------------------------------------

        df.columns = [
            str(col).strip().lower()
            for col in df.columns
        ]


        # -------------------------------------------------
        # OHLC CHECK
        # -------------------------------------------------

        required = [
            "open",
            "high",
            "low",
            "close"
        ]

        missing = [
            col
            for col in required
            if col not in df.columns
        ]


        if missing:

            st.error(
                f"❌ Missing OHLC columns: {missing}"
            )

            st.stop()


        # -------------------------------------------------
        # NUMERIC VALIDATION
        # -------------------------------------------------

        for col in required:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )


        invalid_rows = (
            df[required]
            .isna()
            .any(axis=1)
            .sum()
        )


        if invalid_rows > 0:

            st.warning(
                f"⚠️ {invalid_rows} rows में invalid OHLC values मिलीं।"
            )

            df = df.dropna(
                subset=required
            )


        st.success(
            "✅ OHLC validation complete"
        )


        # -------------------------------------------------
        # DATETIME DETECTION
        # -------------------------------------------------

        datetime_candidates = [
            "datetime",
            "date",
            "time",
            "timestamp"
        ]

        datetime_column = None


        for col in datetime_candidates:

            if col in df.columns:

                datetime_column = col

                break


        if datetime_column is None:

            st.error(
                "❌ Datetime column नहीं मिला।"
            )

            st.stop()


        # -------------------------------------------------
        # DATETIME CONVERSION
        # -------------------------------------------------

        df[datetime_column] = pd.to_datetime(
            df[datetime_column],
            errors="coerce"
        )


        df = df.dropna(
            subset=[datetime_column]
        )


        df = (
            df
            .sort_values(datetime_column)
            .reset_index(drop=True)
        )


        st.success(
            "✅ Datetime validation complete"
        )


        # -------------------------------------------------
        # DATA SUMMARY
        # -------------------------------------------------

        st.write(
            f"**Rows:** {len(df):,}"
        )


        st.write(
            f"**Data range:** "
            f"{df[datetime_column].min()} → "
            f"{df[datetime_column].max()}"
        )


        st.divider()


        # =================================================
        # VALID PULLBACK SCAN
        # =================================================

        st.subheader(
            "🔎 Valid Pullback Detection"
        )


        pullbacks = detect_valid_pullbacks(
            df
        )


        bullish_count = sum(
            1
            for x in pullbacks
            if x["direction"] == "bullish"
        )


        bearish_count = sum(
            1
            for x in pullbacks
            if x["direction"] == "bearish"
        )


        col1, col2, col3 = st.columns(3)


        col1.metric(
            "Total Valid Pullbacks",
            len(pullbacks)
        )


        col2.metric(
            "Bullish",
            bullish_count
        )


        col3.metric(
            "Bearish",
            bearish_count
        )


        # -------------------------------------------------
        # SHOW LAST SIGNALS
        # -------------------------------------------------

        if len(pullbacks) > 0:

            display_data = []

            for signal in pullbacks[-20:]:

                idx = signal["index"]

                display_data.append({

                    "Candle Index":
                        idx,

                    "Direction":
                        signal["direction"],

                    "C1 High":
                        signal["c1_high"],

                    "C1 Low":
                        signal["c1_low"],

                    "C2 High":
                        signal["c2_high"],

                    "C2 Low":
                        signal["c2_low"],

                    "Confirmation Close":
                        signal["confirmation_close"]
                })


            signal_df = pd.DataFrame(
                display_data
            )


            st.dataframe(
                signal_df,
                use_container_width=True
            )


        else:

            st.info(
                "इस dataset में अभी कोई valid pullback नहीं मिला।"
            )


        st.divider()


        # =================================================
        # BACKTEST ENGINE
        # =================================================

        st.subheader(
            "⚙️ Backtest Engine"
        )


        if st.button(
            "▶️ Run V1 Backtest",
            type="primary"
        ):

            st.info(
                "⏳ Full historical execution engine "
                "अगले module में connect किया जाएगा।"
            )


            st.write(
                "✅ CSV processing"
            )

            st.write(
                "✅ OHLC validation"
            )

            st.write(
                "✅ Valid Pullback detection"
            )

            st.write(
                "⏳ LEFT-SIDE manipulation filtering"
            )

            st.write(
                "⏳ AOX entry execution"
            )

            st.write(
                "⏳ SL / TP simulation"
            )

            st.write(
                "⏳ Performance report"
            )


    except Exception as e:

        st.error(
            f"❌ CSV processing error: {e}"
        )


else:

    st.info(
        "ऊपर अपना XAUUSD 1-minute CSV upload करें।"
    )
