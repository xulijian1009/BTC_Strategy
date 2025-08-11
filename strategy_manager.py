import threading
from sqlalchemy import create_engine, text
from config import DB_URI
from strategy_runner import run_strategy
from monitor_trades import run_monitor_loop


engine = create_engine(DB_URI)

with engine.begin() as conn:
    conn.execute(text("UPDATE strategies SET running = FALSE"))

running_strategies = {}

def start_strategy(strategy_id, config_dict):
    """启动指定策略线程，并将配置写入数据库。"""
    if running_strategies.get(strategy_id):
        return f"策略 {strategy_id} 已在运行中"

    config_dict["strategy_id"] = strategy_id
    running_flag = {"running": True}
    running_strategies[strategy_id] = running_flag

    symbol = config_dict["symbol"]

    # 启动策略主线程
    threading.Thread(target=run_strategy, args=(config_dict, running_flag), daemon=True).start()

    # 启动订单监控线程
    threading.Thread(
        target=run_monitor_loop,
        args=(strategy_id, symbol, running_flag),
        daemon=True
    ).start()
    # ✅ 将策略配置同步更新到数据库
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE strategies SET
                symbol = :symbol,
                `interval` = :interval,
                position_size = :position_size,
                leverage = :leverage,
                take_profit_percent = :take_profit_percent,
                stop_loss_percent = :stop_loss_percent,
                rsi_period = :rsi_period,
                rsi_acc_period = :rsi_acc_period,
                rsi_long_threshold = :rsi_long_threshold,
                rsi_short_threshold = :rsi_short_threshold,
                updated_at = NOW(),
                running = TRUE
            WHERE strategy_id = :strategy_id
        """), config_dict)

    return f"🎯 策略 {strategy_id} 启动成功"


def stop_strategy(strategy_id):
    """停止指定策略线程，并更新数据库状态。"""
    running = running_strategies.get(strategy_id)
    if running:
        running["running"] = False

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE strategies SET running = FALSE, updated_at = NOW()
                WHERE strategy_id = :sid
            """), {"sid": strategy_id})

        return f"🛑 策略 {strategy_id} 已停止"
    else:
        return f"⚠️ 策略 {strategy_id} 未运行"
