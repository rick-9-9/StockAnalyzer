import yfinance as yf

def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    fundamentals = {
        "P/E Ratio": info.get("trailingPE"),
        "Forward P/E": info.get("forwardPE"),
        "PEG Ratio": info.get("pegRatio"),
        "EPS": info.get("trailingEps"),
        "Dividend Yield": info.get("dividendYield"),
        "ROE": info.get("returnOnEquity"),
        "Debt to Equity": info.get("debtToEquity"),
        "Profit Margins": info.get("profitMargins"),
    }
    return fundamentals