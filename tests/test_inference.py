from app.inference import run_inference

def test_inference_is_deterministic():
    assert run_inference("Hello AI") == run_inference("Hello AI")

def test_normalizes_case_and_whitespace():
    assert run_inference(" HELLO   AI ") == run_inference("hello ai")

def test_result_shape_and_bounds():
    result = run_inference("platform test")
    assert set(result) == {"label", "score", "input_characters", "model"}
    assert result["label"] in {"positive", "negative"}
    assert 0 <= result["score"] <= 1
