import redis
from rq import Worker, Queue, Connection

listen = ['default']

#redis_url = os.getenv("REDISCLOUD_URL")

conn = redis.from_url("redis://default:wLzcQ5mI3BbsxIHoi7FV706tWzrQHi3D@redis-12778.c92.us-east-1-3.ec2.redns.redis-cloud.com:12778")

try:
    conn.ping()
    print("Redis connection successful!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")
if __name__ == '__main__':
    with Connection(conn):
            worker = Worker(list(map(Queue, listen)))
            worker.work()

        