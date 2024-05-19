import subprocess
import pandas as pd
from infinitetrading import DoTrading

if __name__ == "__main__":
        
    # Excel 파일 로드
    df = pd.read_excel('infinitTrading.xlsx')
    
    # print(df.describe)
    for index, row in df.iterrows():
        stock_name = row["stock_name"]  # 주식 종목명
        balance_amount = row["balance_amount"]  # 전체 잔액
        start_trade_date = str(row["start_trade_date"])[0:10]  # 거래 시작일
        end_trade_date = str(row["end_trade_date"])[0:10]  # 거래 종료일
        buy_times = row["buy_times"]  # 매수 회차
        buffer_trading_point = row["buffer_trading_point"]  # 버퍼 매매 포인트
        sell_point = row["sell_point"]  # 매도 포인트
        buffer_buy_divide = row["buffer_buy_divide"] # 버퍼 매수 분할 수치
        buffer_sell_divide = row["buffer_sell_divide"] # 버퍼 매도 분할 수치
        stop_loss_threshold = row["stop_loss_threshold"]  # 손절매 기준 예: 10%
        batch_yn = False
        
        assessment_result = DoTrading(stock_name,balance_amount,start_trade_date,end_trade_date,buy_times,buffer_trading_point,sell_point,buffer_buy_divide,buffer_sell_divide,stop_loss_threshold,batch_yn)
    
        print(f"Assessment result: {assessment_result}")
        
        # row['final_assessment'] = assessment_result
        df.at[index, 'final_assessment'] = float(assessment_result)
        
    # print(df['final_assessment'])
 
    # 변경된 DataFrame을 sheet2에 저장
    with pd.ExcelWriter('infinitTrading.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='Result', index=False)

 
