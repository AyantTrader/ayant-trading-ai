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
# VALID PULLBACK DETECTION
# ============================================================

def detect_valid_pullbacks(df):

    rows = []

    n = len(df)

    if n < 3:
        return pd.DataFrame()

    # --------------------------------------------------------
    # IMPORTANT INTERPRETATION
    #
    # Bullish market:
    # - Pullback consists of bearish candles.
    # - Reference = highest bullish candle immediately
    #   before the pullback sequence.
    # - Reference Low must be grabbed.
    # - After grab, reference High must CLOSE above.
    #
    # Bearish market:
    # - Pullback consists of bullish candles.
    # - Reference = lowest bearish candle immediately
    #   before the pullback sequence.
    # - Reference High must be grabbed.
    # - After grab, reference Low must CLOSE below.
    #
    # "Grab" requires only price to go beyond the level.
    # Close is NOT required for the grab.
    #
    # Break requires CLOSE beyond the level.
    # --------------------------------------------------------

    i = 1

    while i < n:

        # ====================================================
        # BULLISH MARKET
        # ====================================================

        # A bullish candle can be the reference candle.
        if df["close"].iloc[i] > df["open"].iloc[i]:

            reference_index = i

            reference_high = float(
                df["high"].iloc[i]
            )

            reference_low = float(
                df["low"].iloc[i]
            )

            # ------------------------------------------------
            # Look for bearish pullback candles after the
            # bullish reference candle.
            # ------------------------------------------------

            j = i + 1

            pullback_indices = []

            low_grabbed = False

            while j < n:

                candle_open = float(
                    df["open"].iloc[j]
                )

                candle_high = float(
                    df["high"].iloc[j]
                )

                candle_low = float(
                    df["low"].iloc[j]
                )

                candle_close = float(
                    df["close"].iloc[j]
                )

                # --------------------------------------------
                # A bullish candle before the pullback begins
                # means the previous reference is not the
                # immediate pullback reference.
                #
                # Continue scanning for the next possible
                # bullish reference.
                # --------------------------------------------

                if candle_close > candle_open:

                    break

                # Candle is bearish.

                pullback_indices.append(j)

                # --------------------------------------------
                # Grab of reference LOW.
                #
                # Only price going below the low is required.
                # Wick OR close below = valid grab.
                # --------------------------------------------

                if candle_low < reference_low:

                    low_grabbed = True

                # --------------------------------------------
                # After LOW is grabbed, reference HIGH must
                # be BROKEN by CLOSE.
                # --------------------------------------------

                if (
                    low_grabbed
                    and candle_close > reference_high
                ):

                    c1_index = reference_index

                    c2_index = (
                        pullback_indices[0]
                        if len(pullback_indices) >= 1
                        else j
                    )

                    # ------------------------------------------------
                    # C2 for manipulation is the candle that actually
                    # grabbed the reference low.
                    #
                    # If the grab happened later in the pullback,
                    # use that actual grab candle.
                    # ------------------------------------------------

                    grab_index = None

                    for k in pullback_indices:

                        if (
                            float(df["low"].iloc[k])
                            < reference_low
                        ):

                            grab_index = k
                            break

                    if grab_index is None:
                        grab_index = c2_index

                    c3_index = j

                    rows.append(
                        {
                            "datetime": df["datetime"].iloc[c3_index],

                            "direction": "Bullish",

                            "reference_bar_index": int(
                                reference_index
                            ),

                            "reference_datetime": df[
                                "datetime"
                            ].iloc[reference_index],

                            "reference_high": reference_high,

                            "reference_low": reference_low,

                            "c1_bar_index": int(
                                c1_index
                            ),

                            "c2_bar_index": int(
                                grab_index
                            ),

                            "c3_bar_index": int(
                                c3_index
                            ),

                            "c1_high": float(
                                df["high"].iloc[c1_index]
                            ),

                            "c1_low": float(
                                df["low"].iloc[c1_index]
                            ),

                            "c2_high": float(
                                df["high"].iloc[grab_index]
                            ),

                            "c2_low": float(
                                df["low"].iloc[grab_index]
                            ),

                            "c2_close": float(
                                df["close"].iloc[grab_index]
                            ),

                            "c3_close": float(
                                df["close"].iloc[c3_index]
                            ),

                            # ----------------------------------------
                            # Manipulation point
                            # ----------------------------------------

                            "manipulation_point_type":
                                "Swing Low",

                            "manipulation_point_price":
                                float(
                                    df["low"].iloc[grab_index]
                                ),

                            "manipulation_point_bar_index":
                                int(grab_index),

                            "manipulation_leg":
                                "High → Low",

                            "pullback_confirmed": True
                        }
                    )

                    # Move forward after confirmation so the same
                    # pattern is not repeatedly counted.
                    i = j

                    break

                j += 1

        # ====================================================
        # BEARISH MARKET
        # ====================================================

        if (
            i < n
            and df["close"].iloc[i]
            < df["open"].iloc[i]
        ):

            reference_index = i

            reference_high = float(
                df["high"].iloc[i]
            )

            reference_low = float(
                df["low"].iloc[i]
            )

            j = i + 1

            pullback_indices = []

            high_grabbed = False

            while j < n:

                candle_open = float(
                    df["open"].iloc[j]
                )

                candle_high = float(
                    df["high"].iloc[j]
                )

                candle_low = float(
                    df["low"].iloc[j]
                )

                candle_close = float(
                    df["close"].iloc[j]
                )

                # Another bearish candle means the previous
                # reference is no longer the immediate
                # pullback reference.

                if candle_close < candle_open:

                    break

                # Candle is bullish.

                pullback_indices.append(j)

                # --------------------------------------------
                # Grab of reference HIGH.
                #
                # Price only needs to go above the high.
                # Wick OR close above = valid grab.
                # --------------------------------------------

                if candle_high > reference_high:

                    high_grabbed = True

                # --------------------------------------------
                # After HIGH is grabbed, reference LOW must
                # be broken by CLOSE.
                # --------------------------------------------

                if (
                    high_grabbed
                    and candle_close < reference_low
                ):

                    c1_index = reference_index

                    c2_index = (
                        pullback_indices[0]
                        if len(pullback_indices) >= 1
                        else j
                    )

                    # ------------------------------------------------
                    # Actual candle that grabbed reference HIGH.
                    # ------------------------------------------------

                    grab_index = None

                    for k in pullback_indices:

                        if (
                            float(df["high"].iloc[k])
                            > reference_high
                        ):

                            grab_index = k
                            break

                    if grab_index is None:
                        grab_index = c2_index

                    c3_index = j

                    rows.append(
                        {
                            "datetime": df["datetime"].iloc[c3_index],

                            "direction": "Bearish",

                            "reference_bar_index": int(
                                reference_index
                            ),

                            "reference_datetime": df[
                                "datetime"
                            ].iloc[reference_index],

                            "reference_high": reference_high,

                            "reference_low": reference_low,

                            "c1_bar_index": int(
                                c1_index
                            ),

                            "c2_bar_index": int(
                                grab_index
                            ),

                            "c3_bar_index": int(
                                c3_index
                            ),

                            "c1_high": float(
                                df["high"].iloc[c1_index]
                            ),

                            "c1_low": float(
                                df["low"].iloc[c1_index]
                            ),

                            "c2_high": float(
                                df["high"].iloc[grab_index]
                            ),

                            "c2_low": float(
                                df["low"].iloc[grab_index]
                            ),

                            "c2_close": float(
                                df["close"].iloc[grab_index]
                            ),

                            "c3_close": float(
                                df["close"].iloc[c3_index]
                            ),

                            "manipulation_point_type":
                                "Swing High",

                            "manipulation_point_price":
                                float(
                                    df["high"].iloc[grab_index]
                                ),

                            "manipulation_point_bar_index":
                                int(grab_index),

                            "manipulation_leg":
                                "Low → High",

                            "pullback_confirmed": True
                        }
                    )

                    i = j

                    break

                j += 1

        i += 1

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    result = (
        result
        .sort_values("c3_bar_index")
        .drop_duplicates(
            subset=[
                "c3_bar_index",
                "direction"
            ],
            keep="first"
        )
        .reset_index(drop=True)
    )

    return result


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

    start_time = df[
        "datetime"
    ].iloc[0]

    st.metric(
        "Start",
        start_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

with c3:

    end_time = df[
        "datetime"
    ].iloc[-1]

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
    "Bullish: highest bullish reference candle → "
    "its Low is grabbed → after the grab its High "
    "must be broken by candle CLOSE."
)

st.caption(
    "Bearish: lowest bearish reference candle → "
    "its High is grabbed → after the grab its Low "
    "must be broken by candle CLOSE."
)


pullbacks = detect_valid_pullbacks(
    df
)


if pullbacks.empty:

    total_pullbacks = 0
    bullish_count = 0
    bearish_count = 0

else:

    total_pullbacks = len(
        pullbacks
    )

    bullish_count = int(
        (
            pullbacks["direction"]
            == "Bullish"
        ).sum()
    )

    bearish_count = int(
        (
            pullbacks["direction"]
            == "Bearish"
        ).sum()
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

    if not pullbacks.empty:

        display_columns = [
            "datetime",
            "direction",
            "reference_bar_index",
            "reference_datetime",
            "reference_high",
            "reference_low",
            "c1_bar_index",
            "c2_bar_index",
            "c3_bar_index",
            "c2_high",
            "c2_low",
            "c2_close",
            "c3_close",
            "manipulation_point_type",
            "manipulation_point_price",
            "manipulation_point_bar_index",
            "manipulation_leg"
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

    else:

        st.info(
            "No valid pullbacks detected."
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
    "Valid pullback confirm होने के बाद "
    "उसके manipulation point को आगे AOX के लिए use किया जाएगा."
)


after_setup_rows = []


for _, setup in setups.iterrows():

    setup_date = setup[
        "ny_date"
    ]

    setup_bar_index = int(
        setup[
            "bar_index"
        ]
    )

    setup_time = setup[
        "setup_time"
    ]

    if pullbacks.empty:

        after_setup_rows.append(
            {
                "setup_id":
                    setup["setup_id"],

                "setup_date":
                    setup_date,

                "setup_time":
                    setup_time,

                "setup_bar_index":
                    setup_bar_index,

                "pullback_found":
                    False,

                "pullback_direction":
                    None,

                "pullback_bar_index":
                    None,

                "pullback_datetime":
                    None,

                "manipulation_point_type":
                    None,

                "manipulation_point_price":
                    None,

                "manipulation_point_bar_index":
                    None,

                "manipulation_leg":
                    None
            }
        )

        continue


    candidates = pullbacks[
        (pullbacks["ny_date"] == setup_date)
        &
        (
            pullbacks["c3_bar_index"]
            > setup_bar_index
        )
    ]


    if candidates.empty:

        after_setup_rows.append(
            {
                "setup_id":
                    setup["setup_id"],

                "setup_date":
                    setup_date,

                "setup_time":
                    setup_time,

                "setup_bar_index":
                    setup_bar_index,

                "pullback_found":
                    False,

                "pullback_direction":
                    None,

                "pullback_bar_index":
                    None,

                "pullback_datetime":
                    None,

                "manipulation_point_type":
                    None,

                "manipulation_point_price":
                    None,

                "manipulation_point_bar_index":
                    None,

                "manipulation_leg":
                    None
            }
        )

        continue


    first_pullback = (
        candidates
        .sort_values(
            "c3_bar_index"
        )
        .iloc[0]
    )


    after_setup_rows.append(
        {
            "setup_id":
                setup["setup_id"],

            "setup_date":
                setup_date,

            "setup_time":
                setup_time,

            "setup_bar_index":
                setup_bar_index,

            "pullback_found":
                True,

            "pullback_direction":
                first_pullback[
                    "direction"
                ],

            "pullback_bar_index":
                int(
                    first_pullback[
                        "c3_bar_index"
                    ]
                ),

            "pullback_datetime":
                first_pullback[
                    "datetime"
                ],

            "manipulation_point_type":
                first_pullback[
                    "manipulation_point_type"
                ],

            "manipulation_point_price":
                float(
                    first_pullback[
                        "manipulation_point_price"
                    ]
                ),

            "manipulation_point_bar_index":
                int(
                    first_pullback[
                        "manipulation_point_bar_index"
                    ]
                ),

            "manipulation_leg":
                first_pullback[
                    "manipulation_leg"
                ]
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
        "📋 View Setup → Pullback → Manipulation Mapping"
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
    "left और right candle के High से बड़ा."
)

st.caption(
    "Swing Low = बीच वाली candle का Low "
    "left और right candle के Low से छोटा."
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
# MANIPULATION MAPPING
# ============================================================

st.divider()

st.header(
    "🧭 LEFT-SIDE Manipulation"
)

st.caption(
    "Setup के बाद पहला valid pullback ही "
    "manipulation leg को confirm करता है."
)

st.caption(
    "Bullish → C2 का LOW = Manipulation Swing Low"
)

st.caption(
    "Bearish → C2 का HIGH = Manipulation Swing High"
)


manipulation_rows = []


for _, row in after_setup.iterrows():

    if not bool(
        row["pullback_found"]
    ):

        manipulation_rows.append(
            {
                "setup_id":
                    row["setup_id"],

                "setup_date":
                    row["setup_date"],

                "setup_time":
                    row["setup_time"],

                "direction":
                    None,

                "pullback_bar_index":
                    None,

                "manipulation_point_type":
                    None,

                "manipulation_point_bar_index":
                    None,

                "manipulation_point_price":
                    None,

                "manipulation_leg":
                    None,

                "manipulation_found":
                    False
            }
        )

        continue


    manipulation_rows.append(
        {
            "setup_id":
                row["setup_id"],

            "setup_date":
                row["setup_date"],

            "setup_time":
                row["setup_time"],

            "direction":
                row["pullback_direction"],

            "pullback_bar_index":
                row["pullback_bar_index"],

            "manipulation_point_type":
                row["manipulation_point_type"],

            "manipulation_point_bar_index":
                row["manipulation_point_bar_index"],

            "manipulation_point_price":
                row["manipulation_point_price"],

            "manipulation_leg":
                row["manipulation_leg"],

            "manipulation_found":
                True
        }
    )


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


with st.expander(
    "📋 View Manipulation Mapping"
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
    "AOX levels configured हैं. "
    "Actual Fibonacci price calculation अभी intentionally "
    "apply नहीं की गई है."
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
        "✅ Data → Setup → Valid Pullback → "
        "C2 Manipulation Point mapping "
        "pipeline loaded successfully."
    )

else:

    st.warning(
        "⚠️ No valid setup → pullback → "
        "manipulation mapping was found."
    )


st.info(
    "Next module: AOX Fibonacci → First valid AOX entry → "
    "2-position SL/TP simulation → Performance report."
)
