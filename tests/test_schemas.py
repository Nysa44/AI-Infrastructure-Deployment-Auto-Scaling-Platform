import pytest
from pydantic import ValidationError
from app.schemas import JobRequest

def test_valid_request():
    assert JobRequest(job_id="job-001", text="hello").job_id == "job-001"

@pytest.mark.parametrize("job_id", ["", "has spaces", "bad/slash", "x" * 81])
def test_invalid_job_ids(job_id):
    with pytest.raises(ValidationError):
        JobRequest(job_id=job_id, text="hello")

def test_empty_text_rejected():
    with pytest.raises(ValidationError):
        JobRequest(job_id="job-001", text="")

def test_text_over_limit_rejected():
    with pytest.raises(ValidationError):
        JobRequest(job_id="job-001", text="x" * 5001)

def test_extra_fields_rejected():
    with pytest.raises(ValidationError):
        JobRequest(job_id="job-001", text="hello", admin=True)
