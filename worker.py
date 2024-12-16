import redis
import os
from rq import Worker, Queue, Connection

REDIS_CONN = os.environ.get("REDISCLOUD_URL")

listen = ['default']

conn = redis.from_url(REDIS_CONN)

try:
    conn.ping()
    print("Redis connection successful!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")
    
if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()

        