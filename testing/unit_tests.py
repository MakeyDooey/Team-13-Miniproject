# AI DISCLAIMER: GPT-5 was used to write documentation, all code was written by people 

"""
unit_tests.py
--------------

Lightweight unit test suite for the Pico Orchestra project.

This script provides a minimal test runner and a collection of tests for
core functions in `main.py`. It mocks hardware-specific components 
(e.g., PWM, ADC, and Pin) so the logic can be tested without requiring
a Raspberry Pi Pico. Functions tested include color conversion, RGB 
control, tone playback, API note playback, value mapping, and request 
logging.

The script tracks test results, printing a summary of passed and failed
tests when executed directly.
"""

import math
import ujson as json
import time

# --- Mock machine module ---
class MockPWM:
    def __init__(self, pin):
        self.pin = pin
        self._freq = None
        self._duty = None
    def freq(self, f=None):
        if f is not None:
            self._freq = f
        return self._freq
    def duty_u16(self, d):
        self._duty = d
        return d

class MockPin:
    def __init__(self, num):
        self.num = num

class MockADC:
    def __init__(self, pin):
        self.pin = pin
        self._value = 12345
    def read_u16(self):
        return self._value

# --- Import functions from main file ---
from main import (
    hsv_to_rgb, set_rgb, rgb_one_at_a_time,
    connect_to_wifi, play_tone, stop_tone,
    play_api_note, map_value, log_request
)

# Replace hardware-dependent globals with mocks
import main
main.red_pwm = MockPWM(MockPin(2))
main.green_pwm = MockPWM(MockPin(3))
main.blue_pwm = MockPWM(MockPin(15))
main.buzzer_pin = MockPWM(MockPin(10))
main.buzzer_pin2 = MockPWM(MockPin(13))
main.photo_sensor_pin = MockADC(26)

# --- Test Runner ---
results = {"passed": 0, "failed": 0}

def run_test(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
        results["passed"] += 1
    except AssertionError as e:
        print(f"[FAIL] {name} - {e}")
        results["failed"] += 1
    except Exception as e:
        print(f"[ERROR] {name} - {e}")
        results["failed"] += 1

# --- Tests ---

def test_hsv_to_rgb():
    assert hsv_to_rgb(0, 1, 1) == (255, 0, 0)
    assert hsv_to_rgb(120, 1, 1) == (0, 255, 0)
    assert hsv_to_rgb(240, 1, 1) == (0, 0, 255)

def test_set_rgb():
    set_rgb(128, 64, 32)
    assert main.red_pwm._duty is not None
    assert main.green_pwm._duty is not None
    assert main.blue_pwm._duty is not None

def test_map_value():
    assert map_value(5, 0, 10, 0, 100) == 50
    assert map_value(0, 0, 10, -1, 1) == -1
    assert map_value(10, 0, 10, -1, 1) == 1

def test_play_tone_and_stop_tone():
    play_tone(440, 10)
    assert main.buzzer_pin._freq == 440
    stop_tone()
    assert main.buzzer_pin._duty == 0

def test_log_request():
    log_request("GET", "/", 12345)
    with open("logs.db") as f:
        lines = f.readlines()
        last = json.loads(lines[-1])
        assert last["method"] == "GET"
        assert last["url"] == "/"
        assert last["light_value"] == 12345

def test_rgb_one_at_a_time_coroutine():
    # Just check that it is an async generator
    coro = rgb_one_at_a_time(10)
    assert hasattr(coro, "__await__")

def test_play_api_note_coroutine():
    coro = play_api_note(440, 0.01)
    assert hasattr(coro, "__await__")

# --- Run all tests ---
if __name__ == "__main__":
    run_test("HSV to RGB", test_hsv_to_rgb)
    run_test("Set RGB", test_set_rgb)
    run_test("Map Value", test_map_value)
    run_test("Play Tone and Stop Tone", test_play_tone_and_stop_tone)
    run_test("Log Request", test_log_request)
    run_test("RGB One At A Time Coroutine", test_rgb_one_at_a_time_coroutine)
    run_test("Play API Note Coroutine", test_play_api_note_coroutine)

    print("\nTest Summary:")
    print(f"Passed: {results['passed']}, Failed: {results['failed']}")
