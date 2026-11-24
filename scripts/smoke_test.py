import json, time, urllib.request

BASE = "http://localhost:8000"
def call(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
        headers={"Content-Type":"application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())

print("Health:", call("/health"))
print("Readiness:", call("/ready"))
job_id = "smoke-" + str(int(time.time()))
print("Submit:", call("/jobs", "POST", {"job_id":job_id, "text":"smoke test"}))
for _ in range(20):
    status = call("/jobs/" + job_id)
    if status["status"] == "completed":
        print("Result:", status)
        break
    time.sleep(1)
else:
    raise SystemExit("Job did not complete in 20 seconds")
print("Smoke test passed")
