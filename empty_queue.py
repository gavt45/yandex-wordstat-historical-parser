import redis

c = redis.Redis()

while c.llen("tasks"):
    c.rpop("tasks")

while c.llen("done"):
    c.rpop("done")

