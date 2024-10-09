import os 
import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

#redis_url = os.getenv("REDISCLOUD_URL")

conn = redis.from_url("redis://default:wLzcQ5mI3BbsxIHoi7FV706tWzrQHi3D@redis-12778.c92.us-east-1-3.ec2.redns.redis-cloud.com:12778")

if __name__ =='__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work