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

st.divider()

# ============================================================
# LOCKED V1 RULES
# ============================================================

st.subheader("🔒 Locked V1 Rules")

st.markdown("""
**Timezone:** America/New_York

**Execution Times:**
- 8:30 AM NY
- 9:30 AM NY
- Maximum 1 entry per setup
- Maximum 2 entries per day

**Valid Pullback — Bullish:**
- C1 = reference candle
- C2 sweeps C1 Low
- C2 does NOT close below C1 Low
- C3 closes above C1 High

**Valid Pullback — Bearish:**
- C1 = reference candle
- C2 sweeps C1 High
- C2 does NOT close above C1 High
- C3 closes below C1 Low

**AOX Entry Levels:**
- -0.21
- -0.255
- -0.29

**Trade Management:**
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
    st.info("CSV upload करो ताकि backtest शुरू किया जा सके।")
    st.stop()

# ============================================================
# LOAD CSV
# ============================================================

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV पढ़ने में error आया: {e}")
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

st.success("✅ OHLC validation complete")

# ============================================================
# NUMERIC CONVERSION
# ============================================================

for col in required_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

invalid_numeric = df[required_columns].isna().any(axis=1).sum()

if invalid_numeric > 0:
    st.warning(
        f"⚠️ {invalid_numeric} rows में invalid OHLC values मिलीं। "
        "इन rows को remove किया जा रहा है।"
    )

df = df.dropna(subset=required_columns).copy()

# ============================================================
# DATETIME
# ============================================================

datetime_column = None

for col in ["datetime", "timestamp", "time", "date"]:
    if col in df.columns:
        datetime_column = col
        break

if datetime_column is None:
    st.error(
        "❌ Datetime column नहीं मिली। "
        "Expected: datetime / timestamp / time / date"
    )
    st.stop()

df["datetime"] = pd.to_datetime(
    df[datetime_column],
    errors="coerce",
    utc=True
)

invalid_datetime = df["datetime"].isna().sum()

if invalid_datetime > 0:
    st.warning(
        f"⚠️ {invalid_datetime} invalid datetime rows हटाई गईं।"
    )
    df = df.dropna(subset=["datetime"]).copy()

df = df.sort_values("datetime").reset_index(drop=True)

st.success("✅ Datetime validation complete")

# ============================================================
# DATA SUMMARY
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Rows", f"{len(df):,}")

with col2:
    if len(df) > 0:
        st.metric(
            "Start",
            df["datetime"].iloc[0].strftime("%Y-%m-%d %H:%M")
        )

with col3:
    if len(df) > 0:
        st.metric(
            "End",
            df["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M")
        )

st.divider()

# ============================================================
# VALID PULLBACK DETECTION
# VECTORISED — FAST
# ============================================================

st.subheader("🔎 Valid Pullback Detection")

with st.spinner("Valid Pullbacks detect कर रही हूँ..."):

    # C1 = 2 candles back
    # C2 = previous candle
    # C3 = current candle

    c1_low = df["low"].shift(2)
    c1_high = df["high"].shift(2)

    c2_low = df["low"].shift(1)
    c2_high = df["high"].shift(1)
    c2_close = df["close"].shift(1)

    c3_close = df["close"]

    # --------------------------------------------------------
    # BULLISH VALID PULLBACK
    # --------------------------------------------------------

    bullish_mask = (
        (c2_low < c1_low) &
        (c2_close >= c1_low) &
        (c3_close > c1_high)
    )

    # --------------------------------------------------------
    # BEARISH VALID PULLBACK
    # --------------------------------------------------------

    bearish_mask = (
        (c2_high > c1_high) &
        (c2_close <= c1_high) &
        (c3_close < c1_low)
    )

    # --------------------------------------------------------
    # BUILD SIGNAL TABLE
    # --------------------------------------------------------

    bullish_signals = pd.DataFrame({
        "datetime": df.loc[bullish_mask, "datetime"].values,
        "direction": "BULLISH",
        "c1_high": c1_high.loc[bullish_mask].values,
        "c1_low": c1_low.loc[bullish_mask].values,
        "c2_high": c2_high.loc[bullish_mask].values,
        "c2_low": c2_low.loc[bullish_mask].values,
        "c2_close": c2_close.loc[bullish_mask].values,
        "c3_close": c3_close.loc[bullish_mask].values,
    })

    bearish_signals = pd.DataFrame({
        "datetime": df.loc[bearish_mask, "datetime"].values,
        "direction": "BEARISH",
        "c1_high": c1_high.loc[bearish_mask].values,
        "c1_low": c1_low.loc[bearish_mask].values,
        "c2_high": c2_high.loc[bearish_mask].values,
        "c2_low": c2_low.loc[bearish_mask].values,
        "c2_close": c2_close.loc[bearish_mask].values,
        "c3_close": c3_close.loc[bearish_mask].values,
    })

    pullbacks = pd.concat(
        [bullish_signals, bearish_signals],
        ignore_index=True
    )

    pullbacks = pullbacks.sort_values(
        "datetime"
    ).reset_index(drop=True)

# ============================================================
# PULLBACK METRICS
# ============================================================

total_pullbacks = len(pullbacks)
bullish_count = int(bullish_mask.sum())
bearish_count = int(bearish_mask.sum())

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

if total_pullbacks == 0:
    st.warning(
        "⚠️ इस dataset में कोई Valid Pullback नहीं मिला।"
    )
else:
    st.success(
        f"✅ {total_pullbacks:,} Valid Pullbacks detected"
    )

    st.dataframe(
        pullbacks.head(100),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ============================================================
# AOX LEVELS
# ============================================================

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

col_a, col_b = st.columns(2)

with col_a:
    st.write("**Entry Levels**")
    st.write(AOX_ENTRY_LEVELS)

with col_b:
    st.write("**Reference / Target Levels**")
    st.write(AOX_REFERENCE_LEVELS)

st.divider()

# ============================================================
# TRADE MANAGEMENT
# ============================================================

st.subheader("🎯 Trade Management")

t1, t2 = st.columns(2)

with t1:
    st.write("**Position 1**")
    st.write("SL = 5.000")
    st.write("TP = 15.000")
    st.write("Risk/Reward = 1:3")

with t2:
    st.write("**Position 2**")
    st.write("SL = 5.000")
    st.write("TP = 20.000")
    st.write("Risk/Reward = 1:4")

st.divider()

# ============================================================
# BACKTEST BUTTON
# ============================================================

st.subheader("🚀 V1 Backtest")

run_backtest = st.button(
    "▶️ Run V1 Backtest",
    type="primary",
    use_container_width=True
)

if run_backtest:

    st.info(
        "V1 backtest engine अभी development में है। "
        "Valid Pullback Detection module successfully तैयार है।"
    )

    st.write("### Current Pipeline")

    st.success("✅ CSV Data")
    st.success("✅ Datetime / OHLC Validation")
    st.success("✅ Vectorized Valid Pullback Detection")
    st.warning("⏳ LEFT-SIDE Manipulation Leg Detection — Next Module")
    st.warning("⏳ AOX Calculation — Next Module")
    st.warning("⏳ AOX Entry Detection — Next Module")
    st.warning("⏳ SL / TP Simulation — Next Module")
    st.warning("⏳ Performance Report — Next Module")

st.caption(
    "AYANT Trading AI — V1 Strategy Tester"
)
