import gate
from datetime import datetime
from sqlalchemy import create_engine, text
from config import DB_URI
import strategy

engine = create_engine(DB_URI)

def execute_trade(strategy_id, symbol, signal, open_price, size, leverage, take_profit_percent, stop_loss_percent):
    """TODO: 执行交易并记录结果。"""
    side = "buy" if signal == "long" else "sell"
    # 以当前价格下单
    open_price = float(open_price)
    result = gate.place_order(symbol, side, size)
    # print(f"{result}: 下单成功......")
    # 记录到 trades 表
    log_trade(strategy_id, signal, open_price, leverage, take_profit_percent, stop_loss_percent, result)
    # print(f"{result["id"]}: 日志记录成功.....")
    # 计算止盈止损价格
    tp_price, sl_price = strategy.calculate_tp_sl(signal, open_price, leverage, take_profit_percent, stop_loss_percent)
    # 创建止盈止损订单
    tp_order = gate.create_price_trigger_order(symbol, size, tp_price, signal, "tp")
    # print(f"{tp_order}: 止盈委托创建成功.....")
    sl_order = gate.create_price_trigger_order(symbol, size, sl_price, signal, "sl")
    # print(f"{sl_order}: 止损委托创建成功.....")
    # 记录到 tp_sl_orders 表
    log_tp_sl_order(strategy_id, result["id"], symbol, "tp", tp_price, tp_order["id"], signal, open_price, size, sl_order["id"])
    # print(f"{tp_order["id"]}: 止盈委托记录成功.....")
    log_tp_sl_order(strategy_id, result["id"], symbol, "sl", sl_price, sl_order["id"], signal, open_price, size, tp_order["id"])
    # print(f"{sl_order["id"]}: 止损委托记录成功.....")
    return result

def log_trade(strategy_id, signal, open_price, leverage, take_profit_percent, stop_loss_percent, result):
    """记录下单信息到 trades 表"""
    sql = text("""
        INSERT INTO trades (
            strategy_id, symbol, open_time, `signal`, open_price, size, leverage, take_profit_percent, stop_loss_percent, status, trade_id
        ) VALUES (
            :strategy_id, :symbol, :open_time, :signal, :open_price, :size, :leverage, :take_profit_percent, :stop_loss_percent, 'open', :trade_id
        )
    """)
    params = {
        "strategy_id": strategy_id,
        "symbol": result.get("contract"),
        "open_time": datetime.fromtimestamp(result.get("finish_time")).strftime("%Y-%m-%d %H:%M:%S"),
        "signal": signal,
        "open_price": open_price,
        "size": result.get("size"),
        "leverage": leverage,
        "take_profit_percent":take_profit_percent,
        "stop_loss_percent":stop_loss_percent,
        "trade_id": result.get("id")
    }
    with engine.begin() as conn:
        conn.execute(sql, params)

def log_tp_sl_order(strategy_id, trade_id, symbol, order_type, price, order_id, signal, open_price, size, pair_id):
    """记录止盈止损订单信息到 tp_sl_orders 表"""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tp_sl_orders (
                strategy_id, trade_id, symbol, order_type, price, order_id, status,
                `signal`, open_price, size, pair_id
            )
            VALUES (
                :strategy_id, :trade_id, :symbol, :order_type, :price, :order_id, 'open',
                :signal, :open_price, :size, :pair_id
            )
        """), {
            "strategy_id": strategy_id,
            "trade_id": trade_id,
            "symbol": symbol,
            "order_type": order_type,
            "price": price,
            "order_id": order_id,
            "signal": signal,
            "open_price": open_price,
            "size": size,
            "pair_id": pair_id
        })