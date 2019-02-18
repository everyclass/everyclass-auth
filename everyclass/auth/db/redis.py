import redis

from everyclass.auth.config import get_config

config = get_config()
redis_client = redis.Redis(**config.REDIS_CONFIG)
