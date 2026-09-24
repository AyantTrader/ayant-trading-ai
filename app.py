import streamlit as st
import pandas as pd
import numpy as np


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AYANT Trading AI",
    page_icon="📈",
    layout="wide"
)

st.title("🤖 AYANT Trading AI")
st.caption("XAUUSD 1-Minute Strategy Tester")


# ============================================================
# CONSTANTS
# ============================================================

NY_TZ = "America/New_York"

SETUP_TIMES = [
    (8, 30),
    (9, 30)
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def find_column(df, possible_names):
    lower_map = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in possible_names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]

    return None


def normalize_datetime(df):

    dt_col = find_column(
        df,
        [
            "datetime",
            "date",
            "time",
            "timestamp",
            "date_time"
        ]
    )

    if dt_col is None:
        raise ValueError(
            "Datetime column not found. Expected a column such as datetime."
        )

    parsed = pd.to_datetime(
        df[dt_col],
        errors="coerce",
        utc=True
    )

    if parsed.isna().any():
        bad_count = int(parsed.isna().sum())

        raise ValueError(
            f"Datetime validation failed: "
            f"{bad_count} invalid datetime values found."
        )

    df = df.copy()
    df["datetime"] = parsed

    return df


def validate_ohlc(df):

    open_col = find_column(df, ["open"])
    high_col = find_column(df, ["high"])
    low_col = find_column(df, ["low"])
    close_col = find_column(df, ["close"])

    missing = []

    if open_col is None:
        missing.append("open")

    if high_col is None:
        missing.append("high")

    if low_col is None:
        missing.append("low")

    if close_col is None:
        missing.append("close")

    if missing:
        raise ValueError(
            "Missing OHLC columns: "
            + ", ".join(missing)
        )

    df = df.copy()

    df["open"] = pd.to_numeric(
        df[open_col],
        errors="coerce"
    )

    df["high"] = pd.to_numeric(
        df[high_col],
        errors="coerce"
    )

    df["low"] = pd.to_numeric(
        df[low_col],
        errors="coerce"
    )

    df["close"] = pd.to_numeric(
        df[close_col],
        errors="coerce"
    )

    if df[
        ["open", "high", "low", "close"]
    ].isna().any().any():

        raise ValueError(
            "OHLC validation failed: "
            "non-numeric or missing OHLC values found."
        )

    return df


# ============================================================
# FILE UPLOAD
# ============================================================

st.header("📂 XAUUSD 1-Minute Data")

uploaded_file = st.file_uploader(
    "Upload XAUUSD 1-minute CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Please upload your XAUUSD 1-minute CSV.")
    st.stop()


# ============================================================
# LOAD CSV
# ============================================================

try:

    df = pd.read_csv(uploaded_file)

    st.success("CSV loaded")

except Exception as e:

    st.error(
        f"CSV loading failed: {e}"
    )

    st.stop()


# ============================================================
# OHLC VALIDATION
# ============================================================

try:

    df = validate_ohlc(df)

    st.success(
        "OHLC validation complete"
    )

except Exception as e:

    st.error(
        f"OHLC validation error: {e}"
    )

    st.stop()


# ============================================================
# DATETIME VALIDATION
# ============================================================

try:

    df = normalize_datetime(df)

    st.success(
        "Datetime validation complete"
    )

except Exception as e:

    st.error(
        f"Datetime validation error: {e}"
    )

    st.stop()


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df = (
    df
    .sort_values("datetime")
    .reset_index(drop=True)
)

df = (
    df
    .drop_duplicates(
        subset=["datetime"],
        keep="first"
    )
    .reset_index(drop=True)
)


# ============================================================
# CHRONOLOGICAL BAR INDEX
# ============================================================

df["bar_index"] = np.arange(
    len(df),
    dtype=np.int64
)

st.success(
    "Chronological bar index created"
)


# ============================================================
# BASIC DATA INFORMATION
# ============================================================

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Rows",
        f"{len(df):,}"
    )

with c2:

    start_time = df["datetime"].iloc[0]

    st.metric(
        "Start",
        start_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

with c3:

    end_time = df["datetime"].iloc[-1]

    st.metric(
        "End",
        end_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )


# ============================================================
# NEW YORK TIME
# ============================================================

df["ny_time"] = (
    df["datetime"]
    .dt
    .tz_convert(NY_TZ)
)

df["ny_date"] = (
    df["ny_time"]
    .dt
    .date
)

df["ny_hour"] = (
    df["ny_time"]
    .dt
    .hour
)

df["ny_minute"] = (
    df["ny_time"]
    .dt
    .minute
)


# ============================================================
# VALID PULLBACK DETECTION
# ============================================================

st.divider()

st.header(
    "🔎 Valid Pullback Detection"
)

st.caption(
    "Bullish: C2 sweeps C1 Low without "
    "closing below it, then C3 closes above C1 High."
)

st.caption(
    "Bearish: C2 sweeps C1 High without "
    "closing above it, then C3 closes below C1 Low."
)


# ------------------------------------------------------------
# Candle arrays
# ------------------------------------------------------------

c1_high = df["high"].shift(2)
c1_low = df["low"].shift(2)

c2_high = df["high"].shift(1)
c2_low = df["low"].shift(1)
c2_close = df["close"].shift(1)

c3_high = df["high"]
c3_low = df["low"]
c3_close = df["close"]


# ------------------------------------------------------------
# EXACT BULLISH RULE
# ------------------------------------------------------------

bullish_mask = (
    (c2_low < c1_low)
    &
    (c2_close >= c1_low)
    &
    (c3_close > c1_high)
)


# ------------------------------------------------------------
# EXACT BEARISH RULE
# ------------------------------------------------------------

bearish_mask = (
    (c2_high > c1_high)
    &
    (c2_close <= c1_high)
    &
    (c3_close < c1_low)
)


# ============================================================
# BUILD BULLISH SIGNAL TABLE
# ============================================================

bullish_signals = df.loc[
    bullish_mask
].copy()

bullish_signals["direction"] = (
    "Bullish"
)

bullish_signals["c1_bar_index"] = (
    bullish_signals["bar_index"] - 2
)

bullish_signals["c2_bar_index"] = (
    bullish_signals["bar_index"] - 1
)

bullish_signals["c3_bar_index"] = (
    bullish_signals["bar_index"]
)

bullish_signals["c1_high"] = (
    df["high"]
    .shift(2)
    .loc[bullish_mask]
)

bullish_signals["c1_low"] = (
    df["low"]
    .shift(2)
    .loc[bullish_mask]
)

bullish_signals["c2_high"] = (
    df["high"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals["c2_low"] = (
    df["low"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals["c2_close"] = (
    df["close"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals["c3_close"] = (
    df["close"]
    .loc[bullish_mask]
)


# ============================================================
# BUILD BEARISH SIGNAL TABLE
# ============================================================

bearish_signals = df.loc[
    bearish_mask
].copy()

bearish_signals["direction"] = (
    "Bearish"
)

bearish_signals["c1_bar_index"] = (
    bearish_signals["bar_index"] - 2
)

bearish_signals["c2_bar_index"] = (
    bearish_signals["bar_index"] - 1
)

bearish_signals["c3_bar_index"] = (
    bearish_signals["bar_index"]
)

bearish_signals["c1_high"] = (
    df["high"]
    .shift(2)
    .loc[bearish_mask]
)

bearish_signals["c1_low"] = (
    df["low"]
    .shift(2)
    .loc[bearish_mask]
)

bearish_signals["c2_high"] = (
    df["high"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals["c2_low"] = (
    df["low"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals["c2_close"] = (
    df["close"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals["c3_close"] = (
    df["close"]
    .loc[bearish_mask]
)


# ============================================================
# COMBINE SIGNALS
# ============================================================

pullbacks = pd.concat(
    [
        bullish_signals,
        bearish_signals
    ],
    axis=0,
    ignore_index=True
)

pullbacks = (
    pullbacks
    .sort_values("bar_index")
    .reset_index(drop=True)
)


# ============================================================
# PULLBACK SUMMARY
# ============================================================

total_pullbacks = len(
    pullbacks
)

bullish_count = len(
    bullish_signals
)

bearish_count = len(
    bearish_signals
)


m1, m2, m3 = st.columns(3)

with m1:

    st.metric(
        "Total Valid Pullbacks",
        f"{total_pullbacks:,}"
    )

with m2:

    st.metric(
        "Bullish",
        f"{bullish_count:,}"
    )

with m3:

    st.metric(
        "Bearish",
        f"{bearish_count:,}"
    )


# ============================================================
# PULLBACK TABLE
# ============================================================

with st.expander(
    "📋 View Valid Pullbacks"
):

    display_columns = [
        "datetime",
        "direction",
        "c1_bar_index",
        "c2_bar_index",
        "c3_bar_index",
        "c1_high",
        "c1_low",
        "c2_high",
        "c2_low",
        "c2_close",
        "c3_close"
    ]

    available_columns = [
        c
        for c in display_columns
        if c in pullbacks.columns
    ]

    st.dataframe(
        pullbacks[
            available_columns
        ].head(100),
        use_container_width=True
    )


# ============================================================
# 8:30 / 9:30 NY SETUP DETECTION
# ============================================================

st.divider()

st.header(
    "🕣 8:30 / 9:30 NY Setup Detection"
)


setup_mask = (
    (
        (df["ny_hour"] == 8)
        &
        (df["ny_minute"] == 30)
    )
    |
    (
        (df["ny_hour"] == 9)
        &
        (df["ny_minute"] == 30)
    )
)


setups = df.loc[
    setup_mask
].copy()


setups["setup_time"] = (
    setups["ny_hour"].astype(str)
    + ":"
    + setups["ny_minute"]
    .astype(str)
    .str.zfill(2)
)


setups["setup_id"] = np.arange(
    len(setups),
    dtype=np.int64
)


st.metric(
    "Total 8:30 / 9:30 Setup Candles",
    f"{len(setups):,}"
)


with st.expander(
    "📋 View Setup Candles"
):

    setup_display = [
        "datetime",
        "ny_time",
        "ny_date",
        "setup_time",
        "bar_index",
        "open",
        "high",
        "low",
        "close"
    ]

    setup_display = [
        c
        for c in setup_display
        if c in setups.columns
    ]

    st.dataframe(
        setups[setup_display],
        use_container_width=True
    )


# ============================================================
# SETUP → AFTER-SETUP VALID PULLBACK
# ============================================================

st.divider()

st.header(
    "🔗 Setup → After-Setup Valid Pullback"
)

st.caption(
    "हर 8:30 / 9:30 setup के बाद उसी "
    "New York calendar date में आने वाला "
    "पहला valid pullback लिया जाएगा."
)

st.caption(
    "यहाँ valid pullback manipulation leg को "
    "confirm/complete करता है."
)


after_setup_rows = []


# ------------------------------------------------------------
# Associate each setup with FIRST pullback after setup
# ------------------------------------------------------------

for _, setup in setups.iterrows():

    setup_date = setup["ny_date"]

    setup_bar_index = int(
        setup["bar_index"]
    )

    setup_time = setup["setup_time"]

    candidates = pullbacks[
        (pullbacks["ny_date"] == setup_date)
        &
        (pullbacks["bar_index"] > setup_bar_index)
    ]

    if candidates.empty:

        after_setup_rows.append(
            {
                "setup_id": setup["setup_id"],
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "pullback_found": False,
                "pullback_direction": None,
                "pullback_bar_index": None,
                "pullback_datetime": None
            }
        )

        continue


    first_pullback = candidates.iloc[0]


    after_setup_rows.append(
        {
            "setup_id": setup["setup_id"],
            "setup_date": setup_date,
            "setup_time": setup_time,
            "setup_bar_index": setup_bar_index,
            "pullback_found": True,
            "pullback_direction": first_pullback["direction"],
            "pullback_bar_index": int(
                first_pullback["bar_index"]
            ),
            "pullback_datetime": first_pullback["datetime"]
        }
    )


after_setup = pd.DataFrame(
    after_setup_rows
)


# ============================================================
# AFTER-SETUP SUMMARY
# ============================================================

if len(after_setup) > 0:

    found_count = int(
        after_setup[
            "pullback_found"
        ].sum()
    )

    not_found_count = (
        len(after_setup)
        - found_count
    )

    a1, a2, a3 = st.columns(3)

    with a1:

        st.metric(
            "Setup Candles",
            f"{len(after_setup):,}"
        )

    with a2:

        st.metric(
            "After-Setup Pullback Found",
            f"{found_count:,}"
        )

    with a3:

        st.metric(
            "No Pullback Found",
            f"{not_found_count:,}"
        )


    with st.expander(
        "📋 View Setup → Pullback Mapping"
    ):

        st.dataframe(
            after_setup,
            use_container_width=True
        )


# ============================================================
# SWING DETECTION
# ============================================================

st.divider()

st.header(
    "📌 Swing Detection"
)

st.caption(
    "Swing High = बीच वाली candle का High "
    "उसकी left और right candle के High से बड़ा."
)

st.caption(
    "Swing Low = बीच वाली candle का Low "
    "उसकी left और right candle के Low से छोटा."
)


# ------------------------------------------------------------
# Confirmed swing definitions
# ------------------------------------------------------------

df["swing_high"] = (
    (df["high"] > df["high"].shift(1))
    &
    (df["high"] > df["high"].shift(-1))
)

df["swing_low"] = (
    (df["low"] < df["low"].shift(1))
    &
    (df["low"] < df["low"].shift(-1))
)


swing_high_count = int(
    df["swing_high"].sum()
)

swing_low_count = int(
    df["swing_low"].sum()
)


s1, s2 = st.columns(2)

with s1:

    st.metric(
        "Swing Highs",
        f"{swing_high_count:,}"
    )

with s2:

    st.metric(
        "Swing Lows",
        f"{swing_low_count:,}"
    )


# ============================================================
# LEFT-SIDE MANIPULATION
# ============================================================

st.divider()

st.header(
    "🧭 LEFT-SIDE Manipulation Detection"
)

st.caption(
    "Setup → latest relevant swing pair → "
    "valid pullback confirmation."
)

st.caption(
    "Bullish = latest Swing High के बाद latest Swing Low → High → Low"
)

st.caption(
    "Bearish = latest Swing Low के बाद latest Swing High → Low → High"
)


manipulation_rows = []


# ============================================================
# PROCESS EACH SETUP
# ============================================================

for _, setup in setups.iterrows():

    setup_id = int(
        setup["setup_id"]
    )

    setup_date = setup["ny_date"]

    setup_time = setup["setup_time"]

    setup_bar_index = int(
        setup["bar_index"]
    )


    # --------------------------------------------------------
    # Find associated pullback
    # --------------------------------------------------------

    setup_pullback = after_setup[
        after_setup["setup_id"] == setup_id
    ]


    if setup_pullback.empty:

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": None,
                "pullback_bar_index": None,
                "swing_1_type": None,
                "swing_1_bar_index": None,
                "swing_1_price": None,
                "swing_2_type": None,
                "swing_2_bar_index": None,
                "swing_2_price": None,
                "manipulation_leg": None,
                "manipulation_found": False
            }
        )

        continue


    pullback_info = setup_pullback.iloc[0]


    if not bool(
        pullback_info["pullback_found"]
    ):

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": None,
                "pullback_bar_index": None,
                "swing_1_type": None,
                "swing_1_bar_index": None,
                "swing_1_price": None,
                "swing_2_type": None,
                "swing_2_bar_index": None,
                "swing_2_price": None,
                "manipulation_leg": None,
                "manipulation_found": False
            }
        )

        continue


    direction = (
        pullback_info[
            "pullback_direction"
        ]
    )

    pullback_bar_index = int(
        pullback_info[
            "pullback_bar_index"
        ]
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # A swing needs a candle on its right.
    #
    # Therefore only swings whose right-side confirmation
    # candle has already occurred before the pullback
    # confirmation are eligible.
    #
    # Swing center <= pullback_bar_index - 2
    # --------------------------------------------------------

    eligible_end = (
        pullback_bar_index - 2
    )


    if eligible_end <= setup_bar_index:

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": direction,
                "pullback_bar_index": pullback_bar_index,
                "swing_1_type": None,
                "swing_1_bar_index": None,
                "swing_1_price": None,
                "swing_2_type": None,
                "swing_2_bar_index": None,
                "swing_2_price": None,
                "manipulation_leg": None,
                "manipulation_found": False
            }
        )

        continue


    swing_window = df[
        (df["bar_index"] > setup_bar_index)
        &
        (df["bar_index"] <= eligible_end)
        &
        (
            df["swing_high"]
            |
            df["swing_low"]
        )
    ].copy()


    # --------------------------------------------------------
    # BULLISH:
    # Latest Swing High
    # followed by
    # Latest Swing Low
    # --------------------------------------------------------

    if direction == "Bullish":

        swing_highs = swing_window[
            swing_window["swing_high"]
        ]

        if swing_highs.empty:

            manipulation_rows.append(
                {
                    "setup_id": setup_id,
                    "setup_date": setup_date,
                    "setup_time": setup_time,
                    "direction": direction,
                    "pullback_bar_index": pullback_bar_index,
                    "swing_1_type": None,
                    "swing_1_bar_index": None,
                    "swing_1_price": None,
                    "swing_2_type": None,
                    "swing_2_bar_index": None,
                    "swing_2_price": None,
                    "manipulation_leg": None,
                    "manipulation_found": False
                }
            )

            continue


        latest_high = (
            swing_highs
            .sort_values("bar_index")
            .iloc[-1]
        )


        swing_lows_after_high = swing_window[
            (swing_window["swing_low"])
            &
            (
                swing_window["bar_index"]
                > int(latest_high["bar_index"])
            )
        ]


        if swing_lows_after_high.empty:

            manipulation_rows.append(
                {
                    "setup_id": setup_id,
                    "setup_date": setup_date,
                    "setup_time": setup_time,
                    "direction": direction,
                    "pullback_bar_index": pullback_bar_index,
                    "swing_1_type": "Swing High",
                    "swing_1_bar_index": int(
                        latest_high["bar_index"]
                    ),
                    "swing_1_price": float(
                        latest_high["high"]
                    ),
                    "swing_2_type": None,
                    "swing_2_bar_index": None,
                    "swing_2_price": None,
                    "manipulation_leg": None,
                    "manipulation_found": False
                }
            )

            continue


        latest_low = (
            swing_lows_after_high
            .sort_values("bar_index")
            .iloc[-1]
        )


        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": direction,
                "pullback_bar_index": pullback_bar_index,
                "swing_1_type": "Swing High",
                "swing_1_bar_index": int(
                    latest_high["bar_index"]
                ),
                "swing_1_price": float(
                    latest_high["high"]
                ),
                "swing_2_type": "Swing Low",
                "swing_2_bar_index": int(
                    latest_low["bar_index"]
                ),
                "swing_2_price": float(
                    latest_low["low"]
                ),
                "manipulation_leg": "High → Low",
                "manipulation_found": True
            }
        )


    # --------------------------------------------------------
    # BEARISH:
    # Latest Swing Low
    # followed by
    # Latest Swing High
    # --------------------------------------------------------

    elif direction == "Bearish":

        swing_lows = swing_window[
            swing_window["swing_low"]
        ]

        if swing_lows.empty:

            manipulation_rows.append(
                {
                    "setup_id": setup_id,
                    "setup_date": setup_date,
                    "setup_time": setup_time,
                    "direction": direction,
                    "pullback_bar_index": pullback_bar_index,
                    "swing_1_type": None,
                    "swing_1_bar_index": None,
                    "swing_1_price": None,
                    "swing_2_type": None,
                    "swing_2_bar_index": None,
                    "swing_2_price": None,
                    "manipulation_leg": None,
                    "manipulation_found": False
                }
            )

            continue


        latest_low = (
            swing_lows
            .sort_values("bar_index")
            .iloc[-1]
        )


        swing_highs_after_low = swing_window[
            (swing_window["swing_high"])
            &
            (
                swing_window["bar_index"]
                > int(latest_low["bar_index"])
            )
        ]


        if swing_highs_after_low.empty:

            manipulation_rows.append(
                {
                    "setup_id": setup_id,
                    "setup_date": setup_date,
                    "setup_time": setup_time,
                    "direction": direction,
                    "pullback_bar_index": pullback_bar_index,
                    "swing_1_type": "Swing Low",
                    "swing_1_bar_index": int(
                        latest_low["bar_index"]
                    ),
                    "swing_1_price": float(
                        latest_low["low"]
                    ),
                    "swing_2_type": None,
                    "swing_2_bar_index": None,
                    "swing_2_price": None,
                    "manipulation_leg": None,
                    "manipulation_found": False
                }
            )

            continue


        latest_high = (
            swing_highs_after_low
            .sort_values("bar_index")
            .iloc[-1]
        )


        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": direction,
                "pullback_bar_index": pullback_bar_index,
                "swing_1_type": "Swing Low",
                "swing_1_bar_index": int(
                    latest_low["bar_index"]
                ),
                "swing_1_price": float(
                    latest_low["low"]
                ),
                "swing_2_type": "Swing High",
                "swing_2_bar_index": int(
                    latest_high["bar_index"]
                ),
                "swing_2_price": float(
                    latest_high["high"]
                ),
                "manipulation_leg": "Low → High",
                "manipulation_found": True
            }
        )


    else:

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": direction,
                "pullback_bar_index": pullback_bar_index,
                "swing_1_type": None,
                "swing_1_bar_index": None,
                "swing_1_price": None,
                "swing_2_type": None,
                "swing_2_bar_index": None,
                "swing_2_price": None,
                "manipulation_leg": None,
                "manipulation_found": False
            }
        )


# ============================================================
# MANIPULATION DATAFRAME
# ============================================================

manipulation = pd.DataFrame(
    manipulation_rows
)


# ============================================================
# MANIPULATION SUMMARY
# ============================================================

manipulation_found_count = int(
    manipulation[
        "manipulation_found"
    ].sum()
)

manipulation_not_found_count = (
    len(manipulation)
    - manipulation_found_count
)


m1, m2, m3 = st.columns(3)

with m1:

    st.metric(
        "Total Setups",
        f"{len(manipulation):,}"
    )

with m2:

    st.metric(
        "Manipulation Found",
        f"{manipulation_found_count:,}"
    )

with m3:

    st.metric(
        "Manipulation Not Found",
        f"{manipulation_not_found_count:,}"
    )


# ============================================================
# MANIPULATION TABLE
# ============================================================

with st.expander(
    "📋 View LEFT-SIDE Manipulation Mapping"
):

    st.dataframe(
        manipulation,
        use_container_width=True
    )


# ============================================================
# AOX CONFIGURATION
# ============================================================

st.divider()

st.header(
    "📐 AOX Configuration"
)

st.info(
    "AOX अभी calculation नहीं कर रहा है. "
    "पहले LEFT-SIDE manipulation mapping verify की जा रही है."
)


AOX_LEVELS = [
    0.000,
    1.000,
    -0.210,
    -0.255,
    -0.290,
    1.470,
    1.550,
    2.560,
    2.600,
    2.640
]


AOX_ENTRY_LEVELS = [
    -0.210,
    -0.255,
    -0.290
]


AOX_TARGET_REFERENCE_LEVELS = [
    2.560,
    2.600,
    2.640
]


col1, col2 = st.columns(2)

with col1:

    st.write(
        "**AOX Entry Levels**"
    )

    st.write(
        AOX_ENTRY_LEVELS
    )

with col2:

    st.write(
        "**AOX Reference Levels**"
    )

    st.write(
        AOX_TARGET_REFERENCE_LEVELS
    )


# ============================================================
# TRADE MANAGEMENT CONFIGURATION
# ============================================================

st.divider()

st.header(
    "🎯 Trade Management"
)

t1, t2 = st.columns(2)

with t1:

    st.write(
        "**Trade 1**"
    )

    st.write(
        "SL = 5.000 price distance"
    )

    st.write(
        "TP = 15.000 price distance"
    )

    st.write(
        "Risk : Reward = 1 : 3"
    )

with t2:

    st.write(
        "**Trade 2**"
    )

    st.write(
        "SL = 5.000 price distance"
    )

    st.write(
        "TP = 20.000 price distance"
    )

    st.write(
        "Risk : Reward = 1 : 4"
    )


# ============================================================
# STATUS
# ============================================================

st.divider()

if manipulation_found_count > 0:

    st.success(
        "✅ Data → Valid Pullback → Setup → "
        "Latest Swing → LEFT-SIDE Manipulation "
        "pipeline loaded successfully."
    )

else:

    st.warning(
        "⚠️ No LEFT-SIDE manipulation pair was found "
        "under the current swing definition."
    )


st.info(
    "Next module: AOX Fibonacci → First valid AOX entry → "
    "2-position SL/TP simulation → Performance report."
)
