"""A cache key for a backtest: the same key must mean the same result."""
import hashlib
import json


def run_key(code_version, data_version, params):
    if data_version == "latest":
        raise ValueError("a moving name is not a version")
    text = json.dumps([code_version, data_version, params], sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:16]
