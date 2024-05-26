import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import logging
import datetime

# 주식 종목명
stock_name = "TQQQ"
# 전체 잔액
balance_amount = 10000
# 거래 시작일
start_trade_date = "2023-01-01"
# 거래 종료일
end_trade_date = "2024-01-01"
# 매수 회차
buy_times = 40
# 버퍼 매매 포인트 백분율
buffer_trading_point = 0.05
# 매도 포인트 백분율
sell_point = 0.1
# 버퍼 매수 분할 수치
buffer_buy_divide = 2
# 버퍼 매도 분할 수치
buffer_sell_divide = 4
# 손절매 기준 백분율
stop_loss_threshold = 1
# 거래 수수료율 예: 0.1%
trading_fee_rate = 0.001
# 다량 처리 여부
batch_yn = False
# Trading price flag
trading_price_flag = "high"

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
    init_trade_start_yn = "Y"
    # 전체 보유 수량 초기화
    Number_share_held = 0
    # 전체 매수 금액 초기화
    total_stock_buy_amount = 0
    # 평균 매수가 초기화
    average_buy_amount = 0
    
    return init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount

def StopLoss(close_prcice, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount):
    """
    손절매 조건을 확인하고 손절매를 수행하는 함수
    close_prcice: 주식 종가
    balance_amount: 잔액
    Number_share_held: 보유 주식 수
    average_buy_amount: 평균 매수가
    total_stock_buy_amount: 전체 매수 금액
    return: 갱신된 잔고와 거래 정보
    """
    # 실제 매도 금액 계산
    actual_sell_amount = round(Number_share_held * close_prcice, 2)
    # 매매 수수료 계산
    sell_fee = CalculateFee(actual_sell_amount)
    # 잔액 갱신
    balance_amount += (actual_sell_amount - sell_fee)
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

def Buy(tradeing_price, balance_amount, one_time_buy_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, buffer_trading_point, init_trade_start_yn):
    """
    주식 매수 함수
    tradeing_price: 매매기준가
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
    actual_number_buy_stock = 0 # 실제 매수 주식수
    
    # 초기 매수
    if init_trade_start_yn == "Y":
        # 실제 매수 주식수
        actual_number_buy_stock = int(one_time_buy_amount / tradeing_price)
    else:
        # 종가 <= 평균단가 , full 매수
        if tradeing_price <= average_buy_amount:
            actual_number_buy_stock = int(one_time_buy_amount / tradeing_price)
        # 종가 < 버퍼 매매 
        elif tradeing_price < average_buy_amount * (1 + buffer_trading_point):
            actual_number_buy_stock = int(one_time_buy_amount / buffer_buy_divide / tradeing_price)
            trading_flag = f"BUY/{buffer_buy_divide}"
        else:
            trading_flag = "BUY_SKIP"

    # 실제 매수 금액
    actual_buy_amount = round(actual_number_buy_stock * tradeing_price, 2)
    # 매매 수수료 계산
    buy_fee = CalculateFee(actual_buy_amount)
    # 전체 잔고 계산
    balance_amount -= (actual_buy_amount + buy_fee)
    # 전체 보유 수량 계산
    Number_share_held += actual_number_buy_stock
    # 전체 매수 금액 계산
    total_stock_buy_amount += actual_buy_amount
    # 평균 매수가 계산  
    average_buy_amount = round(total_stock_buy_amount / Number_share_held, 2)        
        
    return balance_amount, Number_share_held, average_buy_amount, round(total_stock_buy_amount, 2), trading_flag

def Sell(tradeing_price, balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, sell_point):
    """
    주식 매도 함수
    tradeing_price: 매매기준가
    balance_amount: 잔액
    Number_share_held: 보유 주식 수
    average_buy_amount: 평균 매수가
    total_stock_buy_amount: 전체 매수 금액
    init_trade_start_yn: 초기 거래 여부
    sell_point: 매도 포인트
    return: 갱신된 잔고와 거래 정보
    """
    acutual_number_sell_stock = 0 # 실제 매도 주식수
    
    # 매매기준가 < 매도 포인트, 버퍼 매도
    if tradeing_price < average_buy_amount * (1 + sell_point):
        # 버퍼 매도
        acutual_number_sell_stock = int(Number_share_held / buffer_sell_divide)
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * tradeing_price, 2)
        
        # 전체 보유 수량 계산
        Number_share_held -= acutual_number_sell_stock
        
        if Number_share_held == 0:
            # 잔액 초기화
            init_trade_start_yn, Number_share_held, total_stock_buy_amount, average_buy_amount = Init()
        else:
            # 전체 매수 금액 계산
            total_stock_buy_amount = round(Number_share_held * average_buy_amount,2)
            
        trading_flag = f"SELL/{buffer_sell_divide}"     
    else: 
        # 전량 매도
        acutual_number_sell_stock = Number_share_held
        # 실제 매도 금액
        actual_sell_amount = round(acutual_number_sell_stock * (average_buy_amount * (1 + sell_point)), 2)
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
    init_trade_start_yn = "Y"
    
    # # 로깅을 위한 파일명 설정 (현재 날짜와 시간을 기반으로 파일명 생성)
    # timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # filename = f'logs/{stock_name}_{start_trade_date}_{end_trade_date}_{buy_times}_{buffer_trading_point}_{sell_point}_{timestamp}.log'

    # # 로거 설정
    # logging.basicConfig(filename=filename, level=logging.DEBUG, format='%(message)s')
    
    # 그래프 데이터를 저장할 리스트 초기화
    dates = []
    trading_prices = []
    average_buy_amounts = []
    assessment_amounts = []
    
    # 주식 이력이 비어있을 경우 주식 정보 설정
    if not stock_history:
        stock_history = SetStockFinalPriceByDate(stock_name, start_trade_date, end_trade_date)
        stock_history.reset_index(inplace=True)
        
    # 주식 이력을 반복하며 거래 수행
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
            print("Set the trading price flag")
            break
        
        # 초기화 이후 첫 거래
        if init_trade_start_yn == "Y":
            # 매수 금액 설정
            one_time_buy_amount = assessment_amount / buy_times
            # 매수 처리
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(tradeing_price, 
                                                                                                balance_amount, 
                                                                                                one_time_buy_amount, 
                                                                                                Number_share_held, 
                                                                                                average_buy_amount, 
                                                                                                total_stock_buy_amount,
                                                                                                buffer_trading_point,
                                                                                                init_trade_start_yn)
            # 초기 후 거래 설정    
            init_trade_start_yn = "N"
        # 손절매 체크 (손절매는 close 가격으로)
        elif close_prcice < average_buy_amount * (1 - stop_loss_threshold) :
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = StopLoss(close_prcice, 
                                                                                                                   balance_amount, 
                                                                                                                   Number_share_held, 
                                                                                                                   average_buy_amount, 
                                                                                                                   total_stock_buy_amount)
        # 매수 거래,  매매기준가 < 버퍼 매매 평단 && 잔고충분
        elif tradeing_price < average_buy_amount + (average_buy_amount * buffer_trading_point) and balance_amount > one_time_buy_amount:
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, trading_flag = Buy(tradeing_price, 
                                                                                              balance_amount, 
                                                                                              one_time_buy_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              buffer_trading_point,
                                                                                              init_trade_start_yn)
        # 매도 거래, 매매기준가 > 버퍼 매매 평단 
        elif tradeing_price > average_buy_amount + (average_buy_amount * buffer_trading_point):
            balance_amount, Number_share_held, average_buy_amount, total_stock_buy_amount, init_trade_start_yn, trading_flag = Sell(tradeing_price, 
                                                                                              balance_amount, 
                                                                                              Number_share_held, 
                                                                                              average_buy_amount, 
                                                                                              total_stock_buy_amount,
                                                                                              init_trade_start_yn,
                                                                                              sell_point)        
        # 평가 금액 = 잔고 + 보유주식수 * 종가
        assessment_amount = round(balance_amount + (Number_share_held * tradeing_price), 2)
        
        # 로깅
        log = f"날짜: {str(date)[0:10]},\t매매기준가: {tradeing_price:.2f},\t매매: {trading_flag},\t잔고: {balance_amount:.2f},\
\t보유주식수: {Number_share_held},\t평균매수금액: {average_buy_amount},\t전체매수금액: {total_stock_buy_amount},\t평가금액: {assessment_amount}"
        
        if not batch_yn:
            print(log)
            # 그래프 데이터 저장
            dates.append(date)
            trading_prices.append(tradeing_price)
            if average_buy_amount != 0:
                average_buy_amounts.append(average_buy_amount)
            else:
                average_buy_amounts.append(None)  # 0인 경우 None 추가
            assessment_amounts.append(assessment_amount)
        
    if not batch_yn:
        # 그래프 그리기
        fig, ax1 = plt.subplots()
        ax1.plot(dates, trading_prices, color='green', alpha=0.5)
        ax1.set_ylabel(f'{trading_price_flag} Price', color='green', rotation=0)
        ax1.plot(dates, average_buy_amounts, color='blue', alpha=0.7, label='Avg Buy Amount')
        ax2 = ax1.twinx()
        ax2.plot(dates, assessment_amounts, color='red', alpha=0.5)
        ax2.set_ylabel('Assessment Amount', color='red', rotation=0)
        plt.show()
    else:
        return assessment_amount

if __name__ == "__main__":
    # 거래 시작
    DoTrading(stock_name, balance_amount, start_trade_date, end_trade_date, buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold, batch_yn)
