from bacpypes.core import run, stop
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.object import AnalogInputObject
from bacpypes.service.device import WhoIsIAmServices
import time
import threading

# Create a local BACnet device object
device = LocalDeviceObject(
    objectName="SimulatedTemperatureSensor",
    objectIdentifier=599,  # Unique ID on the network
    maxApduLengthAccepted=1024,
    segmentationSupported="segmentedBoth",
    vendorIdentifier=15
)

# Create a BACnet object - AnalogInput
ai = AnalogInputObject(
    objectIdentifier=('analogInput', 1),
    objectName='RoomTemperature',
    presentValue=22.5,
    units='degreesCelsius'
)
ai._covIncrement = 0.5
ai.eventState = 'normal'
ai.statusFlags = [0, 0, 0, 0]

# Attach object to the device
device.objectList = [ai]


# Get local IP address automatically
import socket
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP



# List all available IPv4 addresses and let the user choose
import netifaces
def get_ipv4_addresses():
    addresses = []
    for iface in netifaces.interfaces():
        iface_details = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in iface_details:
            for link in iface_details[netifaces.AF_INET]:
                ip = link.get('addr')
                if ip and not ip.startswith('127.'):
                    addresses.append(ip)
    return addresses

addresses = get_ipv4_addresses()
if not addresses:
    print("No valid IPv4 addresses found. Exiting.")
    import sys
    sys.exit(1)

print("Available IPv4 addresses:")
for idx, addr in enumerate(addresses):
    print(f"  [{idx}] {addr}")

print("\nAdvice: Choose the IP address that matches your active network interface (e.g., eth0, WiFi, or the one in the same subnet as your BACnet clients/YABE). Avoid addresses starting with 127. or 10.255.255.")
choice = input(f"Select the IP address to use for BACnet (0-{len(addresses)-1}): ")
try:
    local_ip = addresses[int(choice)]
except Exception:
    print("Invalid selection. Exiting.")
    import sys
    sys.exit(1)

print(f"Using local IP: {local_ip}")

# Ping the local IP to check if it is reachable
import subprocess
def ping_ip(ip):
    try:
        output = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output.returncode == 0
    except Exception as e:
        print(f"Ping failed: {e}")
        return False

if ping_ip(local_ip):
    print(f"Ping to {local_ip} successful.")
else:
    print(f"Ping to {local_ip} failed.")

app = BIPSimpleApplication(device, local_ip)

# Add support for Who-Is/I-Am services
WhoIsIAmServices()

# Simulate temperature changes in another thread
def temperature_simulator():
    import random
    while True:
        ai.presentValue += random.uniform(-0.2, 0.2)
        time.sleep(5)


threading.Thread(target=temperature_simulator, daemon=True).start()

print(f"BACnet simulator running on {local_ip}")

# Start BACnet stack
run()
