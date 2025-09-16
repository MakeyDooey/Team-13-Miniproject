# AI DISCLAIMER: GPT-5 was used to write documentation, all code was written by people 

"""
integration_test.py
-------------------

Asynchronous integration test suite for the Pico project.

This script launches the web server from `server.py` and interacts with
its endpoints over HTTP to verify end-to-end functionality. It simulates
real client behavior using GET and POST requests, then checks both the
HTTP responses and the persistence of log data.

Tests include:
- GET `/` to confirm the server is running and returning a valid page.
- GET `/set_color` to verify color-setting functionality.
- POST `/play_note` to confirm note playback handling.
- Validation that `logs.db` is updated with request entries.
"""

import uasyncio as asyncio
import ujson as json
import os
import time

try:
    import urequests as requests  # MicroPython
except ImportError:
    import requests  # CPython for local testing

# Start the server as a background task
import server  # your main file with start_server()

async def run_server():
    await server.start_server()

async def integration_test():
    # Give server time to start
    await asyncio.sleep(1)

    # Clear logs if they exist
    try:
        os.remove("logs.db")
    except OSError:
        pass

    # Test 1: GET /
    r = requests.get("http://192.168.4.1:80/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "Hello" in r.text or "Color" in r.text, "Unexpected response body"

    # Test 2: GET /set_color
    r = requests.get("http://192.168.4.1:80/set_color?color=red")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "LED" in r.text or "color" in r.text, "Unexpected response body"

    # Test 3: POST /play_note
    r = requests.post("http://192.168.4.1:80/play_note", data="C")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    # Wait for logs to flush
    await asyncio.sleep(1)

    # Check logs.db contains at least 3 entries
    with open("logs.db") as f:
        logs = [json.loads(line) for line in f]
    assert len(logs) >= 3, f"Expected >=3 logs, got {len(logs)}"

    print("Integration test passed)

asyncio.run(integration_test())
