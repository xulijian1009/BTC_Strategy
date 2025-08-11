import pandas as pd
import pandas_ta as ta


def rsi(df: pd.DataFrame, period=14):
    df['rsi'] = ta.rsi(df['close'], length=period)


def atr(df: pd.DataFrame, period=14):
    df['atr'] = ta.atr(high=df['high'], low=df['low'], close=df['close'], length=period)
    


def adx(df: pd.DataFrame, period=14):
    adx_df = ta.adx(high=df['high'], low=df['low'], close=df['close'], length=period)
    df['adx'] = adx_df[f'ADX_{period}']
    df['di_plus'] = adx_df[f'DMP_{period}']
    df['di_minus'] = adx_df[f'DMN_{period}']
    


def supertrend(df: pd.DataFrame, period=7, multiplier=3.0):
    st = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=period, multiplier=multiplier)
    df['supertrend'] = st.iloc[:, 0]  # 默认取第一列 SUPERT_x_x
    


def ema(df: pd.DataFrame, period=20):
    df[f'ema_{period}'] = ta.ema(df['close'], length=period)
    


def sma(df: pd.DataFrame, period=50):
    df[f'sma_{period}'] = ta.sma(df['close'], length=period)
    


def macd(df: pd.DataFrame):
    macd_df = ta.macd(df['close'])
    df['macd'] = macd_df['MACD_12_26_9']
    df['macd_signal'] = macd_df['MACDs_12_26_9']
    df['macd_hist'] = macd_df['MACDh_12_26_9']
    
