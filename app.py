import streamlit as st
from modules import fundamental, indicators
from utils.helpers import info_icon
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
from prophet import Prophet
from prophet.plot import plot_plotly

st.set_page_config(page_title="Investimenti AI", layout="wide")
st.title("📈 Analisi Azioni con AI")

# -----------------------------
# Carica lista ticker dal file locale equities.csv
@st.cache_data
def load_local_tickers(filepath='equities.csv'):
    try:
        df = pd.read_csv(filepath)
        df = df.rename(columns={"symbol": "symbol", "name": "shortname"})
        return df[["symbol", "shortname"]]
    except Exception as e:
        st.error(f"Errore durante il caricamento dei ticker locali: {e}")
        return pd.DataFrame(columns=["symbol", "shortname"])

all_tickers_df = load_local_tickers()

# -----------------------------
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
            st.error(f"Errore durante la ricerca ticker: {e}")
    return results

# -----------------------------
st.sidebar.header("Impostazioni")
search_input = st.sidebar.text_input("Cerca ticker o nome azienda:")

if search_input:
    tickers_df = search_tickers(search_input)
    options = [f"{row['symbol']} - {row['shortname']}" for _, row in tickers_df.iterrows()]
else:
    options = []

ticker_selection = st.sidebar.selectbox("Seleziona un ticker:", options) if options else None
ticker = ticker_selection.split(" - ")[0] if ticker_selection else None

# -----------------------------
if ticker:
    # --- Analisi Fondamentale ---
    st.header("📊 Analisi Fondamentale")
    fundamentals_data = fundamental.get_fundamentals(ticker)
    
    fundamentals_info = {
        "P/E Ratio": {"desc": "Rapporto Prezzo/Utili. Valori più bassi = azione sottovalutata.", "ref": "10-20: medio, <10: sottovalutato, >25: sopravvalutato", "min": 10, "max": 20, "percent": False},
        "Forward P/E": {"desc": "Rapporto Prezzo/Utili attesi (stime future).", "ref": "Simile al P/E", "min": 10, "max": 20, "percent": False},
        "PEG Ratio": {"desc": "Price/Earnings to Growth. Vicino a 1 = valutazione equilibrata.", "ref": "1 = giusto, <1 sottovalutato, >1.5 sopravvalutato", "min": 0, "max": 1.5, "percent": False},
        "EPS": {"desc": "Earnings per Share: utile netto per azione.", "ref": "Maggiore è meglio", "min": 0, "max": None, "percent": False},
        "Dividend Yield": {"desc": "Rendimento da dividendo rispetto al prezzo dell'azione.", "ref": "2-5% normale, >5% alto", "min": 2, "max": 5, "percent": True},
        "ROE": {"desc": "Return on Equity: redditività del capitale proprio.", "ref": "15-20% considerato buono", "min": 15, "max": 20, "percent": True},
        "Debt to Equity": {"desc": "Rapporto tra debiti e capitale proprio. >2 è rischioso.", "ref": "<1 ottimo, 1-2 accettabile, >2 rischioso", "min": 0, "max": 2, "percent": False},
        "Profit Margins": {"desc": "Percentuale di profitto netto sui ricavi.", "ref": "10-20% buono, >20% eccellente", "min": 10, "max": 20, "percent": True},
    }

    cols_per_row = 4
    items = list(fundamentals_info.keys())
    for i in range(0, len(items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, key in enumerate(items[i:i+cols_per_row]):
            value = fundamentals_data.get(key)
            with cols[j]:
                info = fundamentals_info[key]
                color = "white"
                if value is not None and isinstance(value, (int, float)):
                    if info["min"] is not None and info["max"] is not None:
                        color = "green" if info["min"] <= value <= info["max"] else "red"
                    elif info["min"] is not None and info["max"] is None:
                        color = "green" if value >= info["min"] else "red"
                display_value = f"{value:.2f}%" if (value is not None and info["percent"]) else \
                                f"{value:.2f}" if value is not None else "-"
                st.markdown(
                    f"<div style='display:flex; align-items:center; gap:5px; margin-bottom:0;'>"
                    f"<h4 style='margin:0'>{key}</h4>"
                    f"<span title='{info['desc']}' style='font-weight:bold; color:blue; cursor:help;'>i</span>"
                    f"</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='font-size:24px; font-weight:bold; color:{color}; margin-bottom:10px;'>"
                    f"{display_value}<br><span style='color:white; padding:2px 5px; border-radius:5px; font-size:14px;'>"
                    f"Riferimento: {info['ref']}</span>"
                    f"</div>", unsafe_allow_html=True)

    # --- Indicatori Tecnici ---
    st.header("📈 Indicatori Tecnici")
    df_prices = indicators.get_historical_prices(ticker, '5y')
    print(df_prices)
    df_prices['MA20'] = indicators.calculate_moving_average(df_prices)
    df_prices['RSI'] = indicators.calculate_rsi(df_prices)
    df_prices['MACD'], df_prices['Signal'] = indicators.calculate_macd(df_prices)

    # 🔄 GRAFICO COMBINATO: Prezzo + RSI (assi X condivisi)
    st.markdown(
        "<div style='display:flex; align-items:center; gap:5px; margin-bottom:0;'>"
        "<h4 style='margin:0'>Prezzo con Media Mobile & RSI</h4>"
        "<span title='Grafico combinato con candlestick e RSI sincronizzati' style='font-weight:bold; color:blue; cursor:help;'>i</span>"
        "</div>", unsafe_allow_html=True)

    # Crea due subplot: prezzo sopra, RSI sotto
    fig_combined = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=("Prezzo & MA20", "RSI")
    )

    # --- Prezzo e MA20 ---
    fig_combined.add_trace(
        go.Candlestick(
            x=df_prices.index,
            open=df_prices['Open'],
            high=df_prices['High'],
            low=df_prices['Low'],
            close=df_prices['Close'],
            name="Prezzo"
        ),
        row=1, col=1
    )
    fig_combined.add_trace(
        go.Scatter(
            x=df_prices.index, y=df_prices['MA20'],
            name="MA20", line=dict(color="orange", width=2)
        ),
        row=1, col=1
    )

    # --- RSI ---
    fig_combined.add_trace(
        go.Scatter(x=df_prices.index, y=df_prices['RSI'], name='RSI', line=dict(color='blue', width=2)),
        row=2, col=1
    )

    # Linee di riferimento RSI
    fig_combined.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Ipercomprato", row=2, col=1)
    fig_combined.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Ipervenduto", row=2, col=1)

    # Layout generale
    fig_combined.update_layout(
        xaxis_rangeslider_visible=False,
        showlegend=True,
        height=800,
        hovermode="x unified",  # ✅ sincronizza cursore tra grafici
    )

    st.plotly_chart(fig_combined, use_container_width=True)

st.header("🔮 Previsione del Prezzo con Prophet")

# Usa i dati storici (Close)
df_forecast = (
    df_prices.reset_index()[["Date", "Close"]]
    .rename(columns={"Date": "ds", "Close": "y"})
)
# Rimuove timezone (Prophet richiede datetime naive)
df_forecast["ds"] = pd.to_datetime(df_forecast["ds"]).dt.tz_localize(None)

# Selezione periodo di previsione
period_days = st.slider("Giorni da prevedere:", min_value=30, max_value=365, value=180, step=30)

# Modello Prophet
with st.spinner("Addestramento modello Prophet..."):
    # df_forecast["MA20"] = df_prices["MA20"].values
    df_forecast["RSI"] = df_prices["RSI"].values

    model = Prophet(daily_seasonality=True)
    # model.add_regressor("MA20")
    model.add_regressor("RSI")

    model.fit(df_forecast.dropna())
    future = model.make_future_dataframe(periods=period_days)
    # future["MA20"] = df_forecast["MA20"].iloc[-1]
    future["RSI"] = df_forecast["RSI"].iloc[-1]
forecast = model.predict(future)

# Grafico interattivo con Plotly
st.subheader(f"Previsione per i prossimi {period_days} giorni")
fig_forecast = plot_plotly(model, forecast)
st.plotly_chart(fig_forecast, use_container_width=True)

# Tabella con le ultime previsioni
st.subheader("📋 Dati di previsione (ultimi valori)")
st.dataframe(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(10))