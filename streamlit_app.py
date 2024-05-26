import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Streamlit 웹앱 설정
st.title('Stock Trading Simulation')

# 사용자 입력
stock_name = st.text_input("Stock Name", "TQQQ")
balance_amount = st.number_input("Initial Balance", 10000)
start_trade_date = st.date_input("Start Trade Date", pd.to_datetime("2023-01-01"))
end_trade_date = st.date_input("End Trade Date", pd.to_datetime("2024-01-01"))
buy_times = st.number_input("Number of Buy Times", 40)
buffer_trading_point = st.number_input("Buffer Trading Point (%)", 5.0) / 100
sell_point = st.number_input("Sell Point (%)", 10.0) / 100
buffer_buy_divide = st.number_input("Buffer Buy Divide", 2)
buffer_sell_divide = st.number_input("Buffer Sell Divide", 4)
stop_loss_threshold = st.number_input("Stop Loss Threshold (%)", 1.0) / 100
trading_fee_rate = st.number_input("Trading Fee Rate (%)", 0.1) / 100
batch_yn = st.checkbox("Batch Mode")
trading_price_flag = st.selectbox("Trading Price Flag", ["high", "close"])

def CalculateFee(amount):
    return amount * trading_fee_rate

def Init():
    init_trade_start_yn = "Y"
    Number_share_held = 0
    total_stock_buy_amount = 0
    average_buy_amount = 0
    return init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount

def StopLoss(close_prcice, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount):
    actual_sell_amount = round(Number_share_held * close_prcice, 2)
    sell_fee = CalculateFee(actual_sell_amount)
    balance_amount += (actual_sell_amount - sell_fee)
    init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
    trading_flag = "STOP_L"
    return balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag

def SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date):
    try:
        stock = yf.Ticker(stock_name)
        stock_history = stock.history(start=start_trade_date, end=end_trade_date)
        return stock_history
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def Buy(tradeing_price, balance_amount, one_time_buy_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, buffer_trading_point, init_trade_start_yn):
    trading_flag = "BUY"
    actual_number_buy_stock = 0
    
    if init_trade_start_yn == "Y":
        actual_number_buy_stock = int(one_time_buy_amount / tradeing_price)
    else:
        if tradeing_price <= average_buy_amount:
            actual_number_buy_stock = int(one_time_buy_amount / tradeing_price)
        elif tradeing_price < average_buy_amount * (1 + buffer_trading_point):
            actual_number_buy_stock = int(one_time_buy_amount / buffer_buy_divide / tradeing_price)
            trading_flag = f"BUY/{buffer_buy_divide}"
        else:
            trading_flag = "BUY_SKIP"

    actual_buy_amount = round(actual_number_buy_stock * tradeing_price, 2)
    buy_fee = CalculateFee(actual_buy_amount)
    balance_amount -= (actual_buy_amount + buy_fee)
    Number_share_held += actual_number_buy_stock
    total_stock_buy_amount += actual_buy_amount
    average_buy_amount = round(total_stock_buy_amount / Number_share_held, 2)        
        
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount, 2), trading_flag

def Sell(tradeing_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, sell_point):
    acutual_number_sell_stock = 0
    
    if tradeing_price < average_buy_amount * (1 + sell_point):
        acutual_number_sell_stock = int(Number_share_held / buffer_sell_divide)
        actual_sell_amount = round(acutual_number_sell_stock * tradeing_price, 2)
        Number_share_held -= acutual_number_sell_stock
        
        if Number_share_held == 0:
            init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
        else:
            total_stock_buy_amount = round(Number_share_held * average_buy_amount, 2)
            
        trading_flag = f"SELL/{buffer_sell_divide}"     
    else: 
        acutual_number_sell_stock = Number_share_held
        actual_sell_amount = round(acutual_number_sell_stock * (average_buy_amount * (1 + sell_point)), 2)
        init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
        trading_flag = "SELL" 

    sell_fee = CalculateFee(actual_sell_amount)
    balance_amount += (actual_sell_amount - sell_fee)
    
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount, 2), init_trade_start_yn, trading_flag

def DoTrading(stock_name, balance_amount, start_trade_date, end_trade_date, buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold, batch_yn):
    assessment_amount = balance_amount
    stock_history = []
    stock_final_price = 0
    Number_share_held = 0
    total_stock_buy_amount = 0
    average_buy_amount = 0
    one_time_buy_amount = 0
    init_trade_start_yn = "Y"
    
    dates = []
    trading_prices = []
    average_buy_amounts = []
    assessment_amounts = []
    
    if not stock_history:
        stock_history = SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date)
        stock_history.reset_index(inplace=True)
        
    for index, row in stock_history.iterrows():
        date = row["Date"]
        close_prcice = row["Close"]
        high_price = row["High"]
        trading_flag = "SKIP"
        if trading_price_flag == "high":
            tradeing_price = high_price
        elif trading_price_flag == "close":
            tradeing_price = close_prcice
        else:
            st.error("Set the trading price flag")
            break
        
        if init_trade_start_yn == "Y":
            one_time_buy_amount = assessment_amount / buy_times
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(tradeing_price, 
                                                                                                balance_amount, 
                                                                                                one_time_buy_amount, 
                                                                                                Number_share_held, 
                                                                                                average_buy_amount, 
                                                                                                total_stock_buy_amount,
                                                                                                buffer_trading_point,
                                                                                                init_trade_start_yn)
            init_trade_start_yn = "N"
        elif close_prcice < average_buy_amount * (1 - stop_loss_threshold):
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = StopLoss(close_prcice, 
                                                                                                                   balance_amount, 
                                                                                                                   Number_share_held, 
                                                                                                                   average_buy_amount, 
                                                                                                                   total_stock_buy_amount)
        elif tradeing_price < average_buy_amount + (average_buy_amount * buffer_trading_point) and balance_amount > one_time_buy_amount:
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(tradeing_price, 
                                                                                              balance_amount, 
                                                                                              one_time_buy_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              buffer_trading_point,
                                                                                              init_trade_start_yn)
        elif tradeing_price > average_buy_amount + (average_buy_amount * buffer_trading_point):
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = Sell(tradeing_price, 
                                                                                              balance_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              init_trade_start_yn,
                                                                                              sell_point)        
        assessment_amount = round(balance_amount + (Number_share_held * tradeing_price), 2)
        
        log = f"Date: {str(date)[0:10]}, Trading Price: {tradeing_price:.2f}, Action: {trading_flag}, Balance: {balance_amount:.2f},\
        Shares Held: {Number_share_held}, Avg Buy Amount: {average_buy_amount}, Total Buy Amount: {total_stock_buy_amount}, Assessment Amount: {assessment_amount}"
        
        if not batch_yn:
<<<<<<< HEAD
            # st.write(log)
=======
            st.write(log)
>>>>>>> 8647e4b14eca1ba9a8e64c86c05c9a0f484d1edd
            dates.append(date)
            trading_prices.append(tradeing_price)
            if average_buy_amount != 0:
                average_buy_amounts.append(average_buy_amount)
            else:
                average_buy_amounts.append(None)
            assessment_amounts.append(assessment_amount)
        
    if not batch_yn:
        fig, ax1 = plt.subplots()
        ax1.plot(dates, trading_prices, color='green', alpha=0.5)
        ax1.set_ylabel(f'{trading_price_flag.capitalize()} Price', color='green')
        ax1.plot(dates, average_buy_amounts, color='blue', alpha=0.7, label='Avg Buy Amount')
        ax2 = ax1.twinx()
        ax2.plot(dates, assessment_amounts, color='red', alpha=0.5)
        ax2.set_ylabel('Assessment Amount', color='red')
        st.pyplot(fig)
    else:
        return assessment_amount

if st.button("Run Trading Simulation"):
    DoTrading(stock_name, balance_amount, start_trade_date, end_trade_date, buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold, batch_yn)
