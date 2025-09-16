import network
import uasyncio as asyncio
from machine import Pin

ap = network.WLAN(network.AP_IF)
ap.config(essid="Pico2W_WiFi", password="098765432")
ap.active(True)

while not ap.active():
    pass

print("Access Point active")
print("Network config:", ap.ifconfig())

# ---------- Hardware ----------
led = Pin("LED", Pin.OUT)

# ---------- Route Handlers ----------
def index_page():
    return """\
HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n
<html>
    <head><title>Pico W Server</title></head>
    <body>
        <h1>Hello from Pico W!</h1>
        <p><a href="/status">Check Status</a></p>2
        <p><a href="/led/on">Turn LED ON</a></p>
        <p><a href="/led/off">Turn LED OFF</a></p>
    </body>
</html>
"""

def status_page():
    state = "ON" if led.value() else "OFF"
    return f"""\
HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n
<html>
    <body>
        <h2>Status</h2>
        <p>LED is currently: {state}</p>
        <a href="/">Back</a>
    </body>
</html>
"""

def not_found():
    return "HTTP/1.0 404 Not Found\r\n\r\nRoute not found"

# ---------- Async Request Handler ----------
async def handle_client(reader, writer):
    try:
        request_line = await reader.readline()
        print("Request:", request_line)

        if not request_line:
            await writer.aclose()
            return

        # Decode and parse route
        request = request_line.decode().split(" ")
        if len(request) < 2:
            await writer.aclose()
            return
        path = request[1]

        # Match routes
        if path == "/":
            response = index_page()
        elif path == "/status":
            response = status_page()
        elif path == "/led/on":
            led.on()
            response = status_page()
        elif path == "/led/off":
            led.off()
            response = status_page()
        else:
            response = not_found()

        await writer.awrite(response)
        await writer.aclose()

    except Exception as e:
        print("Error handling client:", e)

# ---------- Async Web Server ----------
async def web_server():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    print("Web server running at http://192.168.4.1")
    await server.wait_closed()

# ---------- Background Task ----------
async def blink_background():
    while True:
        # Example: keep doing something else in parallel
        await asyncio.sleep(5)
        print("Background task still running...")

# ---------- Main ----------
async def main():
    await asyncio.gather(
        web_server(),
        blink_background(),
    )

asyncio.run(main())
