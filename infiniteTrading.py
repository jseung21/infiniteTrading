import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

stock_name = "TQQQ"  # 주식 종목명
balance_amount = 10000  # 전체 잔액
start_trade_date = "2023-01-01"  # 거래 시작일
end_trade_date = "2024-01-01"  # 거래 종료일
buy_times = 40  # 매수 회차
buffer_trading_point = 5  # 버퍼 매매 포인트
sell_point = 10  # 매도 포인트
buffer_buy_divide = 2 # 버퍼 매수 분할 수치
buffer_sell_divide = 4 # 버퍼 매도 분할 수치
trading_fee_rate = 0.001  # 거래 수수료율 예: 0.1%
stop_loss_threshold = 0.1  # 손절매 기준 예: 10%
batch_yn = False # 다량 처리

def CalculateFee(amount):
    """
    거래 수수료를 계산하는 함수
    """
    return amount * trading_fee_rate

def StopLoss(close_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount):
    """
    손절매 조건을 확인하고 손절매를 수행하는 함수
    """
    actual_sell_amount = round(Number_share_held * close_price, 2)
    balance_amount += actual_sell_amount
    Number_share_held = 0
    total_stock_buy_amount = 0
    average_buy_amount = 0
    init_trade_start_yn = "N"
    trading_flag = "STOP_L"
    # 손절매 후 갱신된 잔고와 거래 정보를 반환
    return balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag

def SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date):
    """
    주식 종목(stock_name)의 날짜별 종가(stock_history)를 설정하는 함수
    """
    try:
        stock = yf.Ticker(stock_name)
        stock_history = stock.history(start=start_trade_date, end=end_trade_date)
        return stock_history
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def Buy(close_price, balance_amount, one_time_buy_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, buffer_trading_potrading, init_trade_start_yn):
    """
    주식 매수 함수
    - 종가 <= 평단 -> 매수
    - 버퍼 매매 > 종가 > 평단 -> 매수/2
    """
    trading_flag = "BUY"
    acutual_number_buy_stock = 0 # 실제 매수 주식수
    
    # 초기 매수
    if init_trade_start_yn == "N":
        # 실제 매수 주식수
        acutual_number_buy_stock = int(one_time_buy_amount/close_price)
    else:
        # 종가 <= 평균단가 , full 매수
        if close_price <= average_buy_amount :
            # 실제 매수 주식수
            acutual_number_buy_stock = int(one_time_buy_amount/close_price)
        # 종가 < 버퍼 매매 %
        elif close_price < average_buy_amount+(average_buy_amount*buffer_trading_potrading*0.01):
            # 실제 매수 주식수
            acutual_number_buy_stock = int(one_time_buy_amount/buffer_buy_divide/close_price)
            trading_flag = "BUY/2"
        else:
            trading_flag = "BUY_SKIP"

    # 실제 매수 금액
    actual_buy_amount = round(acutual_number_buy_stock * close_price, 2)
    # 매매 수수료 계산
    buy_fee = CalculateFee(actual_buy_amount)
    # 전체 잔고 계산
    balance_amount -= (actual_buy_amount + buy_fee)
    # 전체 보유 수량 계산
    Number_share_held += acutual_number_buy_stock
    # 전체 매수 금액 계산
    total_stock_buy_amount += actual_buy_amount
    # 평균 매수가 계산  
    average_buy_amount = round(total_stock_buy_amount / Number_share_held, 2)        
        
            
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount,2), trading_flag

def Sell(close_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn,sell_point):
    """
    주식 매도 함수
    - 버퍼 매매 < 종가 < 매도 포인트 -> 매도/4
    - 종가 >= 매도 포인트 -> 매도
    """
    acutual_number_sell_stock = 0 # 실제 매도 주식수
    
    # 종가 < 매도 포인트
    if close_price < average_buy_amount+(average_buy_amount*sell_point*0.01):
        # 1/4 매도
        acutual_number_sell_stock = int(Number_share_held/buffer_sell_divide)
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * close_price, 2)
        
        # 전체 보유 수량 계산
        Number_share_held -= acutual_number_sell_stock
        # 전체 매수 금액 계산
        total_stock_buy_amount -= actual_sell_amount
        # 평균 매수가 계산  
        average_buy_amount = round(total_stock_buy_amount / Number_share_held, 2)
        trading_flag = "SELL/4"     
    else: 
        # 전량 매도
        acutual_number_sell_stock = Number_share_held
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * (average_buy_amount+(average_buy_amount*sell_point*0.01)))
        
        # 초기화 진행
        init_trade_start_yn = "N"
        # 전체 보유 수량 초기화
        Number_share_held = 0
        # 전체 매수 금액 계산
        total_stock_buy_amount = 0
        # 평균 매수가 계산  
        average_buy_amount = 0
        
        trading_flag = "SELL" 

    # 매매 수수료 계산 
    sell_fee = CalculateFee(actual_sell_amount)

    # 전체 잔고 계산
    balance_amount += (actual_sell_amount - sell_fee)
    
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount,2), init_trade_start_yn,trading_flag

def DoTrading(stock_name,balance_amount,start_trade_date,end_trade_date,buy_times,buffer_trading_point,sell_point,buffer_buy_divide,buffer_sell_divide,stop_loss_threshold,batch_yn):
    
    assessment_amount = 0 # 평가 금액
    stock_history = []  # 주식 이력 (빈 리스트로 초기화)
    stock_final_price = 0  # 주식 종가 (실제 값으로 설정 필요)
    Number_share_held = 0  # 매수한 주식 수
    total_stock_buy_amount = 0 # 전체 주식 매수 금액
    average_buy_amount = 0  # 평균 매수 금액
    one_time_buy_amount = 0  # 한번 매수 금액
    init_trade_start_yn = "N"
    
    # 그래프 (날짜, 종가, 평가금액)
    dates = []  # 날짜 정보를 저장할 리스트
    close_prices = []  # 종가 정보를 저장할 리스트
    assessment_amounts = []  # 평가금액 정보를 저장할 리스트
    
    # stock_history가 비어있을 경우에만 설정
    if not stock_history:
        stock_history = SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date)
        # 날짜 정보를 컬럼으로 변환
        stock_history.reset_index(inplace=True)
        # print(f"주식 거래 일수: {stock_history.size}")
        
    # stock_history의 크기만큼 루프를 돌면서 처리
    for index, row in stock_history.iterrows():
        date = row["Date"] # 날짜 정보
        close_price = row["Close"]  # 종가 정보
        trading_flag = "SKIP"
        
        # 종가 <= 평단 -> 매수
        # 버퍼 매매 > 종가 > 평단 -> 매수/2
        # 버퍼 매매 < 종가 < 매도 포인트 -> 매도/4
        # 종가 >= 매도 포인트 -> 매도

        # 초기화 이후 거래
        if init_trade_start_yn == "N":
            # 매수 금액 설정
            one_time_buy_amount = balance_amount / buy_times
            # 매수 처리
            if balance_amount > one_time_buy_amount:
                balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(close_price, 
                                                                                                balance_amount, 
                                                                                                one_time_buy_amount, 
                                                                                                Number_share_held, 
                                                                                                average_buy_amount, 
                                                                                                total_stock_buy_amount,
                                                                                                buffer_trading_point,
                                                                                                init_trade_start_yn)
            init_trade_start_yn = "Y"
        # 손절매 체크
        elif close_price < average_buy_amount * (1 - stop_loss_threshold):
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = StopLoss(close_price, 
                                                                                                                   balance_amount, 
                                                                                                                   Number_share_held, 
                                                                                                                   average_buy_amount, 
                                                                                                                   total_stock_buy_amount)
        # 매수 거래,  종가 < 버퍼 매매 평단 %
        elif close_price < average_buy_amount+(average_buy_amount*buffer_trading_point*0.01) and balance_amount > one_time_buy_amount:
            # 매수 처리
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(close_price, 
                                                                                              balance_amount, 
                                                                                              one_time_buy_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              buffer_trading_point,
                                                                                              init_trade_start_yn)
        # 매도 거래, 종가 > 버퍼 매매 평단 %
        elif  close_price > average_buy_amount+(average_buy_amount*buffer_trading_point*0.01) :
            # 매도 처리
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = Sell(close_price, 
                                                                                              balance_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              init_trade_start_yn,
                                                                                              sell_point)        
        # 평가 금액 = 잔고 + 보유주식수 * 종가
        assessment_amount = round(balance_amount + (Number_share_held * close_price),2)
        if not batch_yn:
            print(f"날짜: {str(date)[0:10]},\t종가: {close_price:.2f},\t매매: {trading_flag},\t잔고: {balance_amount:.2f},\
\t보유주식수: {Number_share_held},\t평균매수금액: {average_buy_amount},\t전체매수금액: {total_stock_buy_amount},\t평가금액: {assessment_amount}")
            # 그래프 수치 설정
            dates.append(date)
            close_prices.append(close_price)
            assessment_amounts.append(assessment_amount)
        


    if not batch_yn:
        # 그래프 그리기
        fig, ax1 = plt.subplots()
        ax1.plot(dates, close_prices, color = 'green', alpha = 0.5)
        # y축 라벨 및 범위 지정
        ax1.set_ylabel('final', color = 'green', rotation = 0)
        # ax1.set_ylim(0, 15)

        ax2 = ax1.twinx()
        ax2.plot(dates, assessment_amounts, color = 'red', alpha = 0.5)
        # y축 라벨 및 범위 지정
        ax2.set_ylabel('assessment', color = 'red', rotation = 0)
        # ax2.set_ylim(0, 2500)
        plt.show()
    else:
        return assessment_amount


if __name__ == "__main__":

    # 거래 시작
    DoTrading(stock_name,balance_amount,start_trade_date,end_trade_date,buy_times,buffer_trading_point,sell_point,buffer_buy_divide,buffer_sell_divide,stop_loss_threshold,batch_yn)
