import yfinance as yf
import pandas as pd

def get_earnings_regressors(ticker):
    stock = yf.Ticker(ticker)
    today = pd.Timestamp.today().normalize()

    try:
        financials = stock.quarterly_financials.T.reset_index()
        financials.rename(columns={"index": "ds"}, inplace=True)
        financials["ds"] = pd.to_datetime(financials["ds"])

        revenue = (
            financials[["ds", "Total Revenue"]]
            .rename(columns={"Total Revenue": "Revenue"})
        )
        revenue = revenue[revenue["ds"] <= today]
    except:
        revenue = pd.DataFrame(columns=["ds", "Revenue"])

    try:
        income_stmt = stock.quarterly_income_stmt.T.reset_index()
        income_stmt.rename(columns={"index": "ds"}, inplace=True)
        income_stmt["ds"] = pd.to_datetime(income_stmt["ds"])

        shares = stock.get_shares_full(start="2000-01-01")
        shares = shares.resample("QE").ffill().infer_objects(copy=False)

        eps_df = income_stmt.merge(
            shares.rename("SharesOutstanding"),
            left_on="ds",
            right_index=True,
            how="left"
        )

        eps_df["EPS"] = eps_df["Net Income"] / eps_df["SharesOutstanding"]
        eps_df = eps_df[["ds", "EPS"]]
        eps_df = eps_df[eps_df["ds"] <= today]
    except:
        eps_df = pd.DataFrame(columns=["ds", "EPS"])

    df = eps_df.merge(revenue, on="ds", how="outer")

    df = df.sort_values("ds")
    df = df.fillna(0).infer_objects(copy=False)
    return df[["ds", "EPS", "Revenue"]]
