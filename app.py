import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AYANT Trading AI — XAUUSD Strategy Tester")
st.caption("Locked V1 Strategy | America/New_York")

# ============================================================
# LOCKED V1 RULES
# ============================================================

st.subheader("🔒 Locked V1 Rules")

st.markdown("""
**Timezone:** America/New_York

**Execution setups:**
- 8:30 AM NY
- 9:30 AM NY
- Maximum 1 entry per setup
- Maximum 2 entries per day

**Manipulation:**
- 8:30 setup → manipulation forming after 8:30
- 9:30 setup → manipulation forming after 9:30
- LEFT-SIDE manipulation is confirmed by a valid pullback

**Bullish valid pullback:**
- C1 = reference candle
- C2 sweeps C1 Low
- C2 does NOT close below C1 Low
- C3 closes above C1 High

**Bearish valid pullback:**
- C1 = reference candle
- C2 sweeps C1 High
- C2 does NOT close above C1 High
- C3 closes below C1 Low

**AOX entry levels:**
- -0.21
- -0.255
- -0.29

**Trade management:**
- Position 1: SL 5.000 / TP 15.000
- Position 2: SL 5.000 / TP 20.000
""")

st.divider()

# ============================================================
# CSV UPLOAD
# ============================================================

st.subheader("📂 XAUUSD 1-Minute Data")

uploaded_file = st.file_uploader(
    "Upload XAUUSD 1-minute CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info("CSV upload करो।")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV पढ़ने में error: {e}")
    st.stop()

st.success("✅ CSV loaded")

# ============================================================
# OHLC VALIDATION
# ============================================================

required_columns = ["open", "high", "low", "close"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"❌ Missing columns: {', '.join(missing_columns)}"
    )
    st.stop()

for col in required_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=required_columns
).copy()

st.success("✅ OHLC validation complete")

# ============================================================
# DATETIME VALIDATION
# ============================================================

datetime_column = None

for col in ["datetime", "timestamp", "time", "date"]:
    if col in df.columns:
        datetime_column = col
        break

if datetime_column is None:
    st.error("❌ Datetime column नहीं मिली।")
    st.stop()

# Always convert to UTC-aware datetime
df["datetime"] = pd.to_datetime(
    df[datetime_column],
    errors="coerce",
    utc=True
)

df = df.dropna(
    subset=["datetime"]
).copy()

df = df.sort_values(
    "datetime"
).reset_index(drop=True)

# ============================================================
# CHRONOLOGICAL BAR INDEX
# ============================================================
# IMPORTANT:
# We use bar_index for candle-order comparisons.
# This completely avoids timezone-aware/naive comparison issues.

df["bar_index"] = np.arange(
    len(df),
    dtype=np.int64
)

st.success("✅ Datetime validation complete")
st.success("✅ Chronological bar index created")

# ============================================================
# DATA SUMMARY
# ============================================================

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Rows",
        f"{len(df):,}"
    )

with c2:
    st.metric(
        "Start",
        df["datetime"].iloc[0].strftime(
            "%Y-%m-%d %H:%M"
        )
    )

with c3:
    st.metric(
        "End",
        df["datetime"].iloc[-1].strftime(
            "%Y-%m-%d %H:%M"
        )
    )

st.divider()

# ============================================================
# NEW YORK TIME
# ============================================================

df["ny_time"] = df["datetime"].dt.tz_convert(
    "America/New_York"
)

df["ny_date"] = df["ny_time"].dt.date
df["ny_hour"] = df["ny_time"].dt.hour
df["ny_minute"] = df["ny_time"].dt.minute

# ============================================================
# VALID PULLBACK DETECTION
# ============================================================

st.subheader("🔎 Valid Pullback Detection")

# C1 = 2 candles back
# C2 = previous candle
# C3 = current candle

c1_low = df["low"].shift(2)
c1_high = df["high"].shift(2)

c2_low = df["low"].shift(1)
c2_high = df["high"].shift(1)
c2_close = df["close"].shift(1)

c3_close = df["close"]

# ------------------------------------------------------------
# BULLISH
# ------------------------------------------------------------

bullish_mask = (
    (c2_low < c1_low) &
    (c2_close >= c1_low) &
    (c3_close > c1_high)
)

# ------------------------------------------------------------
# BEARISH
# ------------------------------------------------------------

bearish_mask = (
    (c2_high > c1_high) &
    (c2_close <= c1_high) &
    (c3_close < c1_low)
)

# ============================================================
# PULLBACK TABLE
# ============================================================

bullish_signals = pd.DataFrame({
    "bar_index": df.loc[
        bullish_mask,
        "bar_index"
    ].to_numpy(),

    "datetime": df.loc[
        bullish_mask,
        "datetime"
    ].tolist(),

    "ny_time": df.loc[
        bullish_mask,
        "ny_time"
    ].tolist(),

    "ny_date": df.loc[
        bullish_mask,
        "ny_date"
    ].tolist(),

    "direction": "BULLISH",

    "c1_high": c1_high.loc[
        bullish_mask
    ].to_numpy(),

    "c1_low": c1_low.loc[
        bullish_mask
    ].to_numpy(),

    "c2_high": c2_high.loc[
        bullish_mask
    ].to_numpy(),

    "c2_low": c2_low.loc[
        bullish_mask
    ].to_numpy(),

    "c2_close": c2_close.loc[
        bullish_mask
    ].to_numpy(),

    "c3_close": c3_close.loc[
        bullish_mask
    ].to_numpy()
})

bearish_signals = pd.DataFrame({
    "bar_index": df.loc[
        bearish_mask,
        "bar_index"
    ].to_numpy(),

    "datetime": df.loc[
        bearish_mask,
        "datetime"
    ].tolist(),

    "ny_time": df.loc[
        bearish_mask,
        "ny_time"
    ].tolist(),

    "ny_date": df.loc[
        bearish_mask,
        "ny_date"
    ].tolist(),

    "direction": "BEARISH",

    "c1_high": c1_high.loc[
        bearish_mask
    ].to_numpy(),

    "c1_low": c1_low.loc[
        bullish_mask
    ].to_numpy(),

    "c2_high": c2_high.loc[
        bearish_mask
    ].to_numpy(),

    "c2_low": c2_low.loc[
        bearish_mask
    ].to_numpy(),

    "c2_close": c2_close.loc[
        bearish_mask
    ].to_numpy(),

    "c3_close": c3_close.loc[
        bearish_mask
    ].to_numpy()
})

pullbacks = pd.concat(
    [
        bullish_signals,
        bearish_signals
    ],
    ignore_index=True
)

pullbacks = pullbacks.sort_values(
    "bar_index"
).reset_index(drop=True)

total_pullbacks = len(pullbacks)

bullish_count = int(
    bullish_mask.sum()
)

bearish_count = int(
    bearish_mask.sum()
)

p1, p2, p3 = st.columns(3)

with p1:
    st.metric(
        "Total Valid Pullbacks",
        f"{total_pullbacks:,}"
    )

with p2:
    st.metric(
        "Bullish",
        f"{bullish_count:,}"
    )

with p3:
    st.metric(
        "Bearish",
        f"{bearish_count:,}"
    )

st.success(
    f"✅ {total_pullbacks:,} Valid Pullbacks detected"
)

st.dataframe(
    pullbacks.head(100),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# SETUP DETECTION
# ============================================================

st.divider()

st.subheader(
    "⏰ 8:30 / 9:30 NY Setup Detection"
)

setup_mask = (
    (
        (df["ny_hour"] == 8) &
        (df["ny_minute"] == 30)
    )
    |
    (
        (df["ny_hour"] == 9) &
        (df["ny_minute"] == 30)
    )
)

setups = df.loc[
    setup_mask,
    [
        "bar_index",
        "datetime",
        "ny_time",
        "ny_date",
        "open",
        "high",
        "low",
        "close"
    ]
].copy()

setups["setup_time"] = (
    setups["ny_time"]
    .dt.strftime("%H:%M")
)

st.metric(
    "Total 8:30 / 9:30 Setup Candles",
    f"{len(setups):,}"
)

st.dataframe(
    setups.head(100),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# SETUP → AFTER-SETUP PULLBACK
# ============================================================

st.divider()

st.subheader(
    "🔗 Setup → After-Setup Valid Pullback"
)

if len(setups) == 0:

    st.warning(
        "⚠️ Dataset में 8:30 या 9:30 NY setup candle नहीं मिली।"
    )

else:

    setup_records = []

    for _, setup in setups.iterrows():

        setup_date = setup["ny_date"]

        # Use integer bar index.
        # No datetime comparison is performed here.
        setup_bar_index = int(
            setup["bar_index"]
        )

        candidates = pullbacks[
            (pullbacks["ny_date"] == setup_date)
            &
            (pullbacks["bar_index"] > setup_bar_index)
        ]

        if len(candidates) == 0:
            continue

        # First valid pullback after setup
        first_candidate = candidates.iloc[0]

        setup_records.append({
            "setup_datetime":
                setup["datetime"],

            "setup_ny_time":
                setup["ny_time"],

            "setup_type":
                setup["setup_time"],

            "pullback_datetime":
                first_candidate["datetime"],

            "pullback_ny_time":
                first_candidate["ny_time"],

            "direction":
                first_candidate["direction"],

            "c1_high":
                first_candidate["c1_high"],

            "c1_low":
                first_candidate["c1_low"],

            "c2_high":
                first_candidate["c2_high"],

            "c2_low":
                first_candidate["c2_low"],

            "c2_close":
                first_candidate["c2_close"],

            "c3_close":
                first_candidate["c3_close"]
        })

    setup_pullbacks = pd.DataFrame(
        setup_records
    )

    if len(setup_pullbacks) == 0:

        st.warning(
            "⚠️ किसी setup के बाद same NY day में "
            "valid pullback नहीं मिला।"
        )

    else:

        setup_pullbacks = (
            setup_pullbacks
            .sort_values("setup_datetime")
            .reset_index(drop=True)
        )

        st.success(
            f"✅ {len(setup_pullbacks):,} "
            "setup → after-setup pullback candidates found"
        )

        s1, s2, s3 = st.columns(3)

        with s1:

            count_830 = int(
                (
                    setup_pullbacks["setup_type"]
                    == "08:30"
                ).sum()
            )

            st.metric(
                "8:30 Candidates",
                count_830
            )

        with s2:

            count_930 = int(
                (
                    setup_pullbacks["setup_type"]
                    == "09:30"
                ).sum()
            )

            st.metric(
                "9:30 Candidates",
                count_930
            )

        with s3:

            bull = int(
                (
                    setup_pullbacks["direction"]
                    == "BULLISH"
                ).sum()
            )

            bear = int(
                (
                    setup_pullbacks["direction"]
                    == "BEARISH"
                ).sum()
            )

            st.metric(
                "Bullish / Bearish",
                f"{bull} / {bear}"
            )

        st.dataframe(
            setup_pullbacks.head(100),
            use_container_width=True,
            hide_index=True
        )

        st.info(
            "ℹ️ यह अभी candidate association है। "
            "कोई artificial fixed time-window नहीं लगाया गया है। "
            "अगले चरण में confirmed manipulation leg पर AOX calculation होगी।"
        )

# ============================================================
# AOX
# ============================================================

st.divider()

st.subheader("📐 AOX Configuration")

AOX_ENTRY_LEVELS = [
    -0.21,
    -0.255,
    -0.29
]

AOX_REFERENCE_LEVELS = [
    2.56,
    2.60,
    2.64
]

a1, a2 = st.columns(2)

with a1:
    st.write("**AOX Entry Levels**")
    st.write(AOX_ENTRY_LEVELS)

with a2:
    st.write("**AOX Reference Levels**")
    st.write(AOX_REFERENCE_LEVELS)

# ============================================================
# TRADE MANAGEMENT
# ============================================================

st.divider()

st.subheader("🎯 Trade Management")

t1, t2 = st.columns(2)

with t1:
    st.write("**Position 1**")
    st.write("SL = 5.000")
    st.write("TP = 15.000")
    st.write("Result = +3R at TP / -1R at SL")

with t2:
    st.write("**Position 2**")
    st.write("SL = 5.000")
    st.write("TP = 20.000")
    st.write("Result = +4R at TP / -1R at SL")

# ============================================================
# BACKTEST BUTTON
# ============================================================

st.divider()

st.subheader("🚀 V1 Backtest")

run_backtest = st.button(
    "▶️ Run V1 Backtest",
    type="primary",
    use_container_width=True
)

if run_backtest:

    st.info(
        "Complete V1 backtest engine अभी development में है।"
    )

    st.write("### Current Pipeline")

    st.success("✅ CSV Data")
    st.success("✅ OHLC / Datetime Validation")
    st.success("✅ Valid Pullback Detection")
    st.success("✅ 8:30 / 9:30 Setup Detection")
    st.success("✅ Setup → After-Setup Pullback Association")

    st.warning(
        "⏳ LEFT-SIDE Manipulation Leg — exact objective rule"
    )

    st.warning(
        "⏳ AOX Fibonacci Calculation"
    )

    st.warning(
        "⏳ First AOX Entry Detection"
    )

    st.warning(
        "⏳ SL / TP Simulation"
    )

    st.warning(
        "⏳ Performance Report"
    )

st.caption(
    "AYANT Trading AI — V1 Strategy Tester"
)
