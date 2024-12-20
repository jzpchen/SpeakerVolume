import time
from pyssc.scan import scan
from pyssc.Ssc_device import Ssc_device
from pyssc.Ssc_device_setup import Ssc_device_setup

# trying to time the duration of the scan
start_time = time.time()
print("Scanning for SSC devices...")

# Keep scanning until timeout or all speakers found
timeout = 60  # seconds
scan_interval = 10  # seconds
found_setup = None

while time.time() - start_time < timeout:
    try:
        found_setup = scan()
        num_devices = len(found_setup.ssc_devices)
        
        if num_devices == 2:
            print(f"\nFound {num_devices} devices:")
            for device in found_setup.ssc_devices:
                print(f"Device IP: {device.ip}")
                print(f"Device Port: {device.port}")
                print("---")
            print("\nScan completed in %f seconds" % (time.time() - start_time))
            break
        elif num_devices == 1:
            print("\nFound 1 speaker, looking for second speaker...")
            time.sleep(scan_interval)
        else:
            print("\nNo speakers found, continuing to scan...")
            time.sleep(scan_interval)
    except Exception as e:
        print(f"\nError during scan: {str(e)}")
        time.sleep(scan_interval)

if found_setup and len(found_setup.ssc_devices) < 2:
    print(f"\nTimed out after {timeout} seconds")
    print(f"Only found {len(found_setup.ssc_devices)} speaker(s)")
    for device in found_setup.ssc_devices:
        print(f"Device IP: {device.ip}")
        print(f"Device Port: {device.port}")
        print("---")

# Save the setup to a JSON file
# found_setup.to_json('setup.json')
# print("\nDevice setup has been saved to setup.json")
