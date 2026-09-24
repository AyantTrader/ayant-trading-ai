import streamlit as st
import pandas as pd
import numpy as np

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AYANT Trading AI")
st.subheader("XAUUSD 1-Minute Strategy Tester")

# ============================================================
# CONSTANTS
# ============================================================

NY_TZ = "America/New_York"

SETUP_TIMES = {
    "08:30": (8, 30),
    "09:30": (9, 30),
}

# ============================================================
# AOX CONFIGURATION
# ============================================================

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
    2.64,
]

AOX_ENTRY_LEVELS = [
    -0.21,
    -0.255,
    -0.29,
]

AOX_REFERENCE_LEVELS = [
    2.56,
    2.60,
    2.64,
]

# ============================================================
# TRADE MANAGEMENT
# ============================================================

TRADE_1_SL = 5.000
TRADE_1_TP = 15.000

TRADE_2_SL = 5.000
TRADE_2_TP = 20.000

# ============================================================
# HELPERS
# ============================================================

def find_column(df, names):
    lower_map = {str(c).strip().lower(): c for c in df.columns}

    for name in names:
        key = name.strip().lower()
        if key in lower_map:
            return lower_map[key]

    return None


def normalize_datetime(series):
    dt = pd.to_datetime(series, errors="coerce")

    if dt.isna().all():
        return None

    # If timezone-naive, assume UTC because XAUUSD CSV timestamps
    # are treated as UTC before converting to New York.
    if getattr(dt.dt, "tz", None) is None:
        dt = dt.dt.tz_localize("UTC")

    return dt.dt.tz_convert(NY_TZ)


def validate_ohlc(df):
    required = ["open", "high", "low", "close"]

    for col in required:
        if col not in df.columns:
            return False, f"Missing required column: {col}"

    return True, "OHLC validation complete"


# ============================================================
# FILE UPLOAD
# ============================================================

st.markdown("## 📂 XAUUSD 1-Minute Data")

uploaded_file = st.file_uploader(
    "Upload XAUUSD 1-minute CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Upload your XAUUSD 1-minute CSV to begin.")
    st.stop()

# ============================================================
# LOAD DATA
# ============================================================

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV loading failed: {e}")
    st.stop()

# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

datetime_col = find_column(
    df,
    ["datetime", "date", "time", "timestamp"]
)

open_col = find_column(df, ["open"])
high_col = find_column(df, ["high"])
low_col = find_column(df, ["low"])
close_col = find_column(df, ["close"])
volume_col = find_column(df, ["volume", "vol"])

if datetime_col is None:
    st.error("Datetime column not found.")
    st.stop()

if open_col is None or high_col is None or low_col is None or close_col is None:
    st.error("One or more OHLC columns are missing.")
    st.stop()

# ============================================================
# BUILD STANDARD DATAFRAME
# ============================================================

data = pd.DataFrame()

data["datetime"] = normalize_datetime(df[datetime_col])

if data["datetime"].isna().all():
    st.error("Datetime validation failed.")
    st.stop()

data["open"] = pd.to_numeric(df[open_col], errors="coerce")
data["high"] = pd.to_numeric(df[high_col], errors="coerce")
data["low"] = pd.to_numeric(df[low_col], errors="coerce")
data["close"] = pd.to_numeric(df[close_col], errors="coerce")

if volume_col is not None:
    data["volume"] = pd.to_numeric(df[volume_col], errors="coerce")
else:
    data["volume"] = np.nan

# ============================================================
# CLEAN DATA
# ============================================================

data = data.dropna(
    subset=["datetime", "open", "high", "low", "close"]
).copy()

data = data.sort_values("datetime").drop_duplicates(
    subset=["datetime"]
).reset_index(drop=True)

# Chronological bar index
data["bar_index"] = np.arange(len(data))

# ============================================================
# VALIDATE OHLC
# ============================================================

valid_ohlc, ohlc_message = validate_ohlc(data)

if not valid_ohlc:
    st.error(ohlc_message)
    st.stop()

st.success("CSV loaded")
st.success(ohlc_message)
st.success("Datetime validation complete")
st.success("Chronological bar index created")

# ============================================================
# DATA SUMMARY
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Rows", f"{len(data):,}")

with col2:
    st.metric(
        "Start",
        data["datetime"].iloc[0].strftime("%Y-%m-%d %H:%M")
    )

with col3:
    st.metric(
        "End",
        data["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M")
    )

# ============================================================
# NEW YORK TIME COMPONENTS
# ============================================================

data["ny_date"] = data["datetime"].dt.date
data["ny_hour"] = data["datetime"].dt.hour
data["ny_minute"] = data["datetime"].dt.minute

# ============================================================
# VALID PULLBACK DETECTION
# ============================================================
#
# LOCKED DEFINITION
#
# BULLISH:
# 1. Find the bullish candle(s) before the pullback.
# 2. Among that bullish sequence, select the candle with the
#    highest HIGH.
# 3. Its LOW becomes the protected/reference LOW.
# 4. Pullback must grab that LOW.
#    Wick OR close below LOW = valid grab.
# 5. After the grab, a candle must CLOSE above the reference HIGH.
#
# BEARISH:
# 1. Find the bearish candle(s) before the pullback.
# 2. Among that bearish sequence, select the candle with the
#    lowest LOW.
# 3. Its HIGH becomes the protected/reference HIGH.
# 4. Pullback must grab that HIGH.
#    Wick OR close above HIGH = valid grab.
# 5. After the grab, a candle must CLOSE below the reference LOW.
#
# ============================================================

def detect_valid_pullbacks(df):
    bullish_results = []
    bearish_results = []

    n = len(df)

    # --------------------------------------------------------
    # BULLISH VALID PULLBACKS
    # --------------------------------------------------------

    i = 0

    while i < n - 1:

        # A bullish candle starts a possible bullish sequence.
        if df.iloc[i]["close"] <= df.iloc[i]["open"]:
            i += 1
            continue

        sequence_start = i
        sequence_end = i

        # Continue through consecutive bullish candles.
        while (
            sequence_end + 1 < n
            and df.iloc[sequence_end + 1]["close"]
            > df.iloc[sequence_end + 1]["open"]
        ):
            sequence_end += 1

        # Highest HIGH bullish candle in the sequence.
        bullish_sequence = df.iloc[
            sequence_start:sequence_end + 1
        ]

        ref_idx = bullish_sequence["high"].idxmax()
        ref = df.loc[ref_idx]

        ref_high = float(ref["high"])
        ref_low = float(ref["low"])

        # Pullback begins after bullish sequence.
        j = sequence_end + 1

        grab_found = False
        grab_idx = None

        while j < n:

            candle = df.iloc[j]

            # If a new bullish sequence begins before grab,
            # the previous setup is no longer the immediate
            # pullback sequence.
            if candle["close"] > candle["open"] and not grab_found:
                break

            # Grab:
            # Wick OR close below reference LOW.
            if (
                float(candle["low"]) < ref_low
                or float(candle["close"]) < ref_low
            ):
                grab_found = True
                grab_idx = j
                break

            j += 1

        if grab_found:

            k = grab_idx + 1

            while k < n:

                confirmation = df.iloc[k]

                # Confirmation requires CLOSE above reference HIGH.
                if float(confirmation["close"]) > ref_high:

                    bullish_results.append({
                        "bar_index": int(confirmation["bar_index"]),
                        "datetime": confirmation["datetime"],
                        "ny_date": confirmation["ny_date"],
                        "direction": "Bullish",
                        "reference_bar_index": int(ref["bar_index"]),
                        "reference_datetime": ref["datetime"],
                        "reference_high": ref_high,
                        "reference_low": ref_low,
                        "grab_bar_index": int(
                            df.iloc[grab_idx]["bar_index"]
                        ),
                        "grab_datetime": df.iloc[grab_idx]["datetime"],
                        "confirmation_bar_index": int(
                            confirmation["bar_index"]
                        ),
                        "confirmation_datetime": confirmation["datetime"],
                        "manipulation_bar_index": int(
                            df.iloc[grab_idx]["bar_index"]
                        ),
                        "manipulation_price": ref_low,
                        "manipulation_type": "Swing Low",
                        "aoX_leg": "High → Low",
                    })

                    break

                k += 1

        i = max(sequence_end + 1, i + 1)

    # --------------------------------------------------------
    # BEARISH VALID PULLBACKS
    # --------------------------------------------------------

    i = 0

    while i < n - 1:

        # A bearish candle starts a possible bearish sequence.
        if df.iloc[i]["close"] >= df.iloc[i]["open"]:
            i += 1
            continue

        sequence_start = i
        sequence_end = i

        # Continue through consecutive bearish candles.
        while (
            sequence_end + 1 < n
            and df.iloc[sequence_end + 1]["close"]
            < df.iloc[sequence_end + 1]["open"]
        ):
            sequence_end += 1

        bearish_sequence = df.iloc[
            sequence_start:sequence_end + 1
        ]

        # Lowest LOW bearish candle in the sequence.
        ref_idx = bearish_sequence["low"].idxmin()
        ref = df.loc[ref_idx]

        ref_high = float(ref["high"])
        ref_low = float(ref["low"])

        # Pullback begins after bearish sequence.
        j = sequence_end + 1

        grab_found = False
        grab_idx = None

        while j < n:

            candle = df.iloc[j]

            # New bearish sequence before grab invalidates
            # this immediate pullback attempt.
            if candle["close"] < candle["open"] and not grab_found:
                break

            # Grab:
            # Wick OR close above reference HIGH.
            if (
                float(candle["high"]) > ref_high
                or float(candle["close"]) > ref_high
            ):
                grab_found = True
                grab_idx = j
                break

            j += 1

        if grab_found:

            k = grab_idx + 1

            while k < n:

                confirmation = df.iloc[k]

                # Confirmation requires CLOSE below reference LOW.
                if float(confirmation["close"]) < ref_low:

                    bearish_results.append({
                        "bar_index": int(confirmation["bar_index"]),
                        "datetime": confirmation["datetime"],
                        "ny_date": confirmation["ny_date"],
                        "direction": "Bearish",
                        "reference_bar_index": int(ref["bar_index"]),
                        "reference_datetime": ref["datetime"],
                        "reference_high": ref_high,
                        "reference_low": ref_low,
                        "grab_bar_index": int(
                            df.iloc[grab_idx]["bar_index"]
                        ),
                        "grab_datetime": df.iloc[grab_idx]["datetime"],
                        "confirmation_bar_index": int(
                            confirmation["bar_index"]
                        ),
                        "confirmation_datetime": confirmation["datetime"],
                        "manipulation_bar_index": int(
                            df.iloc[grab_idx]["bar_index"]
                        ),
                        "manipulation_price": ref_high,
                        "manipulation_type": "Swing High",
                        "aoX_leg": "Low → High",
                    })

                    break

                k += 1

        i = max(sequence_end + 1, i + 1)

    bullish_df = pd.DataFrame(bullish_results)
    bearish_df = pd.DataFrame(bearish_results)

    if bullish_df.empty:
        bullish_df = pd.DataFrame(
            columns=[
                "bar_index",
                "datetime",
                "ny_date",
                "direction",
                "reference_bar_index",
                "reference_datetime",
                "reference_high",
                "reference_low",
                "grab_bar_index",
                "grab_datetime",
                "confirmation_bar_index",
                "confirmation_datetime",
                "manipulation_bar_index",
                "manipulation_price",
                "manipulation_type",
                "aoX_leg",
            ]
        )

    if bearish_df.empty:
        bearish_df = pd.DataFrame(
            columns=[
                "bar_index",
                "datetime",
                "ny_date",
                "direction",
                "reference_bar_index",
                "reference_datetime",
                "reference_high",
                "reference_low",
                "grab_bar_index",
                "grab_datetime",
                "confirmation_bar_index",
                "confirmation_datetime",
                "manipulation_bar_index",
                "manipulation_price",
                "manipulation_type",
                "aoX_leg",
            ]
        )

    return bullish_df, bearish_df


# ============================================================
# RUN VALID PULLBACK DETECTION
# ============================================================

st.markdown("## 🔎 Valid Pullback Detection")

st.write(
    "Bullish: pullback से पहले के bullish sequence में "
    "सबसे HIGH वाला bullish candle reference है."
)

st.write(
    "Bearish: pullback से पहले के bearish sequence में "
    "सबसे LOW वाला bearish candle reference है."
)

st.write(
    "Reference level का wick या close से grab valid है, "
    "लेकिन उसके बाद confirmation candle का close "
    "reference level के पार होना जरूरी है."
)

bullish_pullbacks, bearish_pullbacks = detect_valid_pullbacks(data)

pullbacks = pd.concat(
    [bullish_pullbacks, bearish_pullbacks],
    ignore_index=True
)

if not pullbacks.empty:
    pullbacks = pullbacks.sort_values(
        "confirmation_bar_index"
    ).reset_index(drop=True)

st.metric(
    "Total Valid Pullbacks",
    f"{len(pullbacks):,}"
)

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "Bullish",
        f"{len(bullish_pullbacks):,}"
    )

with c2:
    st.metric(
        "Bearish",
        f"{len(bearish_pullbacks):,}"
    )

# ============================================================
# SETUP DETECTION
# ============================================================

st.markdown("## 🕣 8:30 / 9:30 NY Setup Detection")

st.write(
    "8:30 NY और 9:30 NY दोनों independent setups हैं."
)

setup_rows = []

for idx, row in data.iterrows():

    hour = int(row["ny_hour"])
    minute = int(row["ny_minute"])

    setup_name = None

    if hour == 8 and minute == 30:
        setup_name = "08:30"

    elif hour == 9 and minute == 30:
        setup_name = "09:30"

    if setup_name is not None:

        setup_rows.append({
            "setup": setup_name,
            "bar_index": int(row["bar_index"]),
            "datetime": row["datetime"],
            "ny_date": row["ny_date"],
        })

setups = pd.DataFrame(setup_rows)

st.metric(
    "Total 8:30 / 9:30 Setup Candles",
    f"{len(setups):,}"
)

# ============================================================
# SETUP → FIRST AFTER-SETUP VALID PULLBACK
# ============================================================

st.markdown("## 🔗 Setup → After-Setup Valid Pullback")

st.write(
    "हर setup के बाद उसी New York calendar date में "
    "आने वाला पहला valid pullback लिया जाएगा."
)

mapped_rows = []

for _, setup in setups.iterrows():

    same_day = pullbacks[
        pullbacks["ny_date"] == setup["ny_date"]
    ]

    after_setup = same_day[
        same_day["confirmation_bar_index"]
        > setup["bar_index"]
    ]

    if after_setup.empty:
        continue

    first_pullback = (
        after_setup
        .sort_values("confirmation_bar_index")
        .iloc[0]
    )

    row = first_pullback.to_dict()

    row["setup"] = setup["setup"]
    row["setup_bar_index"] = setup["bar_index"]
    row["setup_datetime"] = setup["datetime"]

    mapped_rows.append(row)

mapped = pd.DataFrame(mapped_rows)

st.metric(
    "Setup Candles",
    f"{len(setups):,}"
)

st.metric(
    "After-Setup Pullback Found",
    f"{len(mapped):,}"
)

st.metric(
    "No Pullback Found",
    f"{len(setups) - len(mapped):,}"
)

# ============================================================
# MANIPULATION
# ============================================================

st.markdown("## 🧭 LEFT-SIDE Manipulation")

st.write(
    "Manipulation valid pullback के grab candle से लिया जाएगा."
)

st.write(
    "Bullish = reference LOW का grab → Swing Low / High → Low"
)

st.write(
    "Bearish = reference HIGH का grab → Swing High / Low → High"
)

if not mapped.empty:

    mapped["manipulation_bar_index"] = mapped[
        "grab_bar_index"
    ]

    mapped["manipulation_price"] = mapped[
        "manipulation_price"
    ]

    mapped["manipulation_type"] = mapped[
        "manipulation_type"
    ]

    mapped["aoX_leg"] = mapped[
        "aoX_leg"
    ]

    manipulation_found = mapped[
        mapped["manipulation_bar_index"].notna()
    ].copy()

else:
    manipulation_found = mapped.copy()

st.metric(
    "Total Setups",
    f"{len(setups):,}"
)

st.metric(
    "Manipulation Found",
    f"{len(manipulation_found):,}"
)

st.metric(
    "Manipulation Not Found",
    f"{len(setups) - len(manipulation_found):,}"
)

# ============================================================
# AOX
# ============================================================

st.markdown("## 📐 AOX Configuration")

st.info(
    "AOX levels अभी display/configuration के लिए हैं. "
    "Customized Fibonacci price calculation जानबूझकर अभी add नहीं की गई है."
)

st.write("AOX levels:", AOX_LEVELS)
st.write("AOX entry levels:", AOX_ENTRY_LEVELS)
st.write("AOX reference levels:", AOX_REFERENCE_LEVELS)

st.write(
    "Bullish AOX orientation: High → Low"
)

st.write(
    "Bearish AOX orientation: Low → High"
)

st.write(
    "पहला valid AOX entry ही लिया जाएगा."
)

# ============================================================
# TRADE MANAGEMENT
# ============================================================

st.markdown("## 🎯 Trade Management")

c1, c2 = st.columns(2)

with c1:
    st.write("**Trade 1**")
    st.write(f"SL = {TRADE_1_SL:.3f}")
    st.write(f"TP = {TRADE_1_TP:.3f}")
    st.write("R:R = 1:3")

with c2:
    st.write("**Trade 2**")
    st.write(f"SL = {TRADE_2_SL:.3f}")
    st.write(f"TP = {TRADE_2_TP:.3f}")
    st.write("R:R = 1:4")

st.info(
    "दोनों positions के लिए fixed SL distance 5.000 है. "
    "Trade 1 TP = 15.000 और Trade 2 TP = 20.000."
)

# ============================================================
# STATUS
# ============================================================

st.markdown("## ✅ Current Module Status")

st.success(
    "Data loading + NY timezone + 8:30/9:30 setups + "
    "locked Valid Pullback + manipulation mapping complete."
)

st.warning(
    "AOX का exact customized Fibonacci price formula अभी "
    "जानबूझकर लागू नहीं किया गया है."
)

st.info(
    "Next module: AOX Fibonacci calculation → "
    "first valid entry detection → SL/TP backtest."
)
