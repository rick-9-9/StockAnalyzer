import streamlit as st
from modules import fundamental, indicators
from utils.helpers import info_icon
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
from prophet import Prophet
from prophet.plot import plot_plotly
from modules.earnings import get_earnings_regressors

# Streamlit page configuration
st.set_page_config(page_title="AI Investments", layout="wide")
st.title("📈 AI-Powered Stock Analysis")

# -----------------------------
# Load ticker list from local equities.csv file
@st.cache_data
def load_local_tickers(filepath='equities.csv'):
    try:
        df = pd.read_csv(filepath)
        df = df.rename(columns={"symbol": "symbol", "name": "shortname"})
        return df[["symbol", "shortname"]]
    except Exception as e:
        st.error(f"Error loading local tickers: {e}")
        return pd.DataFrame(columns=["symbol", "shortname"])

all_tickers_df = load_local_tickers()

# -----------------------------
# Search tickers locally and fallback to Yahoo Finance search
def search_tickers(query):
    if not query:
        return pd.DataFrame(columns=["symbol", "shortname"])
    query = query.lower()
    results = all_tickers_df[
        all_tickers_df["symbol"].str.lower().str.contains(query) |
        all_tickers_df["shortname"].str.lower().str.contains(query)
    ]
    if results.empty:
        try:
            yf_results = yf.search(query)
            if yf_results is not None and not yf_results.empty:
                return yf_results[["symbol", "shortname"]]
        except Exception as e:
            st.error(f"Error during ticker search: {e}")
    return results

# -----------------------------
# Sidebar settings
st.sidebar.header("Settings")
search_input = st.sidebar.text_input("Search ticker or company name:")

if search_input:
    tickers_df = search_tickers(search_input)
    options = [f"{row['symbol']} - {row['shortname']}" for _, row in tickers_df.iterrows()]
else:
    options = []

ticker_selection = st.sidebar.selectbox("Select a ticker:", options) if options else None
ticker = ticker_selection.split(" - ")[0] if ticker_selection else None

# -----------------------------
if ticker:
    # --- Fundamental Analysis ---
    st.header("📊 Fundamental Analysis")
    fundamentals_data = fundamental.get_fundamentals(ticker)
    
    # Fundamental metrics configuration and reference ranges
    fundamentals_info = {
        "P/E Ratio": {
            "desc": "Price to Earnings Ratio. Lower values indicate undervaluation.",
            "ref": "10–20: average, <10: undervalued, >25: overvalued",
            "min": 10, "max": 20, "percent": False
        },
        "Forward P/E": {
            "desc": "Forward Price to Earnings based on future estimates.",
            "ref": "Similar to P/E",
            "min": 10, "max": 20, "percent": False
        },
        "PEG Ratio": {
            "desc": "Price/Earnings to Growth. Around 1 means fair valuation.",
            "ref": "1 = fair, <1 undervalued, >1.5 overvalued",
            "min": 0, "max": 1.5, "percent": False
        },
        "EPS": {
            "desc": "Earnings Per Share.",
            "ref": "Higher is better",
            "min": 0, "max": None, "percent": False
        },
        "Dividend Yield": {
            "desc": "Dividend return relative to stock price.",
            "ref": "2–5% normal, >5% high",
            "min": 2, "max": 5, "percent": True
        },
        "ROE": {
            "desc": "Return on Equity.",
            "ref": "15–20% considered good",
            "min": 15, "max": 20, "percent": True
        },
        "Debt to Equity": {
            "desc": "Debt-to-equity ratio. >2 is risky.",
            "ref": "<1 excellent, 1–2 acceptable, >2 risky",
            "min": 0, "max": 2, "percent": False
        },
        "Profit Margins": {
            "desc": "Net profit margin percentage.",
            "ref": "10–20% good, >20% excellent",
            "min": 10, "max": 20, "percent": True
        },
    }

    # Display fundamental metrics in a grid
    cols_per_row = 4
    items = list(fundamentals_info.keys())
    for i in range(0, len(items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, key in enumerate(items[i:i + cols_per_row]):
            value = fundamentals_data.get(key)
            with cols[j]:
                info = fundamentals_info[key]
                color = "white"
                if value is not None and isinstance(value, (int, float)):
                    if info["min"] is not None and info["max"] is not None:
                        color = "green" if info["min"] <= value <= info["max"] else "red"
                    elif info["min"] is not None and info["max"] is None:
                        color = "green" if value >= info["min"] else "red"

                display_value = (
                    f"{value:.2f}%" if (value is not None and info["percent"])
                    else f"{value:.2f}" if value is not None else "-"
                )

                st.markdown(
                    f"<div style='display:flex; align-items:center; gap:5px; margin-bottom:0;'>"
                    f"<h4 style='margin:0'>{key}</h4>"
                    f"<span title='{info['desc']}' style='font-weight:bold; color:blue; cursor:help;'>i</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div style='font-size:24px; font-weight:bold; color:{color}; margin-bottom:10px;'>"
                    f"{display_value}<br>"
                    f"<span style='color:white; padding:2px 5px; border-radius:5px; font-size:14px;'>"
                    f"Reference: {info['ref']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # --- Technical Indicators ---
    st.header("📈 Technical Indicators")
    df_prices = indicators.get_historical_prices(ticker, '10y')
    df_prices['MA20'] = indicators.calculate_moving_average(df_prices)
    df_prices['RSI'] = indicators.calculate_rsi(df_prices)
    df_prices['MACD'], df_prices['Signal'] = indicators.calculate_macd(df_prices)

    # 🔄 COMBINED CHART: Price + RSI (shared X-axis)
    st.markdown(
        "<div style='display:flex; align-items:center; gap:5px; margin-bottom:0;'>"
        "<h4 style='margin:0'>Price with Moving Average & RSI</h4>"
        "<span title='Combined candlestick and RSI chart with shared timeline' "
        "style='font-weight:bold; color:blue; cursor:help;'>i</span>"
        "</div>",
        unsafe_allow_html=True
    )

    # Create two subplots: price on top, RSI below
    fig_combined = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.05,
        specs=[[{"secondary_y": True}], [{}]]
    )

    # --- Price (Candlestick) ---
    fig_combined.add_trace(
        go.Candlestick(
            x=df_prices.index,
            open=df_prices['Open'],
            high=df_prices['High'],
            low=df_prices['Low'],
            close=df_prices['Close'],
            name="Price"
        ),
        row=1, col=1, secondary_y=False
    )

    # --- MA20 ---
    fig_combined.add_trace(
        go.Scatter(
            x=df_prices.index,
            y=df_prices['MA20'],
            name="MA20",
            line=dict(color="orange", width=2)
        ),
        row=1, col=1, secondary_y=False
    )

    # --- Volume bars with secondary axis ---
    volume_colors = [
        "rgba(0, 200, 0, 0.75)" if close >= open_ else "rgba(200, 0, 0, 0.75)"
        for open_, close in zip(df_prices["Open"], df_prices["Close"])
    ]

    fig_combined.add_trace(
        go.Bar(
            x=df_prices.index,
            y=df_prices['Volume'],
            name="Volume",
            marker=dict(color=volume_colors),
            opacity=0.6
        ),
        row=1, col=1, secondary_y=True
    )

    # --- RSI ---
    fig_combined.add_trace(
        go.Scatter(
            x=df_prices.index,
            y=df_prices['RSI'],
            name='RSI',
            line=dict(color='blue', width=2)
        ),
        row=2, col=1
    )

    # RSI threshold lines
    fig_combined.add_hline(
        y=70, line_dash="dash", line_color="red",
        annotation_text="Overbought", row=2, col=1
    )
    fig_combined.add_hline(
        y=30, line_dash="dash", line_color="green",
        annotation_text="Oversold", row=2, col=1
    )

    # Layout settings
    fig_combined.update_layout(
        xaxis_rangeslider_visible=False,
        height=900,
        hovermode="x unified",
        showlegend=True
    )

    st.plotly_chart(fig_combined, use_container_width=True)

    # --- Price Forecast with Prophet ---
    st.header("🔮 Price Forecast with Prophet")

    # Prepare historical close prices
    df_forecast = (
        df_prices.reset_index()[["Date", "Close"]]
        .rename(columns={"Date": "ds", "Close": "y"})
    )

    # Remove timezone (Prophet requires naive datetime)
    df_forecast["ds"] = pd.to_datetime(df_forecast["ds"]).dt.tz_localize(None)

    earnings_df = get_earnings_regressors(ticker)
    df_forecast = df_forecast.merge(earnings_df, on="ds", how="left")

    # Earnings values only on earnings days, 0 otherwise
    df_forecast[["EPS", "Revenue"]] = df_forecast[["EPS", "Revenue"]].fillna(0)

    # Forecast horizon selection
    period_days = st.slider(
        "Days to forecast:", min_value=30, max_value=365, value=180, step=30
    )

    # Prophet model
    with st.spinner("Training Prophet model..."):
        df_forecast["RSI"] = df_prices["RSI"].values
        df_forecast["Volume"] = df_prices["Volume"].values

        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True
        )

        model.add_regressor("RSI")
        model.add_regressor("EPS")
        model.add_regressor("Volume")
        model.add_regressor("Revenue")

        model.fit(df_forecast.dropna())

        future = model.make_future_dataframe(periods=period_days)
        future["RSI"] = df_forecast["RSI"].iloc[-1]
        future["Volume"] = df_forecast["Volume"].iloc[-1]

        for col in ["EPS", "Revenue"]:
            future[col] = 0

    forecast = model.predict(future)

    # Interactive forecast chart
    st.subheader(f"Forecast for the next {period_days} days")
    fig_forecast = plot_plotly(model, forecast)
    st.plotly_chart(fig_forecast, use_container_width=True)

    # Forecast data table
    st.subheader("📋 Forecast data (latest values)")

    # Current price (last available close)
    current_price = df_prices["Close"].iloc[-1]

    forecast_table = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(10).copy()

    # Percentage change relative to current price
    forecast_table["% yhat"] = (forecast_table["yhat"] / current_price - 1) * 100
    forecast_table["% yhat_lower"] = (forecast_table["yhat_lower"] / current_price - 1) * 100
    forecast_table["% yhat_upper"] = (forecast_table["yhat_upper"] / current_price - 1) * 100

    # Reorder columns: percentage next to each value
    forecast_table = forecast_table[
        [
            "ds",
            "yhat", "% yhat",
            "yhat_lower", "% yhat_lower",
            "yhat_upper", "% yhat_upper"
        ]
    ]

    st.dataframe(
        forecast_table.style.format({
            "yhat": "{:.2f}",
            "yhat_lower": "{:.2f}",
            "yhat_upper": "{:.2f}",
            "% yhat": "{:+.2f}%",
            "% yhat_lower": "{:+.2f}%",
            "% yhat_upper": "{:+.2f}%"
        })
    )
