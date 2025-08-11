from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
import config
import pandas as pd
import gate
from strategy_manager import start_strategy, stop_strategy

app = Flask(__name__)

engine = create_engine(config.DB_URI)

@app.route("/", methods=["GET", "POST"])
def index():
    """TODO: 添加函数 index 的描述。"""
    with engine.connect() as conn:
        strategies = pd.read_sql("SELECT * FROM strategies ORDER BY id", conn)

    if request.method == "POST":
        strategy_id = request.form.get("strategy_id")
        if "start" in request.form:
            config_dict = {
                "symbol": "BTC_USDT",
                "interval": request.form["interval"],
                "position_size": int(request.form["position_size"]),
                "leverage": int(request.form["leverage"]),
                "take_profit_percent": float(request.form["take_profit_percent"]),
                "stop_loss_percent": float(request.form["stop_loss_percent"]),
                "rsi_period": int(request.form["rsi_period"]),
                "rsi_acc_period": int(request.form["rsi_acc_period"]),
                "rsi_long_threshold": float(request.form["rsi_long_threshold"]),
                "rsi_short_threshold": float(request.form["rsi_short_threshold"]),
                "max_positions": int(request.form["max_positions"]),
            }
            start_strategy(strategy_id, config_dict)
        elif "stop" in request.form:
            stop_strategy(strategy_id)
        return redirect(url_for("index"))

    return render_template("index.html", strategies=strategies.to_dict(orient="records"))

@app.route("/kline/<symbol>/<interval>")
def kline(symbol, interval):
    """实时获取K线图"""
    try:
        # 获取查询参数中的RSI配置
        rsi_period = request.args.get('rsi_period', type=int)
        rsi_acc_period = request.args.get('rsi_acc_period', type=int)
        # print(rsi_period)
        # print(rsi_acc_period)
        data = gate.get_kline(
            symbol, 
            interval, 
            as_dict=True,
            rsi_period=rsi_period,
            rsi_acc_period=rsi_acc_period
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logs/<strategy_id>")
def logs(strategy_id):
    """获取策略知行日志"""
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT time, message FROM logs WHERE strategy_id = %s ORDER BY id DESC limit 20",
            conn, params=(strategy_id,)
        )
        df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(df.to_dict(orient="records"))

@app.route("/trades/<strategy_id>")
def trades(strategy_id):
    """获取策略订单"""
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT * FROM trades WHERE strategy_id = %s ORDER BY id DESC", 
            conn, params=(strategy_id,)
        )

        # 格式化时间
        df["open_time"] = pd.to_datetime(df["open_time"], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
        df["close_time"] = pd.to_datetime(df["close_time"], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")

        # 替换 NaN 为 "-"
        df = df.fillna("-")

        return jsonify(df.to_dict(orient="records"))


@app.route("/closures/<strategy_id>")
def get_closures(strategy_id):
    """获取止盈止损记录"""
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT * FROM closures WHERE strategy_id=%s ORDER BY close_time DESC limit 20", 
            conn, params=(strategy_id,)
        )
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/ticker/<symbol>")
def get_ticker(symbol):
    data = gate.get_ticker(symbol)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

