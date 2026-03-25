import psutil
import os
import time


def get_usb_mountpoints():
    """
    Returns a 'set' of mountpoints for currently connected USB drives.
    Using a set allows us to easily compare old vs. new connections.
    """
    usb_mountpoints = set()

    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'removable' in partition.opts:
                usb_mountpoints.add(partition.device)  # e.g., 'E:\'
        else:
            if partition.mountpoint.startswith('/media/') or \
                    partition.mountpoint.startswith('/run/media/') or \
                    partition.mountpoint.startswith('/Volumes/'):
                usb_mountpoints.add(partition.mountpoint)

    print(usb_mountpoints)
    return usb_mountpoints


def monitor_usb_connections():
    print("🕵️‍♂️ USB Tracker Started. Waiting for events... (Press Ctrl+C to stop)")

    # 1. Take a baseline snapshot of what is plugged in right now
    current_drives = get_usb_mountpoints()

    try:
        # 2. Start an infinite loop to monitor changes
        while True:
            # Wait 2 seconds before checking again (prevents CPU overload)
            time.sleep(2)

            # Take a new snapshot
            latest_drives = get_usb_mountpoints()

            # 3. The Pythonic Magic: Set difference!
            added = latest_drives - current_drives
            removed = current_drives - latest_drives

            # 4. Print results if anything changed
            for drive in added:
                print(f"✅ [CONNECTED] New USB device detected: {drive}")

            for drive in removed:
                print(f"❌ [DISCONNECTED] USB device removed: {drive}")

            # Update our baseline for the next loop iteration
            current_drives = latest_drives

    except KeyboardInterrupt:
        # Gracefully handle the user pressing Ctrl+C
        print("\n🛑 Tracking stopped. See you next time!")


if __name__ == "__main__":
    monitor_usb_connections()