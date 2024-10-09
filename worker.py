import os 
import redis
import logging
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

#redis_url = os.getenv("REDISCLOUD_URL")

conn = redis.from_url("redis://default:wLzcQ5mI3BbsxIHoi7FV706tWzrQHi3D@redis-12778.c92.us-east-1-3.ec2.redns.redis-cloud.com:12778")

try:
    conn.ping()
    print("Redis connection successful!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logging.info('Starting worker...')
    try:
        with Connection(conn):
            queues = [Queue(name) for name in listen]  # Create list of Queue objects
            worker = Worker(queues)  # Pass the list of queues to the worker
            worker.work()
    except Exception as e:
        logging.error(f'Worker crashed: {e}')

        