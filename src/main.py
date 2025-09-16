# main.py for Raspberry Pi Pico W
# Title: Pico Light Orchestra Instrument Code

import machine
import time
import network
import json
import asyncio
import math
# --- RGB LED Pin Configuration ---
# Common cathode RGB LED: GP2=Red, GP3=Green, GP4=Blue (each via 100 ohm resistor)
red_pwm = machine.PWM(machine.Pin(2))
green_pwm = machine.PWM(machine.Pin(3))
blue_pwm = machine.PWM(machine.Pin(15))

# Set PWM frequency (Hz)
for pwm in (red_pwm, green_pwm, blue_pwm):
    pwm.freq(1000)
# --- Core Functions ---

# --- HSV to RGB conversion (0-1 floats in, 0-255 ints out) ---
def hsv_to_rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    hi = int(h / 60) % 6
    f = (h / 60) - math.floor(h / 60)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    if hi == 0:
        r, g, b = v, t, p
    elif hi == 1:
        r, g, b = q, v, p
    elif hi == 2:
        r, g, b = p, v, t
    elif hi == 3:
        r, g, b = p, q, v
    elif hi == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)

# --- Set RGB LED color (0-255 per channel) ---
def set_rgb(r, g, b):
    # Invert for common cathode: 0=off, 255=full brightness
    red_pwm.duty_u16(65535 - int(r * 257))
    green_pwm.duty_u16(65535 - int(g * 257))
    blue_pwm.duty_u16(65535 - int(b * 257))

# --- Coroutine to max out each LED pin one at a time ---
async def rgb_one_at_a_time(delay_ms=500):
    while True:
        set_rgb(255, 0, 0)  # Red on
        await asyncio.sleep_ms(delay_ms)
        set_rgb(0, 255, 0)  # Green on
        await asyncio.sleep_ms(delay_ms)
        set_rgb(0, 0, 255)  # Blue on
        await asyncio.sleep_ms(delay_ms)

# --- Pin Configuration ---
# The photosensor is connected to an Analog-to-Digital Converter (ADC) pin.
# We will read the voltage, which changes based on light.
photo_sensor_pin = machine.ADC(26)

# The buzzer is connected to a GPIO pin that supports Pulse Width Modulation (PWM).
# PWM allows us to create a square wave at a specific frequency to make a sound.
buzzer_pin = machine.PWM(machine.Pin(10))
buzzer_pin2 = machine.PWM(machine.Pin(13))

# --- Global State ---
# This variable will hold the task that plays a note from an API call.
# This allows us to cancel it if a /stop request comes in.
api_note_task = None

# --- Core Functions ---


def connect_to_wifi(wifi_config: str = "wifi_config.json"):
    """Sets up the Pico W as a WiFi Access Point (AP mode)."""
    ap_ssid = "Pico-Orchestra"
    ap_password = "picopassword"  # Minimum 8 characters
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password)
    print(f"Access Point started! SSID: {ap_ssid}, Password: {ap_password}")
    # Wait for AP to be active
    while not ap.active():
        time.sleep(1)
    ip_address = ap.ifconfig()[0]
    print(f"Pico AP IP Address: {ip_address}")
    return ip_address


def play_tone(frequency: int, duration_ms: int) -> None:
    """Plays a tone on the buzzer for a given duration."""
    if frequency > 0:
        buzzer_pin.freq(int(frequency))
        buzzer_pin2.freq(int(frequency))
        buzzer_pin.duty_u16(32768)  # 50% duty cycle
        buzzer_pin2.duty_u16(32768)  # 50% duty cycle
        time.sleep_ms(duration_ms)  # type: ignore[attr-defined]
        stop_tone()
    else:
        time.sleep_ms(duration_ms)  # type: ignore[attr-defined]


def stop_tone():
    """Stops any sound from playing."""
    buzzer_pin.duty_u16(0)  # 0% duty cycle means silence
    buzzer_pin2.duty_u16(0)  # 0% duty cycle means silence


async def play_api_note(frequency, duration_s):
    """Coroutine to play a note from an API call, can be cancelled."""
    try:
        print(f"API playing note: {frequency}Hz for {duration_s}s")
        buzzer_pin.freq(int(frequency))
        buzzer_pin2.freq(int(frequency))
        buzzer_pin.duty_u16(32768)  # 50% duty cycle
        buzzer_pin2.duty_u16(32768)  # 50% duty cycle
        await asyncio.sleep(duration_s)
        stop_tone()
        print("API note finished.")
    except asyncio.CancelledError:
        stop_tone()
        print("API note cancelled.")


def map_value(x, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another."""
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


async def handle_request(reader, writer):
    """Handles incoming HTTP requests."""
    global api_note_task

    print("Client connected")
    request_line = await reader.readline()
    # Skip headers
    while await reader.readline() != b"\r\n":
        pass

    try:
        request = str(request_line, "utf-8")
        method, url, _ = request.split()
        print(f"Request: {method} {url}")
    except (ValueError, IndexError):
        writer.write(b"HTTP/1.0 400 Bad Request\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Read current sensor value
    light_value = photo_sensor_pin.read_u16()

    response = ""
    content_type = "text/html"

    # --- API Endpoint Routing ---
    if method == "GET" and url.startswith("/set_color"):
        # Parse color from query string
        import ure
        match = ure.search(r"color=([a-zA-Z]+)", url)
        color = match.group(1).lower() if match else ""
        if color == "red":
            set_rgb(255, 0, 0)
        elif color == "green":
            set_rgb(0, 255, 0)
        elif color == "blue":
            set_rgb(0, 0, 255)
        else:
            set_rgb(0, 0, 0)
        response = f'{{"status": "ok", "color": "{color}"}}'
        content_type = "application/json"
    elif method == "GET" and url == "/":
        html = f"""
        <html>
            <body>
                <h1>Pico Light Orchestra</h1>
                <p>Current light sensor reading: {light_value}</p>
                <button onclick=\"fetch('/set_color?color=red')\">Red</button>
                <button onclick=\"fetch('/set_color?color=green')\">Green</button>
                <button onclick=\"fetch('/set_color?color=blue')\">Blue</button>
            </body>
        </html>
        """
        response = html
    elif method == "POST" and url == "/play_note":
        # This requires reading the request body, which is not trivial.
        # A simple approach for a known content length:
        # Note: A robust server would parse Content-Length header.
        # For this student project, we'll assume a small, simple JSON body.
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            freq = data.get("frequency", 0)
            duration = data.get("duration", 0)

            # If a note is already playing via API, cancel it first
            if api_note_task:
                api_note_task.cancel()

            # Start the new note as a background task
            api_note_task = asyncio.create_task(play_api_note(freq, duration))

            response = '{"status": "ok", "message": "Note playing started."}'
            content_type = "application/json"
        except (ValueError, json.JSONDecodeError):
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error": "Invalid JSON"}\r\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

    elif method == "POST" and url == "/stop":
        if api_note_task:
            api_note_task.cancel()
            api_note_task = None
        stop_tone()  # Force immediate stop
        response = '{"status": "ok", "message": "All sounds stopped."}'
        content_type = "application/json"
    else:
        writer.write(b"HTTP/1.0 404 Not Found\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Send response
    writer.write(
        f"HTTP/1.0 200 OK\r\nContent-type: {content_type}\r\n\r\n".encode("utf-8")
    )
    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")


async def main():
    """Main execution loop."""
    # Try to connect to WiFi and start web server if successful
    try:
        ip = connect_to_wifi()
        print(f"Web server running at http://{ip}/")
        server = await asyncio.start_server(handle_request, "0.0.0.0", 80)
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"WiFi/web server failed: {e}\nRunning in default mode.")
        # Fallback: run default behavior
        print("Use light sensor to control musical tones!")
        print("RGB LED will smoothly transition through the color spectrum.")
        rgb_task = asyncio.create_task(rgb_one_at_a_time())
        while True:
            light_value = photo_sensor_pin.read_u16()
            min_light = 1000
            max_light = 65000
            min_freq = 261  # C4
            max_freq = 1046  # C6
            clamped_light = max(min_light, min(light_value, max_light))
            if clamped_light > min_light:
                frequency = map_value(
                    clamped_light, min_light, max_light, min_freq, max_freq
                )
                buzzer_pin.freq(frequency)
                buzzer_pin2.freq(frequency)
                buzzer_pin.duty_u16(32768)
                buzzer_pin2.duty_u16(32768)
            else:
                stop_tone()
            await asyncio.sleep_ms(50)


# Run the main event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
        stop_tone()