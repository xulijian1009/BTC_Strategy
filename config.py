import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
GATE_API_KEY = os.getenv("GATE_API_KEY")
GATE_API_SECRET = os.getenv("GATE_API_SECRET")
BTC_PAR = float(os.getenv("BTC_PAR", "0.0001"))
FEE_RATE = float(os.getenv("FEE_RATE", "0.001"))


MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_DB = os.getenv("MYSQL_DB")
TABLE_NAME = os.getenv("TABLE_NAME")


# ✅ 添加数据库连接字符串供 SQLAlchemy 使用
encoded_pwd = quote_plus(MYSQL_PASSWORD)
DB_URI = f"mysql+pymysql://{MYSQL_USER}:{encoded_pwd}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
