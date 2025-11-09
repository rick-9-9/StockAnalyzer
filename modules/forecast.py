from sklearn.linear_model import LinearRegression
import numpy as np

def predict_future_price(df, days_ahead=30):
    df = df.reset_index()
    df['Day'] = np.arange(len(df))
    
    X = df[['Day']]
    y = df['Close']
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_days = np.arange(len(df), len(df) + days_ahead).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    return predictions