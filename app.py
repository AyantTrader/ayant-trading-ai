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
# AOX CUSTOMIZED FIBONACCI CALCULATION
# ============================================================

def calculate_aox_levels(
    direction,
    manipulation_high,
    manipulation_low
):

    if direction == "Bullish":

        fib_0_price = float(
            manipulation_low
        )

        fib_1_price = float(
            manipulation_high
        )

    elif direction == "Bearish":

        fib_0_price = float(
            manipulation_high
        )

        fib_1_price = float(
            manipulation_low
        )

    else:

        raise ValueError(
            f"Invalid AOX direction: {direction}"
        )

    price_range = (
        fib_1_price
        - fib_0_price
    )

    result = {}

    for level in AOX_LEVELS:

        price = (
            fib_0_price
            + (
                float(level)
                * price_range
            )
        )

        result[float(level)] = float(
            price
        )

    return {
        "fib_0_price": fib_0_price,
        "fib_1_price": fib_1_price,
        "range": price_range,
        "levels": result
    }


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

bullish_mask = (
    (c2_low < c1_low)
    &
    (c3_close > c1_high)
)


# ============================================================
# BEARISH VALID PULLBACK
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
# AOX CUSTOMIZED FIBONACCI
# ============================================================

st.divider()

st.header(
    "📐 AOX Customized Fibonacci"
)

st.caption(
    "Bullish: Low = Fib 0, High = Fib 1."
)

st.caption(
    "Bearish: High = Fib 0, Low = Fib 1."
)

st.caption(
    "Price = Fib 0 + Level × (Fib 1 − Fib 0)."
)


aox_rows = []


# ============================================================
# CALCULATE AOX FOR EVERY VALID MANIPULATION
# ============================================================

for _, row in manipulation.iterrows():

    if not bool(
        row["manipulation_found"]
    ):

        continue


    direction = (
        row["direction"]
    )


    c2_bar_index = int(
        row["c2_bar_index"]
    )


    # --------------------------------------------------------
    # MANIPULATION CANDLE HIGH / LOW
    # --------------------------------------------------------

    manipulation_candle = df.loc[
        df["bar_index"] == c2_bar_index
    ]


    if manipulation_candle.empty:

        continue


    manipulation_candle = (
        manipulation_candle.iloc[0]
    )


    manipulation_high = float(
        manipulation_candle["high"]
    )

    manipulation_low = float(
        manipulation_candle["low"]
    )


    # --------------------------------------------------------
    # CALCULATE CUSTOM FIB
    # --------------------------------------------------------

    aox = calculate_aox_levels(
        direction=direction,
        manipulation_high=manipulation_high,
        manipulation_low=manipulation_low
    )


    level_prices = (
        aox["levels"]
    )


    # --------------------------------------------------------
    # ENTRY LEVEL PRICES
    # --------------------------------------------------------

    entry_price_minus_021 = level_prices[
        -0.210
    ]

    entry_price_minus_0255 = level_prices[
        -0.255
    ]

    entry_price_minus_029 = level_prices[
        -0.290
    ]


    # --------------------------------------------------------
    # TARGET / REFERENCE LEVEL PRICES
    # --------------------------------------------------------

    reference_price_256 = level_prices[
        2.560
    ]

    reference_price_260 = level_prices[
        2.600
    ]

    reference_price_264 = level_prices[
        2.640
    ]


    # --------------------------------------------------------
    # SAVE AOX ROW
    # --------------------------------------------------------

    aox_rows.append(
        {
            "setup_id": int(
                row["setup_id"]
            ),
            "setup_date": row[
                "setup_date"
            ],
            "setup_time": row[
                "setup_time"
            ],
            "direction": direction,
            "pullback_bar_index": int(
                row["pullback_bar_index"]
            ),
            "c2_bar_index": c2_bar_index,

            "manipulation_high": (
                manipulation_high
            ),

            "manipulation_low": (
                manipulation_low
            ),

            "fib_0_price": (
                aox["fib_0_price"]
            ),

            "fib_1_price": (
                aox["fib_1_price"]
            ),

            "fib_range": (
                aox["range"]
            ),

            "aox_-0.210": (
                entry_price_minus_021
            ),

            "aox_-0.255": (
                entry_price_minus_0255
            ),

            "aox_-0.290": (
                entry_price_minus_029
            ),

            "aox_1.470": (
                level_prices[
                    1.470
                ]
            ),

            "aox_1.550": (
                level_prices[
                    1.550
                ]
            ),

            "aox_2.560": (
                reference_price_256
            ),

            "aox_2.600": (
                reference_price_260
            ),

            "aox_2.640": (
                reference_price_264
            )
        }
    )


# ============================================================
# AOX DATAFRAME
# ============================================================

aox_calculations = pd.DataFrame(
    aox_rows
)


# ============================================================
# AOX SUMMARY
# ============================================================

aox_calculation_count = len(
    aox_calculations
)


st.metric(
    "AOX Calculations",
    f"{aox_calculation_count:,}"
)


# ============================================================
# AOX CALCULATION TABLE
# ============================================================

with st.expander(
    "📋 View AOX Calculated Prices"
):

    aox_display_columns = [
        "setup_id",
        "setup_date",
        "setup_time",
        "direction",
        "pullback_bar_index",
        "c2_bar_index",
        "manipulation_high",
        "manipulation_low",
        "fib_0_price",
        "fib_1_price",
        "fib_range",
        "aox_-0.210",
        "aox_-0.255",
        "aox_-0.290",
        "aox_1.470",
        "aox_1.550",
        "aox_2.560",
        "aox_2.600",
        "aox_2.640"
    ]

    aox_display_columns = [
        c
        for c in aox_display_columns
        if c in aox_calculations.columns
    ]

    st.dataframe(
        aox_calculations[
            aox_display_columns
        ],
        use_container_width=True
    )


# ============================================================
# AOX FIRST VALID ENTRY DETECTION
# ============================================================

st.divider()

st.header(
    "🎯 AOX First Valid Entry Detection"
)

st.caption(
    "हर setup में AOX के -0.21, -0.255 और -0.29 "
    "entry levels में से पहला valid tap लिया जाएगा."
)

st.caption(
    "एक ही 1-minute candle में multiple AOX entry levels "
    "touch हों और OHLC से intrabar order निश्चित न हो, "
    "तो entry AMBIGUOUS मानी जाएगी."
)

st.caption(
    "AMBIGUOUS candle पर कोई level guess नहीं किया जाएगा."
)


# ============================================================
# ENTRY DETECTION ROWS
# ============================================================

aox_entry_rows = []


# ============================================================
# PROCESS EVERY AOX SETUP
# ============================================================

for _, aox_row in aox_calculations.iterrows():

    setup_id = int(
        aox_row["setup_id"]
    )

    setup_date = (
        aox_row["setup_date"]
    )

    setup_time = (
        aox_row["setup_time"]
    )

    direction = (
        aox_row["direction"]
    )

    pullback_bar_index = int(
        aox_row["pullback_bar_index"]
    )


    # --------------------------------------------------------
    # ENTRY LEVEL PRICE MAP
    # --------------------------------------------------------

    entry_levels = {
        -0.210: float(
            aox_row["aox_-0.210"]
        ),
        -0.255: float(
            aox_row["aox_-0.255"]
        ),
        -0.290: float(
            aox_row["aox_-0.290"]
        )
    }


    # --------------------------------------------------------
    # ONLY SEARCH AFTER THE VALID PULLBACK
    # --------------------------------------------------------

    future_bars = df[
        df["bar_index"] > pullback_bar_index
    ].copy()


    if future_bars.empty:

        aox_entry_rows.append(
            {
                "setup_id": setup_id,
                "setup_date": setup_date,
                "setup_time": setup_time,
                "direction": direction,
                "pullback_bar_index": pullback_bar_index,
                "entry_found": False,
                "entry_status": "NO_ENTRY",
                "entry_level": None,
                "entry_price": None,
                "entry_bar_index": None,
                "entry_datetime": None
            }
        )

        continue


    # --------------------------------------------------------
    # FIND FIRST CANDLE TOUCHING AOX ENTRY LEVEL(S)
    # --------------------------------------------------------

    entry_found = False

    entry_status = "NO_ENTRY"

    selected_level = None

    selected_price = None

    selected_bar_index = None

    selected_datetime = None


    for _, candle in future_bars.iterrows():

        candle_high = float(
            candle["high"]
        )

        candle_low = float(
            candle["low"]
        )


        touched_levels = []


        # ----------------------------------------------------
        # CHECK EVERY AOX ENTRY LEVEL
        # ----------------------------------------------------

        for level, level_price in entry_levels.items():

            if (
                candle_low
                <= level_price
                <= candle_high
            ):

                touched_levels.append(
                    (
                        level,
                        level_price
                    )
                )


        # ----------------------------------------------------
        # NO AOX ENTRY LEVEL TOUCHED
        # ----------------------------------------------------

        if len(touched_levels) == 0:

            continue


        # ----------------------------------------------------
        # EXACTLY ONE AOX ENTRY LEVEL TOUCHED
        # ----------------------------------------------------

        if len(touched_levels) == 1:

            selected_level = float(
                touched_levels[0][0]
            )

            selected_price = float(
                touched_levels[0][1]
            )

            selected_bar_index = int(
                candle["bar_index"]
            )

            selected_datetime = (
                candle["datetime"]
            )

            entry_found = True

            entry_status = "VALID_ENTRY"

            break


        # ----------------------------------------------------
        # MULTIPLE ENTRY LEVELS TOUCHED IN SAME CANDLE
        # ----------------------------------------------------

        if len(touched_levels) > 1:

            selected_bar_index = int(
                candle["bar_index"]
            )

            selected_datetime = (
                candle["datetime"]
            )

            entry_found = False

            entry_status = "AMBIGUOUS"

            break


    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    aox_entry_rows.append(
        {
            "setup_id": setup_id,
            "setup_date": setup_date,
            "setup_time": setup_time,
            "direction": direction,
            "pullback_bar_index": pullback_bar_index,
            "entry_found": entry_found,
            "entry_status": entry_status,
            "entry_level": selected_level,
            "entry_price": selected_price,
            "entry_bar_index": selected_bar_index,
            "entry_datetime": selected_datetime
        }
    )


# ============================================================
# AOX ENTRY DATAFRAME
# ============================================================

aox_entries = pd.DataFrame(
    aox_entry_rows
)


# ============================================================
# AOX ENTRY SUMMARY
# ============================================================

if len(aox_entries) > 0:

    valid_entry_count = int(
        (
            aox_entries[
                "entry_status"
            ]
            == "VALID_ENTRY"
        ).sum()
    )

    ambiguous_entry_count = int(
        (
            aox_entries[
                "entry_status"
            ]
            == "AMBIGUOUS"
        ).sum()
    )

    no_entry_count = int(
        (
            aox_entries[
                "entry_status"
            ]
            == "NO_ENTRY"
        ).sum()
    )

else:

    valid_entry_count = 0
    ambiguous_entry_count = 0
    no_entry_count = 0


e1, e2, e3 = st.columns(3)

with e1:

    st.metric(
        "Valid AOX Entries",
        f"{valid_entry_count:,}"
    )

with e2:

    st.metric(
        "Ambiguous Entries",
        f"{ambiguous_entry_count:,}"
    )

with e3:

    st.metric(
        "No Entry",
        f"{no_entry_count:,}"
    )


# ============================================================
# AOX ENTRY TABLE
# ============================================================

with st.expander(
    "📋 View AOX First Valid Entries"
):

    aox_entry_display = [
        "setup_id",
        "setup_date",
        "setup_time",
        "direction",
        "pullback_bar_index",
        "entry_found",
        "entry_status",
        "entry_level",
        "entry_price",
        "entry_bar_index",
        "entry_datetime"
    ]

    aox_entry_display = [
        c
        for c in aox_entry_display
        if c in aox_entries.columns
    ]

    st.dataframe(
        aox_entries[
            aox_entry_display
        ],
        use_container_width=True
    )


# ============================================================
# 2-POSITION SL/TP SIMULATION
# ============================================================

st.divider()

st.header(
    "📊 2-Position SL/TP Simulation"
)

st.caption(
    "हर valid AOX entry पर 2 independent positions "
    "simulate की जाएंगी."
)

st.caption(
    "Trade 1: SL = 5.000, TP = 15.000."
)

st.caption(
    "Trade 2: SL = 5.000, TP = 20.000."
)

st.caption(
    "एक ही candle में SL और TP दोनों touch होने पर "
    "result AMBIGUOUS माना जाएगा."
)

st.caption(
    "Entry candle में exit level touch होने पर भी "
    "intrabar order निश्चित नहीं होने के कारण "
    "result AMBIGUOUS माना जाएगा."
)


# ============================================================
# SL/TP SIMULATION FUNCTION
# ============================================================

def simulate_position(
    direction,
    entry_price,
    entry_bar_index,
    sl_distance,
    tp_distance,
    position_name
):

    entry_price = float(
        entry_price
    )

    entry_bar_index = int(
        entry_bar_index
    )

    sl_distance = float(
        sl_distance
    )

    tp_distance = float(
        tp_distance
    )


    # --------------------------------------------------------
    # CALCULATE SL / TP PRICES
    # --------------------------------------------------------

    if direction == "Bullish":

        sl_price = (
            entry_price
            - sl_distance
        )

        tp_price = (
            entry_price
            + tp_distance
        )

    elif direction == "Bearish":

        sl_price = (
            entry_price
            + sl_distance
        )

        tp_price = (
            entry_price
            - tp_distance
        )

    else:

        return {
            "position": position_name,
            "status": "INVALID_DIRECTION",
            "entry_price": entry_price,
            "sl_price": None,
            "tp_price": None,
            "exit_price": None,
            "exit_bar_index": None,
            "exit_datetime": None,
            "result_r": None
        }


    # --------------------------------------------------------
    # SEARCH FROM ENTRY CANDLE ONWARD
    # --------------------------------------------------------

    trade_bars = df[
        df["bar_index"] >= entry_bar_index
    ].copy()


    if trade_bars.empty:

        return {
            "position": position_name,
            "status": "NO_EXIT",
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "exit_price": None,
            "exit_bar_index": None,
            "exit_datetime": None,
            "result_r": None
        }


    # --------------------------------------------------------
    # PROCESS CANDLES
    # --------------------------------------------------------

    for _, candle in trade_bars.iterrows():

        candle_bar_index = int(
            candle["bar_index"]
        )

        candle_high = float(
            candle["high"]
        )

        candle_low = float(
            candle["low"]
        )

        candle_datetime = (
            candle["datetime"]
        )


        # ----------------------------------------------------
        # BULLISH
        # ----------------------------------------------------

        if direction == "Bullish":

            sl_touched = (
                candle_low
                <= sl_price
            )

            tp_touched = (
                candle_high
                >= tp_price
            )


        # ----------------------------------------------------
        # BEARISH
        # ----------------------------------------------------

        else:

            sl_touched = (
                candle_high
                >= sl_price
            )

            tp_touched = (
                candle_low
                <= tp_price
            )


        # ----------------------------------------------------
        # BOTH SL AND TP TOUCHED
        # ----------------------------------------------------

        if sl_touched and tp_touched:

            return {
                "position": position_name,
                "status": "AMBIGUOUS",
                "entry_price": entry_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "exit_price": None,
                "exit_bar_index": candle_bar_index,
                "exit_datetime": candle_datetime,
                "result_r": None
            }


        # ----------------------------------------------------
        # ONLY SL TOUCHED
        # ----------------------------------------------------

        if sl_touched:

            return {
                "position": position_name,
                "status": "SL",
                "entry_price": entry_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "exit_price": sl_price,
                "exit_bar_index": candle_bar_index,
                "exit_datetime": candle_datetime,
                "result_r": -1.0
            }


        # ----------------------------------------------------
        # ONLY TP TOUCHED
        # ----------------------------------------------------

        if tp_touched:

            if position_name == "Trade 1":

                result_r = 3.0

            else:

                result_r = 4.0


            return {
                "position": position_name,
                "status": "TP",
                "entry_price": entry_price,
                "sl_price": sl_price,
                "tp_price": tp_price,
                "exit_price": tp_price,
                "exit_bar_index": candle_bar_index,
                "exit_datetime": candle_datetime,
                "result_r": result_r
            }


    # --------------------------------------------------------
    # DATA ENDED WITHOUT EXIT
    # --------------------------------------------------------

    return {
        "position": position_name,
        "status": "NO_EXIT",
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "exit_price": None,
        "exit_bar_index": None,
        "exit_datetime": None,
        "result_r": None
    }


# ============================================================
# PROCESS VALID AOX ENTRIES
# ============================================================

trade_simulation_rows = []


valid_aox_entries = aox_entries[
    aox_entries[
        "entry_status"
    ] == "VALID_ENTRY"
].copy()


for _, entry in valid_aox_entries.iterrows():

    setup_id = int(
        entry["setup_id"]
    )

    setup_date = (
        entry["setup_date"]
    )

    setup_time = (
        entry["setup_time"]
    )

    direction = (
        entry["direction"]
    )

    entry_level = float(
        entry["entry_level"]
    )

    entry_price = float(
        entry["entry_price"]
    )

    entry_bar_index = int(
        entry["entry_bar_index"]
    )

    entry_datetime = (
        entry["entry_datetime"]
    )


    # --------------------------------------------------------
    # TRADE 1
    # --------------------------------------------------------

    trade_1 = simulate_position(
        direction=direction,
        entry_price=entry_price,
        entry_bar_index=entry_bar_index,
        sl_distance=TRADE_1_SL,
        tp_distance=TRADE_1_TP,
        position_name="Trade 1"
    )


    # --------------------------------------------------------
    # TRADE 2
    # --------------------------------------------------------

    trade_2 = simulate_position(
        direction=direction,
        entry_price=entry_price,
        entry_bar_index=entry_bar_index,
        sl_distance=TRADE_2_SL,
        tp_distance=TRADE_2_TP,
        position_name="Trade 2"
    )


    # --------------------------------------------------------
    # COMBINED R
    # --------------------------------------------------------

    if (
        trade_1["result_r"] is not None
        and
        trade_2["result_r"] is not None
    ):

        combined_r = (
            trade_1["result_r"]
            +
            trade_2["result_r"]
        )

    else:

        combined_r = None


    # --------------------------------------------------------
    # SAVE TRADE RESULT
    # --------------------------------------------------------

    trade_simulation_rows.append(
        {
            "setup_id": setup_id,
            "setup_date": setup_date,
            "setup_time": setup_time,
            "direction": direction,
            "entry_level": entry_level,
            "entry_price": entry_price,
            "entry_bar_index": entry_bar_index,
            "entry_datetime": entry_datetime,

            "trade_1_status": (
                trade_1["status"]
            ),

            "trade_1_sl": (
                trade_1["sl_price"]
            ),

            "trade_1_tp": (
                trade_1["tp_price"]
            ),

            "trade_1_exit_price": (
                trade_1["exit_price"]
            ),

            "trade_1_exit_bar_index": (
                trade_1["exit_bar_index"]
            ),

            "trade_1_exit_datetime": (
                trade_1["exit_datetime"]
            ),

            "trade_1_result_r": (
                trade_1["result_r"]
            ),

            "trade_2_status": (
                trade_2["status"]
            ),

            "trade_2_sl": (
                trade_2["sl_price"]
            ),

            "trade_2_tp": (
                trade_2["tp_price"]
            ),

            "trade_2_exit_price": (
                trade_2["exit_price"]
            ),

            "trade_2_exit_bar_index": (
                trade_2["exit_bar_index"]
            ),

            "trade_2_exit_datetime": (
                trade_2["exit_datetime"]
            ),

            "trade_2_result_r": (
                trade_2["result_r"]
            ),

            "combined_r": combined_r
        }
    )


# ============================================================
# TRADE SIMULATION DATAFRAME
# ============================================================

trade_simulations = pd.DataFrame(
    trade_simulation_rows
)


# ============================================================
# TRADE SIMULATION SUMMARY
# ============================================================

if len(trade_simulations) > 0:

    trade_1_tp_count = int(
        (
            trade_simulations[
                "trade_1_status"
            ]
            == "TP"
        ).sum()
    )

    trade_1_sl_count = int(
        (
            trade_simulations[
                "trade_1_status"
            ]
            == "SL"
        ).sum()
    )

    trade_1_ambiguous_count = int(
        (
            trade_simulations[
                "trade_1_status"
            ]
            == "AMBIGUOUS"
        ).sum()
    )

    trade_1_no_exit_count = int(
        (
            trade_simulations[
                "trade_1_status"
            ]
            == "NO_EXIT"
        ).sum()
    )


    trade_2_tp_count = int(
        (
            trade_simulations[
                "trade_2_status"
            ]
            == "TP"
        ).sum()
    )

    trade_2_sl_count = int(
        (
            trade_simulations[
                "trade_2_status"
            ]
            == "SL"
        ).sum()
    )

    trade_2_ambiguous_count = int(
        (
            trade_simulations[
                "trade_2_status"
            ]
            == "AMBIGUOUS"
        ).sum()
    )

    trade_2_no_exit_count = int(
        (
            trade_simulations[
                "trade_2_status"
            ]
            == "NO_EXIT"
        ).sum()
    )

else:

    trade_1_tp_count = 0
    trade_1_sl_count = 0
    trade_1_ambiguous_count = 0
    trade_1_no_exit_count = 0

    trade_2_tp_count = 0
    trade_2_sl_count = 0
    trade_2_ambiguous_count = 0
    trade_2_no_exit_count = 0


# ============================================================
# TRADE 1 SUMMARY
# ============================================================

st.subheader(
    "Trade 1 — 1:3"
)

t1a, t1b, t1c, t1d = st.columns(4)

with t1a:

    st.metric(
        "TP",
        f"{trade_1_tp_count:,}"
    )

with t1b:

    st.metric(
        "SL",
        f"{trade_1_sl_count:,}"
    )

with t1c:

    st.metric(
        "AMBIGUOUS",
        f"{trade_1_ambiguous_count:,}"
    )

with t1d:

    st.metric(
        "NO EXIT",
        f"{trade_1_no_exit_count:,}"
    )


# ============================================================
# TRADE 2 SUMMARY
# ============================================================

st.subheader(
    "Trade 2 — 1:4"
)

t2a, t2b, t2c, t2d = st.columns(4)

with t2a:

    st.metric(
        "TP",
        f"{trade_2_tp_count:,}"
    )

with t2b:

    st.metric(
        "SL",
        f"{trade_2_sl_count:,}"
    )

with t2c:

    st.metric(
        "AMBIGUOUS",
        f"{trade_2_ambiguous_count:,}"
    )

with t2d:

    st.metric(
        "NO EXIT",
        f"{trade_2_no_exit_count:,}"
    )


# ============================================================
# COMBINED R SUMMARY
# ============================================================

if len(trade_simulations) > 0:

    completed_combined = (
        trade_simulations[
            "combined_r"
        ].dropna()
    )

else:

    completed_combined = pd.Series(
        dtype=float
    )


if len(completed_combined) > 0:

    combined_r_total = float(
        completed_combined.sum()
    )

    combined_r_average = float(
        completed_combined.mean()
    )

else:

    combined_r_total = 0.0

    combined_r_average = 0.0


r1, r2, r3 = st.columns(3)

with r1:

    st.metric(
        "Valid AOX Entries Simulated",
        f"{len(trade_simulations):,}"
    )

with r2:

    st.metric(
        "Completed 2-Position Trades",
        f"{len(completed_combined):,}"
    )

with r3:

    st.metric(
        "Combined R",
        f"{combined_r_total:.2f}R"
    )


st.metric(
    "Average Combined R / Completed Trade",
    f"{combined_r_average:.2f}R"
)


# ============================================================
# TRADE SIMULATION TABLE
# ============================================================

with st.expander(
    "📋 View 2-Position SL/TP Simulation"
):

    trade_display_columns = [
        "setup_id",
        "setup_date",
        "setup_time",
        "direction",
        "entry_level",
        "entry_price",
        "entry_datetime",

        "trade_1_status",
        "trade_1_sl",
        "trade_1_tp",
        "trade_1_exit_price",
        "trade_1_exit_datetime",
        "trade_1_result_r",

        "trade_2_status",
        "trade_2_sl",
        "trade_2_tp",
        "trade_2_exit_price",
        "trade_2_exit_datetime",
        "trade_2_result_r",

        "combined_r"
    ]

    trade_display_columns = [
        c
        for c in trade_display_columns
        if c in trade_simulations.columns
    ]

    st.dataframe(
        trade_simulations[
            trade_display_columns
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

st.success(
    "AOX customized Fibonacci price calculation "
    "successfully applied to every valid manipulation."
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
    "Bullish AOX: Low → High"
)

st.caption(
    "Bearish AOX: High → Low"
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
        "Valid Pullback → C2 Manipulation → "
        "AOX Fibonacci → First Valid AOX Entry → "
        "2-Position SL/TP Simulation "
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
    "Next module: Performance report → "
    "win rate → profit factor → net R → "
    "drawdown → streaks → session/day/month breakdown."
)
