from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

JOBS_SUBMITTED = Counter("inference_jobs_submitted_total", "Jobs accepted by the API")
JOBS_PROCESSED = Counter("inference_jobs_processed_total", "Jobs successfully processed")
JOBS_FAILED = Counter("inference_jobs_failed_total", "Jobs moved to dead-letter queue")
RETRIES = Counter("inference_worker_retries_total", "Worker processing retries")
DLQ_TOTAL = Counter("inference_dead_letter_total", "Messages sent to dead-letter stream")
PROCESSING_SECONDS = Histogram("inference_job_processing_seconds", "Inference processing duration")
QUEUE_DEPTH = Gauge("inference_queue_depth", "Approximate stream length")

def metrics_payload():
    return generate_latest(), CONTENT_TYPE_LATEST
