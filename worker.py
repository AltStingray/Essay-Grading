import os 
import redis
import logging
from rq import Worker, Queue, Connection

#listen = ['high', 'default', 'low']

#redis_url = os.getenv("REDISCLOUD_URL")


#try:
#    conn.ping()
#    print("Redis connection successful!")
#except redis.ConnectionError as e:
#    print(f"Redis connection failed: {e}")

        