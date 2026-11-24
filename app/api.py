import json
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from app.config import REDIS_STREAM, RESULT_PREFIX
from app.metrics import JOBS_SUBMITTED, metrics_payload
from app.redis_client import get_redis, ensure_group
from app.schemas import JobRequest

app = FastAPI(title="AI Infrastructure Auto-Scaling Platform", version="1.0.0")

@app.on_event("startup")
def startup():
    ensure_group(get_redis())

@app.get("/health")
def health():
    return {"status": "alive"}

@app.get("/ready")
def ready():
    try:
        get_redis().ping()
        return {"status": "ready", "redis": "connected"}
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc

@app.get("/metrics")
def metrics():
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)

@app.post("/jobs", status_code=202)
def submit_job(request: JobRequest):
    client = get_redis()
    result_key = RESULT_PREFIX + request.job_id
    existing = client.get(result_key)
    if existing:
        return {"job_id": request.job_id, "status": "completed", "result": json.loads(existing), "duplicate": True}
    reservation = "inference:submitted:" + request.job_id
    if not client.set(reservation, "1", nx=True, ex=86400):
        return {"job_id": request.job_id, "status": "queued", "duplicate": True}
    try:
        client.xadd(REDIS_STREAM, {"job_id": request.job_id, "text": request.text, "attempt": "0"})
        JOBS_SUBMITTED.inc()
    except Exception:
        client.delete(reservation)
        raise
    return {"job_id": request.job_id, "status": "queued", "duplicate": False}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    client = get_redis()
    result = client.get(RESULT_PREFIX + job_id)
    if result:
        return {"job_id": job_id, "status": "completed", "result": json.loads(result)}
    failure = client.get("inference:failed:" + job_id)
    if failure:
        return {"job_id": job_id, "status": "dead_letter", "error": failure}
    if client.exists("inference:submitted:" + job_id):
        return {"job_id": job_id, "status": "queued"}
    raise HTTPException(status_code=404, detail="Job not found")
