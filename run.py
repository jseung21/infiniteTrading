import subprocess
import pandas as pd

def run_infinite_trading_script(para0, para1, para2, para3, para4, para5, para6, para7, para8):
    # Execute runInfiniteTrading.py and capture its output
    try:
        cmd = ["python", "runInfiniteTrading.py", str(para0), str(para1), str(para2), str(para3), str(para4), str(para5), str(para6), str(para7), str(para8)]
        result = subprocess.check_output(cmd, universal_newlines=True)
        return result.strip()  # Remove any leading/trailing whitespace
    except subprocess.CalledProcessError:
        return "Error executing runInfiniteTrading.py"

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
    
        assessment_result = run_infinite_trading_script(stock_name, balance_amount,start_trade_date,end_trade_date,buy_times,buffer_trading_point,sell_point,buffer_buy_divide,buffer_sell_divide)
        print(f"Assessment result: {assessment_result}")
        
        # row['final_assessment'] = assessment_result
        df.at[index, 'final_assessment'] = float(assessment_result)
        
    # print(df['final_assessment'])
    # 변경된 DataFrame을 다시 Excel 파일로 저장
    df.to_excel('infinitTrading.xlsx', index=False)
    # os.system(f"python runInfiniteTrading.py {stock_name} {balance_amount} {start_trade_date} {end_trade_date} {buy_times} {buffer_trading_point} {sell_point} {buffer_buy_divide} {buffer_sell_divide}") 
