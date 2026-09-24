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
# AOX CONFIGURATION
# ============================================================

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


# ============================================================
# TRADE MANAGEMENT
# ============================================================

TRADE_1_SL = 5.000
TRADE_1_TP = 15.000

TRADE_2_SL = 5.000
TRADE_2_TP = 20.000


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
            "Datetime column not found. "
            "Expected a column such as datetime."
        )

    parsed = pd.to_datetime(
        df[dt_col],
        errors="coerce",
        utc=True
    )

    if parsed.isna().any():

        bad_count = int(
            parsed.isna().sum()
        )

        raise ValueError(
            f"Datetime validation failed: "
            f"{bad_count} invalid datetime values found."
        )

    df = df.copy()

    df["datetime"] = parsed

    return df


def validate_ohlc(df):

    open_col = find_column(
        df,
        ["open"]
    )

    high_col = find_column(
        df,
        ["high"]
    )

    low_col = find_column(
        df,
        ["low"]
    )

    close_col = find_column(
        df,
        ["close"]
    )

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

    st.info(
        "Please upload your XAUUSD 1-minute CSV."
    )

    st.stop()


# ============================================================
# LOAD CSV
# ============================================================

try:

    df = pd.read_csv(
        uploaded_file
    )

    st.success(
        "CSV loaded"
    )

except Exception as e:

    st.error(
        f"CSV loading failed: {e}"
    )

    st.stop()


# ============================================================
# OHLC VALIDATION
# ============================================================

try:

    df = validate_ohlc(
        df
    )

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

    df = normalize_datetime(
        df
    )

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
    .sort_values(
        "datetime"
    )
    .reset_index(
        drop=True
    )
)

df = (
    df
    .drop_duplicates(
        subset=["datetime"],
        keep="first"
    )
    .reset_index(
        drop=True
    )
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

    start_time = (
        df["datetime"].iloc[0]
    )

    st.metric(
        "Start",
        start_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

with c3:

    end_time = (
        df["datetime"].iloc[-1]
    )

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
    .tz_convert(
        NY_TZ
    )
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
    "Bullish: C2 Low grabs C1 Low, "
    "then C3 closes above C1 High."
)

st.caption(
    "Bearish: C2 High grabs C1 High, "
    "then C3 closes below C1 Low."
)

st.caption(
    "C2 का wick या close level के पार जाना "
    "grab के लिए valid है."
)


# ============================================================
# THREE-CANDLE STRUCTURE
# ============================================================

c1_high = (
    df["high"].shift(2)
)

c1_low = (
    df["low"].shift(2)
)

c2_high = (
    df["high"].shift(1)
)

c2_low = (
    df["low"].shift(1)
)

c3_close = (
    df["close"]
)


# ============================================================
# BULLISH VALID PULLBACK
# ============================================================
#
# C2 Low must go below C1 Low.
# C2 close does NOT need to close back above C1 Low.
#
# Then C3 must CLOSE above C1 High.
#
# This follows:
# "grabbing = price went below low,
# wick or close both valid."
# ============================================================

bullish_mask = (
    (c2_low < c1_low)
    &
    (c3_close > c1_high)
)


# ============================================================
# BEARISH VALID PULLBACK
# ============================================================
#
# C2 High must go above C1 High.
# C2 close does NOT need to close back below C1 High.
#
# Then C3 must CLOSE below C1 Low.
#
# This follows:
# "grabbing = price went above high,
# wick or close both valid."
# ============================================================

bearish_mask = (
    (c2_high > c1_high)
    &
    (c3_close < c1_low)
)


# ============================================================
# BUILD BULLISH SIGNAL TABLE
# ============================================================

bullish_signals = df.loc[
    bullish_mask
].copy()

bullish_signals[
    "direction"
] = "Bullish"

bullish_signals[
    "c1_bar_index"
] = (
    bullish_signals["bar_index"]
    - 2
)

bullish_signals[
    "c2_bar_index"
] = (
    bullish_signals["bar_index"]
    - 1
)

bullish_signals[
    "c3_bar_index"
] = (
    bullish_signals["bar_index"]
)

bullish_signals[
    "c1_high"
] = (
    df["high"]
    .shift(2)
    .loc[bullish_mask]
)

bullish_signals[
    "c1_low"
] = (
    df["low"]
    .shift(2)
    .loc[bullish_mask]
)

bullish_signals[
    "c2_high"
] = (
    df["high"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals[
    "c2_low"
] = (
    df["low"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals[
    "c2_close"
] = (
    df["close"]
    .shift(1)
    .loc[bullish_mask]
)

bullish_signals[
    "c3_close"
] = (
    df["close"]
    .loc[bullish_mask]
)

# ------------------------------------------------------------
# IMPORTANT:
# Pullback date is the NY date of C3.
# ------------------------------------------------------------

bullish_signals[
    "ny_date"
] = (
    df["ny_date"]
    .loc[bullish_mask]
)


# ============================================================
# BUILD BEARISH SIGNAL TABLE
# ============================================================

bearish_signals = df.loc[
    bearish_mask
].copy()

bearish_signals[
    "direction"
] = "Bearish"

bearish_signals[
    "c1_bar_index"
] = (
    bearish_signals["bar_index"]
    - 2
)

bearish_signals[
    "c2_bar_index"
] = (
    bearish_signals["bar_index"]
    - 1
)

bearish_signals[
    "c3_bar_index"
] = (
    bearish_signals["bar_index"]
)

bearish_signals[
    "c1_high"
] = (
    df["high"]
    .shift(2)
    .loc[bearish_mask]
)

bearish_signals[
    "c1_low"
] = (
    df["low"]
    .shift(2)
    .loc[bearish_mask]
)

bearish_signals[
    "c2_high"
] = (
    df["high"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals[
    "c2_low"
] = (
    df["low"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals[
    "c2_close"
] = (
    df["close"]
    .shift(1)
    .loc[bearish_mask]
)

bearish_signals[
    "c3_close"
] = (
    df["close"]
    .loc[bearish_mask]
)

# ------------------------------------------------------------
# IMPORTANT:
# Pullback date is the NY date of C3.
# ------------------------------------------------------------

bearish_signals[
    "ny_date"
] = (
    df["ny_date"]
    .loc[bearish_mask]
)


# ============================================================
# COMBINE VALID PULLBACKS
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
    .sort_values(
        "bar_index"
    )
    .reset_index(
        drop=True
    )
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
        "ny_date",
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

st.caption(
    "8:30 NY और 9:30 NY दोनों independent setups हैं."
)

st.caption(
    "प्रत्येक setup की अपनी अलग valid pullback mapping होगी."
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
    setups["ny_hour"]
    .astype(str)
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
        setups[
            setup_display
        ],
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
    "8:30 और 9:30 setups independent हैं."
)


after_setup_rows = []


# ============================================================
# ASSOCIATE EACH SETUP WITH FIRST VALID PULLBACK
# ============================================================

for _, setup in setups.iterrows():

    setup_id = int(
        setup["setup_id"]
    )

    setup_date = (
        setup["ny_date"]
    )

    setup_bar_index = int(
        setup["bar_index"]
    )

    setup_time = (
        setup["setup_time"]
    )


    candidates = pullbacks[
        (pullbacks["ny_date"] == setup_date)
        &
        (pullbacks["bar_index"] > setup_bar_index)
    ].copy()


    if candidates.empty:

        after_setup_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "pullback_found": False,
                "pullback_direction": None,
                "pullback_bar_index": None,
                "pullback_datetime": None,
                "c1_bar_index": None,
                "c2_bar_index": None,
                "c3_bar_index": None,
                "c1_high": None,
                "c1_low": None,
                "c2_high": None,
                "c2_low": None,
                "c2_close": None,
                "c3_close": None
            }
        )

        continue


    first_pullback = (
        candidates
        .sort_values(
            "bar_index"
        )
        .iloc[0]
    )


    after_setup_rows.append(
        {
            "setup_id": setup_id,
            "setup_date": setup_date,
            "setup_time": setup_time,
            "setup_bar_index": setup_bar_index,
            "pullback_found": True,
            "pullback_direction": (
                first_pullback["direction"]
            ),
            "pullback_bar_index": int(
                first_pullback["bar_index"]
            ),
            "pullback_datetime": (
                first_pullback["datetime"]
            ),
            "c1_bar_index": int(
                first_pullback["c1_bar_index"]
            ),
            "c2_bar_index": int(
                first_pullback["c2_bar_index"]
            ),
            "c3_bar_index": int(
                first_pullback["c3_bar_index"]
            ),
            "c1_high": float(
                first_pullback["c1_high"]
            ),
            "c1_low": float(
                first_pullback["c1_low"]
            ),
            "c2_high": float(
                first_pullback["c2_high"]
            ),
            "c2_low": float(
                first_pullback["c2_low"]
            ),
            "c2_close": float(
                first_pullback["c2_close"]
            ),
            "c3_close": float(
                first_pullback["c3_close"]
            )
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
#
# These definitions are kept only as the general swing
# definitions supplied by the user.
#
# IMPORTANT:
# Swing High / Swing Low are NOT being used to create
# the manipulation leg.
#
# Manipulation comes directly from the Valid Pullback C2.
# ============================================================

st.divider()

st.header(
    "📌 Swing Detection"
)

st.caption(
    "Swing High = middle candle का High "
    "left और right candle के High से बड़ा."
)

st.caption(
    "Swing Low = middle candle का Low "
    "left और right candle के Low से छोटा."
)

st.caption(
    "Swing detection manipulation mapping में "
    "use नहीं हो रही है."
)


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
    "🧭 LEFT-SIDE Manipulation"
)

st.caption(
    "Manipulation valid pullback के C2 से लिया जाएगा."
)

st.caption(
    "Bullish = C2 Low → Swing Low / manipulation point"
)

st.caption(
    "Bearish = C2 High → Swing High / manipulation point"
)

st.caption(
    "Setup के बाद बनने वाला valid pullback ही "
    "उस setup की manipulation को define करेगा."
)


manipulation_rows = []


# ============================================================
# PROCESS EACH SETUP
# ============================================================

for _, setup in setups.iterrows():

    setup_id = int(
        setup["setup_id"]
    )

    setup_date = (
        setup["ny_date"]
    )

    setup_time = (
        setup["setup_time"]
    )

    setup_bar_index = int(
        setup["bar_index"]
    )


    setup_pullback = after_setup[
        after_setup["setup_id"] == setup_id
    ]


    # --------------------------------------------------------
    # NO PULLBACK
    # --------------------------------------------------------

    if setup_pullback.empty:

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "direction": None,
                "pullback_bar_index": None,
                "pullback_datetime": None,
                "c1_bar_index": None,
                "c1_price_high": None,
                "c1_price_low": None,
                "c2_bar_index": None,
                "c2_high": None,
                "c2_low": None,
                "c2_close": None,
                "c3_bar_index": None,
                "c3_close": None,
                "manipulation_point_type": None,
                "manipulation_point_price": None,
                "manipulation_point_bar_index": None,
                "manipulation_leg": None,
                "manipulation_found": False
            }
        )

        continue


    pullback_info = (
        setup_pullback.iloc[0]
    )


    if not bool(
        pullback_info[
            "pullback_found"
        ]
    ):

        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "direction": None,
                "pullback_bar_index": None,
                "pullback_datetime": None,
                "c1_bar_index": None,
                "c1_price_high": None,
                "c1_price_low": None,
                "c2_bar_index": None,
                "c2_high": None,
                "c2_low": None,
                "c2_close": None,
                "c3_bar_index": None,
                "c3_close": None,
                "manipulation_point_type": None,
                "manipulation_point_price": None,
                "manipulation_point_bar_index": None,
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


    # ========================================================
    # BULLISH
    # ========================================================

    if direction == "Bullish":

        c2_bar_index = int(
            pullback_info[
                "c2_bar_index"
            ]
        )

        c2_low = float(
            pullback_info[
                "c2_low"
            ]
        )


        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "direction": "Bullish",
                "pullback_bar_index": pullback_bar_index,
                "pullback_datetime": (
                    pullback_info[
                        "pullback_datetime"
                    ]
                ),
                "c1_bar_index": int(
                    pullback_info[
                        "c1_bar_index"
                    ]
                ),
                "c1_price_high": float(
                    pullback_info[
                        "c1_high"
                    ]
                ),
                "c1_price_low": float(
                    pullback_info[
                        "c1_low"
                    ]
                ),
                "c2_bar_index": c2_bar_index,
                "c2_high": float(
                    pullback_info[
                        "c2_high"
                    ]
                ),
                "c2_low": c2_low,
                "c2_close": float(
                    pullback_info[
                        "c2_close"
                    ]
                ),
                "c3_bar_index": int(
                    pullback_info[
                        "c3_bar_index"
                    ]
                ),
                "c3_close": float(
                    pullback_info[
                        "c3_close"
                    ]
                ),
                "manipulation_point_type": "Swing Low",
                "manipulation_point_price": c2_low,
                "manipulation_point_bar_index": c2_bar_index,
                "manipulation_leg": "High → Low",
                "manipulation_found": True
            }
        )


    # ========================================================
    # BEARISH
    # ========================================================

    elif direction == "Bearish":

        c2_bar_index = int(
            pullback_info[
                "c2_bar_index"
            ]
        )

        c2_high = float(
            pullback_info[
                "c2_high"
            ]
        )


        manipulation_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "setup_bar_index": setup_bar_index,
                "direction": "Bearish",
                "pullback_bar_index": pullback_bar_index,
                "pullback_datetime": (
                    pullback_info[
                        "pullback_datetime"
                    ]
                ),
                "c1_bar_index": int(
                    pullback_info[
                        "c1_bar_index"
                    ]
                ),
                "c1_price_high": float(
                    pullback_info[
                        "c1_high"
                    ]
                ),
                "c1_price_low": float(
                    pullback_info[
                        "c1_low"
                    ]
                ),
                "c2_bar_index": c2_bar_index,
                "c2_high": c2_high,
                "c2_low": float(
                    pullback_info[
                        "c2_low"
                    ]
                ),
                "c2_close": float(
                    pullback_info[
                        "c2_close"
                    ]
                ),
                "c3_bar_index": int(
                    pullback_info[
                        "c3_bar_index"
                    ]
                ),
                "c3_close": float(
                    pullback_info[
                        "c3_close"
                    ]
                ),
                "manipulation_point_type": "Swing High",
                "manipulation_point_price": c2_high,
                "manipulation_point_bar_index": c2_bar_index,
                "manipulation_leg": "Low → High",
                "manipulation_found": True
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

if len(manipulation) > 0:

    manipulation_found_count = int(
        manipulation[
            "manipulation_found"
        ].sum()
    )

else:

    manipulation_found_count = 0


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

    manipulation_display = [
        "setup_id",
        "setup_date",
        "setup_time",
        "direction",
        "pullback_bar_index",
        "c1_bar_index",
        "c1_price_high",
        "c1_price_low",
        "c2_bar_index",
        "c2_high",
        "c2_low",
        "c2_close",
        "c3_bar_index",
        "c3_close",
        "manipulation_point_type",
        "manipulation_point_price",
        "manipulation_point_bar_index",
        "manipulation_leg",
        "manipulation_found"
    ]

    manipulation_display = [
        c
        for c in manipulation_display
        if c in manipulation.columns
    ]

    st.dataframe(
        manipulation[
            manipulation_display
        ],
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
    "AOX levels अभी display/configuration के रूप में हैं. "
    "Exact customized Fibonacci price calculation "
    "जानबूझकर नहीं जोड़ी गई है."
)


col1, col2, col3 = st.columns(3)

with col1:

    st.write(
        "**AOX Levels**"
    )

    st.write(
        AOX_LEVELS
    )

with col2:

    st.write(
        "**AOX Entry Levels**"
    )

    st.write(
        AOX_ENTRY_LEVELS
    )

with col3:

    st.write(
        "**AOX Reference Levels**"
    )

    st.write(
        AOX_TARGET_REFERENCE_LEVELS
    )


st.caption(
    "Bullish AOX orientation: High → Low"
)

st.caption(
    "Bearish AOX orientation: Low → High"
)

st.caption(
    "पहला valid AOX entry ही लिया जाएगा."
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
# CURRENT PIPELINE STATUS
# ============================================================

st.divider()

if manipulation_found_count > 0:

    st.success(
        "✅ Data → 8:30/9:30 Setup → "
        "Valid Pullback → C2 Manipulation "
        "pipeline loaded successfully."
    )

else:

    st.warning(
        "⚠️ Current data में setup के बाद "
        "कोई valid C2 manipulation नहीं मिला."
    )


# ============================================================
# NEXT MODULE
# ============================================================

st.info(
    "Next module: AOX customized Fibonacci calculation → "
    "first valid AOX entry → "
    "2-position SL/TP simulation → "
    "performance report."
)
