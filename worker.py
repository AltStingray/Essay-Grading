import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

#redis_url = os.getenv("REDISCLOUD_URL")

conn = redis.from_url("redis://default:wLzcQ5mI3BbsxIHoi7FV706tWzrQHi3D@redis-12778.c92.us-east-1-3.ec2.redns.redis-cloud.com:12778")

q = Queue(connection=conn)

try:
    conn.ping()
    print("Redis connection successful!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")

with Connection(conn):
        worker = Worker("default")
        worker.work()

        