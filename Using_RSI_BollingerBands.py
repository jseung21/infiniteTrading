import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def calculate_RSI(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_BollingerBands(data, window=20):
    rolling_mean = data['Close'].rolling(window).mean()
    rolling_std = data['Close'].rolling(window).std()
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)
    return upper_band, lower_band

def initial_buy_signal(data, rsi_threshold=30):
    data['RSI'] = calculate_RSI(data)
    upper_band, lower_band = calculate_BollingerBands(data)
    data['Upper Band'] = upper_band
    data['Lower Band'] = lower_band

    buy_signals = (data['Close'] < data['Lower Band']) & (data['RSI'] < rsi_threshold)
    return buy_signals

def plot_signals(data, buy_signals):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Close'], label='Close Price')
    plt.plot(data['Upper Band'], label='Upper Bollinger Band', linestyle='--')
    plt.plot(data['Lower Band'], label='Lower Bollinger Band', linestyle='--')
    plt.scatter(data.index[buy_signals], data['Close'][buy_signals], marker='^', color='g', label='Buy Signal')
    plt.legend()
    plt.show()

def main():
    stock_name = "SQQQ"
    start_date = "2023-01-01"
    end_date = "2024-05-19"
    
    stock_data = yf.download(stock_name, start=start_date, end=end_date)
    
    buy_signals = initial_buy_signal(stock_data)
    plot_signals(stock_data, buy_signals)

if __name__ == "__main__":
    main()
