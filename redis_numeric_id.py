import redis
from datetime import datetime, timedelta

class RedisNumericIDGenerator:
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.redis = redis.Redis(host=host, port=port, db=db, password=password)

    def get_numeric_id(self, prefix_date=True, counter_digits=6):
        """
        生成纯数字ID，如：20250804000001

        :param prefix_date: 是否使用当前日期作为前缀
        :param counter_digits: 自增位数，不足左补0
        :return: 纯数字字符串
        """
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        redis_key = f"NUMID:{date_str}"

        counter = self.redis.incr(redis_key)

        # 设置Redis key在当天23:59:59过期（只设置一次）
        if counter == 1:
            expire_at = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
            ttl = int((expire_at - now).total_seconds())
            self.redis.expire(redis_key, ttl)

        counter_str = str(counter).zfill(counter_digits)
        return f"{date_str}{counter_str}" if prefix_date else counter_str
