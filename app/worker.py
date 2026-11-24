import json
import logging
import time
import redis
from prometheus_client import start_http_server
from app.config import REDIS_STREAM, REDIS_GROUP, REDIS_CONSUMER, MAX_RETRIES, RESULT_PREFIX
from app.inference import run_inference
from app.metrics import JOBS_PROCESSED, JOBS_FAILED, RETRIES, DLQ_TOTAL, PROCESSING_SECONDS, QUEUE_DEPTH
from app.redis_client import get_redis, ensure_group

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("inference-worker")
DLQ_STREAM = REDIS_STREAM + ":dlq"

def process_entry(client, message_id, fields):
    job_id = fields.get("job_id", "unknown")
    started = time.perf_counter()
    try:
        text = fields.get("text", "")
        if not text or len(text) > 5000:
            raise ValueError("text must contain 1..5000 characters")
        result = run_inference(text)
        client.set(RESULT_PREFIX + job_id, json.dumps(result), ex=86400)
        JOBS_PROCESSED.inc()
        client.xack(REDIS_STREAM, REDIS_GROUP, message_id)
    except Exception as exc:
        attempt = int(fields.get("attempt", "0")) + 1
        if attempt >= MAX_RETRIES:
            client.xadd(DLQ_STREAM, {"job_id": job_id, "error": str(exc)[:300], "original_id": message_id})
            client.set("inference:failed:" + job_id, str(exc)[:300], ex=86400)
            client.xack(REDIS_STREAM, REDIS_GROUP, message_id)
            JOBS_FAILED.inc()
            DLQ_TOTAL.inc()
            log.exception("sent %s to DLQ", job_id)
        else:
            RETRIES.inc()
            time.sleep(min(2 ** attempt, 8))
            client.xadd(REDIS_STREAM, {"job_id": job_id, "text": fields.get("text", ""), "attempt": str(attempt)})
            client.xack(REDIS_STREAM, REDIS_GROUP, message_id)
            log.warning("retry %s for %s: %s", attempt, job_id, exc)
    finally:
        PROCESSING_SECONDS.observe(time.perf_counter() - started)

def main():
    start_http_server(8000, addr='0.0.0.0')
    client = get_redis()
    ensure_group(client)
    log.info("worker started: %s", REDIS_CONSUMER)
    while True:
        try:
            QUEUE_DEPTH.set(client.xlen(REDIS_STREAM))
            # Reclaim work left pending by a worker that crashed or was terminated.
            claimed = client.xautoclaim(REDIS_STREAM, REDIS_GROUP, REDIS_CONSUMER, 30000, "0-0", count=10)
            for message_id, fields in claimed[1]:
                process_entry(client, message_id, fields)
            batches = client.xreadgroup(REDIS_GROUP, REDIS_CONSUMER, {REDIS_STREAM: ">"}, count=10, block=5000)
            for _, messages in batches:
                for message_id, fields in messages:
                    process_entry(client, message_id, fields)
        except redis.RedisError:
            log.exception("Redis unavailable; retrying")
            time.sleep(2)

if __name__ == "__main__":
    main()
