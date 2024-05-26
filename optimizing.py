import infinitetrading
from scipy.optimize import basinhopping

# 함수 호출 횟수를 기록할 전역 변수
global_call_count = 0

# 최적화할 함수 정의
def objective(params):
    global global_call_count
    global_call_count += 1
    
    buy_times, buffer_trading_point, sell_point, buffer_buy_divide, buffer_sell_divide, stop_loss_threshold = params
    assessment_amount = infinitetrading.DoTrading(
        stock_name=infinitetrading.stock_name,
        balance_amount=infinitetrading.balance_amount,
        start_trade_date=infinitetrading.start_trade_date,
        end_trade_date=infinitetrading.end_trade_date,
        buy_times=int(buy_times),
        buffer_trading_point=buffer_trading_point,
        sell_point=sell_point,
        buffer_buy_divide=int(buffer_buy_divide),
        buffer_sell_divide=int(buffer_sell_divide),
        stop_loss_threshold=stop_loss_threshold,
        batch_yn=True
    )
    # maximize assessment_amount by minimizing its negative
    return -assessment_amount

# 초기값 설정
initial_params = [
    infinitetrading.buy_times,
    infinitetrading.buffer_trading_point,
    infinitetrading.sell_point,
    infinitetrading.buffer_buy_divide,
    infinitetrading.buffer_sell_divide,
    infinitetrading.stop_loss_threshold
]

# 변수의 경계 설정
bounds = [
    (10, 100),  # buy_times
    (1, 10),    # buffer_trading_point
    (1, 10),    # sell_point
    (1, 10),    # buffer_buy_divide
    (1, 10),    # buffer_sell_divide
    (0.01, 0.2) # stop_loss_threshold
]

# 경계를 만족하는지 확인하는 함수
def bounds_check(**kwargs):
    x = kwargs["x_new"]
    for param, (lower, upper) in zip(x, bounds):
        if param < lower or param > upper:
            return False
    return True

# Basin-hopping 최적화 수행
minimizer_kwargs = {
    "method": "L-BFGS-B",
    "bounds": bounds
}

result = basinhopping(
    objective,
    initial_params,
    minimizer_kwargs=minimizer_kwargs,
    niter=100,
    accept_test=bounds_check
)

# 최적화 결과 출력
optimized_params = result.x
optimized_assessment_amount = -result.fun

print("최적화된 변수 값:")
print(f"buy_times: {int(optimized_params[0])}")
print(f"buffer_trading_point: {optimized_params[1]}")
print(f"sell_point: {optimized_params[2]}")
print(f"buffer_buy_divide: {int(optimized_params[3])}")
print(f"buffer_sell_divide: {int(optimized_params[4])}")
print(f"stop_loss_threshold: {optimized_params[5]}")
print(f"최대 평가 금액: {optimized_assessment_amount}")
print(f"함수 호출 횟수: {global_call_count}")
