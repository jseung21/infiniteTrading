import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import logging
import datetime
import os

# 주식 종목명
stock_name = "TQQQ"
# 전체 잔액
balance_amount = 10000
# 거래 시작일
start_trade_date = "2023-01-01"
# 거래 종료일
end_trade_date = "2024-01-01"
# 매수 회차
buy_times = 50
# 버퍼 매매 포인트
buffer_trading_point = 3
# 매도 포인트
sell_point = 4
# 버퍼 매수 분할 수치
buffer_buy_divide = 4
# 버퍼 매도 분할 수치
buffer_sell_divide = 4
# 거래 수수료율 예: 0.1%
trading_fee_rate = 0.001
# 손절매 기준 예: 10%
stop_loss_threshold = 0.0888759951267608
# 다량 처리 여부
batch_yn = False

def CalculateFee(amount):
    """
    거래 수수료를 계산하는 함수
    amount: 거래 금액
    return: 거래 수수료
    """
    return amount * trading_fee_rate

def Init():
    """
    초기 거래 상태를 설정하는 함수
    return: 초기 거래 상태 변수들
    """
    # 초기화 진행 여부
    init_trade_start_yn = "N"
    # 전체 보유 수량 초기화
    Number_share_held = 0
    # 전체 매수 금액 초기화
    total_stock_buy_amount = 0
    # 평균 매수가 초기화
    average_buy_amount = 0
    return init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount

def StopLoss(close_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount):
    """
    손절매 조건을 확인하고 손절매를 수행하는 함수
    close_price: 주식 종가
    balance_amount: 잔액
    Number_share_held: 보유 주식 수
    average_buy_amount: 평균 매수가
    total_stock_buy_amount: 전체 매수 금액
    return: 갱신된 잔고와 거래 정보
    """
    # 실제 매도 금액 계산
    actual_sell_amount = round(Number_share_held * close_price, 2)
    # 잔액 갱신
    balance_amount += actual_sell_amount
    # 초기화 진행
    init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
    # 손절매 플래그 설정
    trading_flag = "STOP_L"
    return balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag

def SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date):
    """
    주식 종목(stock_name)의 날짜별 종가(stock_history)를 설정하는 함수
    stock_name: 주식 종목명
    start_trade_date: 거래 시작일
    end_trade_date: 거래 종료일
    return: 날짜별 종가 데이터
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
    close_price: 주식 종가
    balance_amount: 잔액
    one_time_buy_amount: 한 번의 매수 금액
    Number_share_held: 보유 주식 수
    average_buy_amount: 평균 매수가
    total_stock_buy_amount: 전체 매수 금액
    buffer_trading_potrading: 버퍼 매매 포인트
    init_trade_start_yn: 초기 거래 여부
    return: 갱신된 잔고와 거래 정보
    """
    trading_flag = "BUY"
    acutual_number_buy_stock = 0 # 실제 매수 주식수
    
    # 초기 매수
    if init_trade_start_yn == "N":
        # 실제 매수 주식수
        acutual_number_buy_stock = int(one_time_buy_amount / close_price)
    else:
        # 종가 <= 평균단가 , full 매수
        if close_price <= average_buy_amount:
            acutual_number_buy_stock = int(one_time_buy_amount / close_price)
        # 종가 < 버퍼 매매 %
        elif close_price < average_buy_amount + (average_buy_amount * buffer_trading_potrading * 0.01):
            acutual_number_buy_stock = int(one_time_buy_amount / buffer_buy_divide / close_price)
            trading_flag = f"BUY/{buffer_buy_divide}"
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
        
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount, 2), trading_flag

def Sell(close_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, sell_point):
    """
    주식 매도 함수
    close_price: 주식 종가
    balance_amount: 잔액
    Number_share_held: 보유 주식 수
    average_buy_amount: 평균 매수가
    total_stock_buy_amount: 전체 매수 금액
    init_trade_start_yn: 초기 거래 여부
    sell_point: 매도 포인트
    return: 갱신된 잔고와 거래 정보
    """
    acutual_number_sell_stock = 0 # 실제 매도 주식수
    
    # 종가 < 매도 포인트
    if close_price < average_buy_amount + (average_buy_amount * sell_point * 0.01):
        # 1/4 매도
        acutual_number_sell_stock = int(Number_share_held / buffer_sell_divide)
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * close_price, 2)
        
        # 전체 보유 수량 계산
        Number_share_held -= acutual_number_sell_stock
        
        if Number_share_held == 0:
            # 잔액 초기화
            init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
        else:
            # 전체 매수 금액 계산
            total_stock_buy_amount -= actual_sell_amount
            # 평균 매수가 계산  
            average_buy_amount = round(total_stock_buy_amount / Number_share_held, 2)
        trading_flag = f"SELL/{buffer_sell_divide}"     
    else: 
        # 전량 매도
        acutual_number_sell_stock = Number_share_held
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * (average_buy_amount + (average_buy_amount * sell_point * 0.01)))
        # 잔액 초기화
        init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
        
        trading_flag = "SELL" 

    # 매매 수수료 계산 
    sell_fee = CalculateFee(actual_sell_amount)

    # 전체 잔고 계산
    balance_amount += (actual_sell_amount - sell_fee)
    
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount, 2), init_trade_start_yn, trading_flag

def DoTrading(stock_name, balance_amount, start_trade_date, end_trade_date, buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold, batch_yn):
    """
    거래 처리 함수
    stock_name: 주식 종목명
    balance_amount: 잔액
    start_trade_date: 거래 시작일
    end_trade_date: 거래 종료일
    buy_times: 매수 회차
    buffer_trading_point: 버퍼 매매 포인트
    sell_point: 매도 포인트
    buffer_buy_divide: 버퍼 매수 분할 수치
    buffer_sell_divide: 버퍼 매도 분할 수치
    stop_loss_threshold: 손절매 기준
    batch_yn: 다량 처리 여부
    """
    # 초기 평가 금액 설정
    assessment_amount = balance_amount
    # 주식 이력 초기화
    stock_history = []
    # 초기 주식 종가 설정
    stock_final_price = 0
    # 초기 보유 주식 수 설정
    Number_share_held = 0
    # 초기 전체 매수 금액 설정
    total_stock_buy_amount = 0
    # 초기 평균 매수 금액 설정
    average_buy_amount = 0
    # 초기 한 번 매수 금액 설정
    one_time_buy_amount = 0
    # 초기 거래 여부 설정
    init_trade_start_yn = "N"
    
    # 로깅을 위한 파일명 설정 (현재 날짜와 시간을 기반으로 파일명 생성)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'logs/{stock_name}_{start_trade_date}_{end_trade_date}_{buy_times}_{buffer_trading_point}_{sell_point}_{timestamp}.log'

    # 로거 설정
    logging.basicConfig(filename=filename, level=logging.DEBUG, 
                        format='%(message)s')
    
    # 그래프 데이터를 저장할 리스트 초기화
    dates = []
    close_prices = []
    assessment_amounts = []
    
    # 주식 이력이 비어있을 경우 주식 종가 설정
    if not stock_history:
        stock_history = SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date)
        stock_history.reset_index(inplace=True)
        
    # 주식 이력을 반복하며 거래 수행
    for index, row in stock_history.iterrows():
        date = row["Date"]
        close_price = row["Close"]
        trading_flag = "SKIP"
        
        # 초기화 이후 거래
        if init_trade_start_yn == "N":
            # 매수 금액 설정
            one_time_buy_amount = assessment_amount / buy_times
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
        elif close_price < average_buy_amount + (average_buy_amount * buffer_trading_point * 0.01) and balance_amount > one_time_buy_amount:
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(close_price, 
                                                                                              balance_amount, 
                                                                                              one_time_buy_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              buffer_trading_point,
                                                                                              init_trade_start_yn)
        # 매도 거래, 종가 > 버퍼 매매 평단 %
        elif close_price > average_buy_amount + (average_buy_amount * buffer_trading_point * 0.01):
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = Sell(close_price, 
                                                                                              balance_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              init_trade_start_yn,
                                                                                              sell_point)        
        # 평가 금액 = 잔고 + 보유주식수 * 종가
        assessment_amount = round(balance_amount + (Number_share_held * close_price), 2)
        
        # 로깅
        log = f"날짜: {str(date)[0:10]},\t종가: {close_price:.2f},\t매매: {trading_flag},\t잔고: {balance_amount:.2f},\
\t보유주식수: {Number_share_held},\t평균매수금액: {average_buy_amount},\t전체매수금액: {total_stock_buy_amount},\t평가금액: {assessment_amount}"
        
        if not batch_yn:
            print(log)
            # 그래프 데이터 저장
            dates.append(date)
            close_prices.append(close_price)
            assessment_amounts.append(assessment_amount)
        
    if not batch_yn:
        # 그래프 그리기
        fig, ax1 = plt.subplots()
        ax1.plot(dates, close_prices, color='green', alpha=0.5)
        ax1.set_ylabel('Close Price', color='green', rotation=0)
        ax2 = ax1.twinx()
        ax2.plot(dates, assessment_amounts, color='red', alpha=0.5)
        ax2.set_ylabel('Assessment Amount', color='red', rotation=0)
        plt.show()
    else:
        return assessment_amount

if __name__ == "__main__":
    # 거래 시작
    DoTrading(stock_name, balance_amount, start_trade_date, end_trade_date, buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold, batch_yn)
