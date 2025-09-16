import uasyncio as asyncio
from machine import Pin, PWM, ADC

# --- Pins ---
red_led = Pin(2, Pin.OUT)    
green_led = Pin(3, Pin.OUT)
blue_led = Pin(15, Pin.OUT)

photo_sensor = ADC(Pin(26))   # Photoresistor
buzzer = PWM(Pin(17))         # Buzzer

# --- Configuration ---
# Thresholds for each color (adjust after calibration)
RED_THRESHOLD = 700
GREEN_THRESHOLD = 700
BLUE_THRESHOLD = 700

LOW_FREQ = 262      # Low tone if color detected
HIGH_FREQ = 1046    # High tone if not detected
DUTY = 32768        # 50% duty cycle for buzzer

# --- Helper Functions ---
def play_tone(freq):
    buzzer.freq(freq)
    buzzer.duty_u16(DUTY)

def stop_tone():
    buzzer.duty_u16(0)

# --- Color Detection Loop ---
async def color_detector_loop():
    while True:
        # --- GREEN TEST (active) ---
        red_led.value(0)
        green_led.value(1)   # ON
        blue_led.value(0)
        
        val_green = photo_sensor.read_u16()
        print("Green LED reading:", val_green)
        
        if val_green > GREEN_THRESHOLD:
            play_tone(LOW_FREQ)   # Green detected → low tone
        else:
            play_tone(HIGH_FREQ)  # Not green → high tone
        
        await asyncio.sleep(0.2)
        stop_tone()

        # --- RED TEST (commented out for now) ---
        """
        red_led.value(1)     # ON
        green_led.value(0)
        blue_led.value(0)

        val_red = photo_sensor.read_u16()
        print("Red LED reading:", val_red)

        if val_red > RED_THRESHOLD:
            play_tone(LOW_FREQ)
        else:
            play_tone(HIGH_FREQ)

        await asyncio.sleep(0.2)
        stop_tone()
        """

        # --- BLUE TEST (commented out for now) ---
        """
        red_led.value(0)
        green_led.value(0)
        blue_led.value(1)     # ON

        val_blue = photo_sensor.read_u16()
        print("Blue LED reading:", val_blue)

        if val_blue > BLUE_THRESHOLD:
            play_tone(LOW_FREQ)
        else:
            play_tone(HIGH_FREQ)

        await asyncio.sleep(0.2)
        stop_tone()
        """

# --- Main ---
async def main():
    asyncio.create_task(color_detector_loop())
    while True:
        await asyncio.sleep(1)

# --- Run Program ---
asyncio.run(main())

