import hashlib

def run_inference(text: str) -> dict:
    # Deterministic demo adapter; replace this function with a real model client.
    normalized = " ".join(text.lower().split())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    score = round((int(digest[:8], 16) % 10000) / 10000, 4)
    return {
        "label": "positive" if score >= 0.5 else "negative",
        "score": score,
        "input_characters": len(normalized),
        "model": "demo-deterministic-v1",
    }
