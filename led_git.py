from gpiozero import LED
import sys

led = LED(17)

if len(sys.argv) < 2:
    print("Usage: python3 led.py on|off")
    sys.exit(1)

command = sys.argv[1].lower()

if command == "on":
    led.on()
    print("LED ON")

elif command == "off":
    led.off()
    print("LED OFF")

else:
    print("Unknown command")
    sys.exit(1)