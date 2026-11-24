import os
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_STREAM = os.getenv("REDIS_STREAM", "inference:jobs")
REDIS_GROUP = os.getenv("REDIS_GROUP", "inference-workers")
REDIS_CONSUMER = os.getenv("REDIS_CONSUMER", "worker-1")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RESULT_PREFIX = "inference:result:"
