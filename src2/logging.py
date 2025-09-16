import ujson as json  # MicroPython’s lightweight json
import uos
import time

def log_request(method: str, url: str, light_value: int) -> None:
    """Append a request log entry to logs.db"""
    entry = {
        "timestamp": time.time(),
        "method": method,
        "url": url,
        "light_value": light_value,
    }
    try:
        with open("logs.db", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print("Logging failed:", e)
