import pandas as pd
import config

def check_rsi(
    df: pd.DataFrame,
    long_threshold: float,
    short_threshold: float
):
    """TODO: 判断是否满足开仓条件，返回信号和 RSI 值。"""
    if df.empty or "rsi" not in df.columns or "rsi_acc" not in df.columns:
        return None, None, None
    
    latest_rsi = df["rsi"].iloc[-1]
    rsi_acc = df["rsi_acc"].iloc[-1]

    if pd.isna(latest_rsi) or pd.isna(rsi_acc):
        return None, None, None

    if rsi_acc < long_threshold:
        return "long", latest_rsi, rsi_acc
    elif rsi_acc > short_threshold:
        return "short", latest_rsi, rsi_acc
    else:
        return None, latest_rsi, rsi_acc


def calculate_tp_sl(signal, open_price, leverage, tp_pct, sl_pct):
    """计算止盈止损价格"""
    if signal == "long":
        tp_price = open_price * (1 + tp_pct / leverage / 100)
        sl_price = open_price * (1 - sl_pct / leverage / 100)
    else:
        tp_price = open_price * (1 - tp_pct / leverage / 100)
        sl_price = open_price * (1 + sl_pct / leverage / 100)
    return int(tp_price), int(sl_price)



def calculate_pnl(signal, open_price, current_price, size, par, fee_rate=config.FEE_RATE):
    """计算盈亏"""
    if signal == "long":
        pnl = (current_price - open_price) * size * par
    else:
        pnl = (open_price - current_price) * size * par
    

    open_fee = open_price * size * par * fee_rate
    close_fee = current_price * size * par * fee_rate
    total_fee = open_fee + close_fee
    
    # 净盈亏
    net_pnl = pnl - total_fee
    return net_pnl