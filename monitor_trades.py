import time
from datetime import datetime
from sqlalchemy import create_engine, text
import strategy
import gate
import config

engine = create_engine(config.DB_URI)

def monitor_trades_once(strategy_id, symbol):
    with engine.begin() as conn:
        ticker = gate.get_ticker(symbol)
        current_price = ticker.get("last")
        if current_price is None:
            print(f"[错误] 监控线程获取实时价格失败，跳过本轮执行")
            return
        try:
            current_price = float(ticker.get("last"))
        except (TypeError, ValueError):
            print(f"[错误] 监控线程获取实时价格失败，返回值异常：{ticker.get("last")}")
            return
        # 查询未触发的止盈止损委托
        result = conn.execute(text("""
            SELECT * FROM tp_sl_orders
            WHERE strategy_id = :strategy_id AND status = 'open'
        """), {"strategy_id": strategy_id})
        rows = result.mappings().all()

        for row in rows:
            try:
                trade_id = row["trade_id"]
                order_id = row["order_id"]
                pair_id = row["pair_id"]
                order_type = row["order_type"]  # 'tp' or 'sl'
                trigger_price = float(row["price"])

                # ✅ 直接从 tp_sl_orders 表中获取判断所需字段
                signal = row["signal"]          # 'long' or 'short'
                size = float(row["size"])
                open_price = float(row["open_price"])

                # 判断是否触发
                is_triggered = False
                if signal == "long":
                    if order_type == "tp" and current_price >= trigger_price:
                        is_triggered = True
                    elif order_type == "sl" and current_price <= trigger_price:
                        is_triggered = True
                elif signal == "short":
                    if order_type == "tp" and current_price <= trigger_price:
                        is_triggered = True
                    elif order_type == "sl" and current_price >= trigger_price:
                        is_triggered = True

                if is_triggered:
                    close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 标记该委托为已触发
                    conn.execute(text("""
                        UPDATE tp_sl_orders SET status = 'finished'
                        WHERE order_id = :order_id
                    """), {"order_id": order_id})

                    # 自动关闭配对单
                    conn.execute(text("""
                        UPDATE tp_sl_orders
                        SET status = 'cancelled'
                        WHERE order_id = :pair_id AND status = 'open'
                    """), {"pair_id": pair_id})

                    # 计算盈亏
                    pnl = strategy.calculate_pnl(signal, open_price, current_price, size, config.BTC_PAR)

                    # 更新主订单为已平仓
                    conn.execute(text("""
                        UPDATE trades
                        SET status = 'closed',
                            close_price = :close_price,
                            pnl = :pnl,
                            close_time = :close_time
                        WHERE trade_id = :trade_id
                    """), {
                        "trade_id": trade_id,
                        "close_price": current_price,
                        "pnl": round(pnl, 4),
                        "close_time": close_time
                    })

                    # 写入平仓记录
                    conn.execute(text("""
                        INSERT INTO closures (strategy_id, trade_id, reason, close_price, pnl, close_time)
                        VALUES (:strategy_id, :trade_id, :reason, :close_price, :pnl, :close_time)
                    """), {
                        "strategy_id": strategy_id,
                        "trade_id": trade_id,
                        "reason": order_type,
                        "close_price": current_price,
                        "pnl": round(pnl, 4),
                        "close_time": close_time
                    })

                    print(f"[平仓] ✅ {order_type.upper()} 触发 | 订单 {trade_id} | 触发价 {trigger_price} | 当前价 {current_price}")
            except Exception as e:
                print(f"[错误] 处理委托 {row.get('order_id')} 出错: {e}")

        # print("已执行一轮监控......")
def run_monitor_loop(strategy_id, symbol, running_flag):
    while running_flag.get("running"):
        monitor_trades_once(strategy_id, symbol)
        time.sleep(1)
