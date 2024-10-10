import redis
import logging


#listen = ['high', 'default', 'low']

#redis_url = os.getenv("REDISCLOUD_URL")

conn = redis.from_url("rediss://:p12c44fffdc8c8c946d2ff90391affe0b7bdcd87e15565f1feeab19cd6d93c7a6@ec2-54-146-141-60.compute-1.amazonaws.com:12410")

try:
    conn.ping()
    print("Redis connection successful!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")


        