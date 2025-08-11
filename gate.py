import requests
import time
import hmac
import hashlib
import config
import pandas as pd
import json
import indicators
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from redis_numeric_id import RedisNumericIDGenerator

gen = RedisNumericIDGenerator()

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)
BASE_URL = config.BASE_URL

def get_kline(symbol="BTC_USDT", interval="1m", limit=2000, as_dict=False, 
             rsi_period=None, rsi_acc_period=None):
    # print(rsi_period)
    # print(rsi_acc_period)
    """
    获取 K线数据，可选返回 dict list 或 DataFrame。
    """
    url = f"{BASE_URL}/api/v4/futures/usdt/candlesticks"
    params = {"contract": symbol, "interval": interval, "limit": limit}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.json()

        if not isinstance(data, list) or not isinstance(data[0], dict):
            raise ValueError("K线返回格式不正确")

        df = pd.DataFrame(data)
        rename_map = {
            "t": "t", "o": "o", "h": "h", "l": "l", "c": "c"
        }

        # 只保留有效字段
        df = df.rename(columns=rename_map)[["t", "o", "h", "l", "c"]]
        df["t"] = pd.to_datetime(df["t"], unit="s")
        df[["o", "h", "l", "c"]] = df[["o", "h", "l", "c"]].astype(float)

        # 如果提供了RSI参数，计算指标
        if rsi_period is not None and rsi_acc_period is not None:
            
            # 使用indicators.rsi计算RSI
            df["c"] = df["c"].astype(float)
            df.rename(columns={"c": "close"}, inplace=True)
            indicators.rsi(df, period=rsi_period)
            # print("df对象增加rsi指标")
            df.rename(columns={"close": "c"}, inplace=True)
            
            # 计算平滑RSI
            df["rsi_acc"] = df["rsi"].rolling(rsi_acc_period).mean()

            # print("df对象增加rsi_acc指标")

        if as_dict:
            df["t"] = df["t"].dt.tz_localize("UTC").dt.tz_convert("Asia/Shanghai").dt.strftime("%Y-%m-%d %H:%M:%S")
            # 返回包含rsi_acc的列
            columns = ["t", "o", "h", "l", "c"]
            if "rsi" in df.columns:
                columns.append("rsi")
                # print("df对象返回了rsi指标")
            if "rsi_acc" in df.columns:
                columns.append("rsi_acc")
                # print("df对象返回了rsi_acc指标")
            return df[columns].to_dict(orient="records")

        return df

    except Exception as e:
        print(f"❌ 获取 K线失败: {e}")
        return pd.DataFrame() if not as_dict else []



def get_ticker(symbol="BTC_USDT"):
    """获取指定合约的最新成交价格。"""
    url = f"{BASE_URL}/api/v4/futures/usdt/contracts/{symbol}"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {"last": data.get("last_price")}
    except Exception as e:
        print(f"[错误] 获取 Ticker 失败: {e}")
        return {"last": None}


def gen_sign(method, url, query_string=None, payload_string=None):
    key = config.GATE_API_KEY        # api_key
    secret = config.GATE_API_SECRET     # api_secret

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

def place_order(symbol, side, size):
    """TODO: 下单"""
    # ✅ 根据 side 判断 size 是正数（多）还是负数（空）
    adjusted_size = abs(size) if side == "buy" else -abs(size)
    data = {
        "contract": symbol,
        "size": adjusted_size,
        "price": "0",
        "tif": "ioc",
        "text": "t-rsi-bot"
    }

    # # 🔁 模拟响应数据
    # # ✅ 获取市价作为模拟下单价格
    # try:
    #     ticker = get_ticker(symbol)
    #     last_price = str(ticker["last"])  # 保持与官方格式一致，string
    # except:
    #     last_price = "0"

    # now_ts = int(time.time())


    # return {
    #     "id":gen.get_numeric_id(),
    #     "contract": "BTC_USDT",
    #     "status": "simulated",
    #     "price": last_price,
    #     "leverage": 125,
    #     "side": side,
    #     "size": adjusted_size,
    #     "contract": symbol,
    #     "finish_time": now_ts,
    #     "text": "rsi-bot"
    # }

    # ===== 真实下单代码，已注释 =====
    endpoint = "/api/v4/futures/usdt/orders"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    url = BASE_URL + endpoint
    body = json.dumps(data)
    sign_headers = gen_sign("POST", endpoint, "", body)
    headers.update(sign_headers)
    r = requests.post(url, headers=headers, data=body, timeout=5)
    return r.json()

def create_price_trigger_order(symbol, size, trigger_price, signal, trigger_type):
    """
    创建止盈/止损价格触发委托单。
    """
    order_type = ""
    if signal == "long":
        adjusted_size = int(-abs(size)) #平多是负数
        order_type = "plan-close-long-position" # 部分平多委托
        trigger_rule = 1 if trigger_type == "tp" else 2  # tp: >=, sl: <=
    elif signal == "short":
        adjusted_size = int(abs(size)) #平空是正数
        order_type = "plan-close-short-position" # 部分平空委托
        trigger_rule = 2 if trigger_type == "tp" else 1  # tp: <=, sl: >=
    else:
        raise ValueError("Invalid signal")


    data = {
        "initial": {
            "contract": symbol,
            "size": adjusted_size,
            "price": "0",
            "tif": "ioc",
            "reduce_only": True
        },
        "trigger": {
            "strategy_type": 0,
            "price_type": 0,
            "price": str(trigger_price),
            "rule": trigger_rule
        },
        "order_type": order_type,
        "text": f"t-{trigger_type}-auto"
    }

    try:
        # 模拟创建委托单
        # return {
        #     "id":gen.get_numeric_id()
        # }
        endpoint = "/api/v4/futures/usdt/price_orders"
        url = BASE_URL + endpoint
        body = json.dumps(data)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        sign_headers = gen_sign('POST', endpoint, "", body)
        headers.update(sign_headers)
        response = requests.post(url, headers=headers, data=body, timeout=5)
        # print(f"创建止盈/止损订单返回：{response.json()}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 创建{trigger_type}订单失败: {e}")
        return None

