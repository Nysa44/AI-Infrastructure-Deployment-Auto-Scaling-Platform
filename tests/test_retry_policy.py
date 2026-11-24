def retry_or_dead_letter(attempt, max_retries=3):
    return "dead_letter" if attempt + 1 >= max_retries else "retry"

def test_early_failure_retries():
    assert retry_or_dead_letter(0) == "retry"

def test_final_failure_dead_letters():
    assert retry_or_dead_letter(2) == "dead_letter"
