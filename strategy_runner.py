import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from config import DB_URI
import strategy
from trader import execute_trade
from gate import get_kline, get_ticker

engine = create_engine(DB_URI)

def wait_until_next_interval(interval_sec: int):
    """计算当前时间到下一个周期的秒数并休眠。"""
    now = datetime.now()
    seconds_since_hour = now.minute * 60 + now.second
    next_tick = ((seconds_since_hour // interval_sec) + 1) * interval_sec
    sleep_time = next_tick - seconds_since_hour
    time.sleep(sleep_time)


def is_latest_kline_closed(df):
    if df.empty or "t" not in df.columns:
        return False

    latest_ts = df["t"].iloc[-1].to_pydatetime()  # 本地时间
    now = datetime.now().replace(second=0, microsecond=0)  # 本地时间

    closed = latest_ts <= now

    # print(f"[{strategy_id}] 最新K线时间：{latest_ts} | 当前本地时间：{now} | 判断结果：{'✅已收盘' if closed else '❌未收盘'}")
    return closed

def run_strategy(row, running_flag):
    """持续运行策略，判断是否满足信号并下单。"""
    strategy_id = row["strategy_id"]
    symbol = row["symbol"]
    interval = row["interval"]
    interval_map = {"1m": 60, "5m": 300, "15m": 900}
    sleep_sec = interval_map.get(interval, 60)
    rsi_period = row["rsi_period"]
    rsi_acc_period = row["rsi_acc_period"]
    rsi_long_threshold = row["rsi_long_threshold"]
    rsi_short_threshold = row["rsi_short_threshold"]
    max_positions = row["max_positions"]

    while running_flag["running"]:
        try:
            # 获取K线并计算指标
            df = get_kline(
                symbol, 
                interval, 
                rsi_period=rsi_period,
                rsi_acc_period=rsi_acc_period
            )

            if not is_latest_kline_closed(df):
                print(f"⏳ 策略【{strategy_id}】运行失败：当前K线未收盘，跳过判断")
                time.sleep(5)  # 小睡几秒等待收盘
                continue

            # 使用策略检查函数判断信号
            signal, rsi, rsi_acc = strategy.check_rsi(
                df,
                rsi_long_threshold,
                rsi_short_threshold
            )

            rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
            rsi_acc_str = f"{rsi_acc:.2f}" if rsi_acc is not None else "N/A"
            # log(strategy_id, f"👉 RSI={rsi_str} | 平滑RSI={rsi_acc_str} | RSI周期={rsi_period} | 回顾周期={rsi_acc_period} | 开多低于={rsi_long_threshold} | 开空高于={rsi_short_threshold}")
            if signal:
                # ✅ 查询持仓中订单数量
                with engine.begin() as conn:
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM trades 
                        WHERE strategy_id = :strategy_id AND status = 'open'
                    """), {"strategy_id": strategy_id})
                    position_count = result.scalar()

                if position_count >= max_positions:
                    log(strategy_id, f"🚫 当前持仓数量为已达最大限制，跳过本轮下单")
                    continue
                ticker = get_ticker(symbol)
                open_price = ticker.get("last")
                if open_price is None:
                    print(f"⚠️ 策略【{strategy_id}】获取实时价格失败，本轮跳过执行")
                    continue
                # 计算是否加倍仓位
                position_size = row["position_size"]
                if rsi_acc is not None and (rsi_acc < 5 or rsi_acc > 95):
                    position_size *= 2
                    log(strategy_id, f"⚠️ RSI平滑值触发双倍下单条件 (rsi_acc={rsi_acc:.2f})，加倍仓位至 {position_size}")

                # 执行下单
                execute_trade(strategy_id, symbol, signal, open_price, position_size, row["leverage"], row["take_profit_percent"], row["stop_loss_percent"])

                signal_text = "做多" if signal == "long" else "做空"
                log(strategy_id, f"{signal_text} | RSI={rsi_str} | 平滑RSI={rsi_acc_str} | 开仓价格={open_price} | 下单成功")        
        except Exception as e:
            print(f"⚠️ 策略【{strategy_id}】执行异常：{e}")

        wait_until_next_interval(sleep_sec)

def log(strategy_id, message):
    """记录策略日志信息。"""
    # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(f"{now} | {message}")
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO logs (strategy_id, time, message) VALUES (:sid, NOW(), :msg)
        """), {"sid": strategy_id, "msg": message})
